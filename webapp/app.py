import os
import uuid
import joblib
import pandas as pd
import sys
from datetime import datetime, timezone
from extensions import db

import db_model





from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash


from db_model import User, Dataset, Transaction

from flask_mail import Mail, Message
import random
from datetime import timedelta
from db_model import OTPCode

from flask import Flask
from flask_migrate import Migrate


from flask_migrate import Migrate

from pdf_report import generate_report
import tempfile

from flask import render_template, request, redirect, url_for
from datetime import datetime
import numpy as np

from flask import Flask
from dotenv import load_dotenv
import os
import requests

import os
import requests
from flask import request, session, jsonify
from collections import Counter
from flask import render_template
from datetime import datetime


import os
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

AI_URL = "https://openrouter.ai/api/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "http://localhost:5000",
    "X-Title": "Fraud Detection App"
}


#Name: admin
#Email: admin@email.com
#Password: admin123
#Role: admin



BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)

# ======================
# App Config
# ======================
app = Flask(__name__)
app.secret_key = "dev-secret-key"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///fraud.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


# Email Config
app.config.update(
    MAIL_SERVER="smtp.gmail.com",
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME="sembeunton@gmail.com",
    MAIL_PASSWORD="cvie zokr vadc uime",
    MAIL_DEFAULT_SENDER= "your_email@gmail.com",
)
mail = Mail(app)



db.init_app(app)

#migrate = Migrate.init_app(app, db)  # 🔑 THIS LINE CREATES flask db

from models import *
from src.data_prep import prepare_data
from src.train_models import train_models


def generate_otp():
    return str(random.randint(100000, 999999))


# ======================
# Helpers
# ======================
def interpret_risk(p):
    if p < 0.3:
        return "Low Risk"
    elif p < 0.7:
        return "Medium Risk"
    return "High Risk"


def explain_transaction_ai(tx: Transaction):
    reasons = []

    if tx.fraud_probability >= 0.9:
        reasons.append("Extremely high fraud probability detected")

    if tx.amount and tx.amount > 10000:
        reasons.append("Transaction amount is unusually high")

    if tx.timestamp:
        reasons.append("Transaction timing may be suspicious")

    if tx.location:
        reasons.append(f"Transaction originated from {tx.location}")

    if not reasons:
        reasons.append("No strong fraud indicators found")

    return reasons


from functools import wraps

def admin_required(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):

        if "user_id" not in session:
            return redirect(url_for("login"))

        if session.get("role") != "admin":
            flash("Admin access required", "danger")
            return redirect(url_for("dashboard"))

        return f(*args, **kwargs)

    return decorated_function






# ======================
# Paths
# ======================
DATA_DIR = os.path.join(BASE_DIR, "data", "uploads")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
MODEL_DIR = os.path.join(BASE_DIR, "models")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)

# ======================
# Auth
# ======================
@app.route("/")
def home():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("home.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"]

        # 🔎 Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("An account with this email already exists. Please log in.", "warning")
            return redirect(url_for("login"))

        user = User(
            name=request.form["name"],
            email=email,
            password=generate_password_hash(request.form["password"])
        )

        db.session.add(user)
        db.session.commit()

        flash("Account created successfully. Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")



@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        user = User.query.filter_by(
            email=request.form["email"]
        ).first()

        if not user or not check_password_hash(
            user.password,
            request.form["password"]
        ):
            flash("Invalid credentials", "danger")
            return redirect(url_for("login"))

        # ==========================
        # Generate OTP
        # ==========================

        otp_code = generate_otp()

        otp = OTPCode(
            user_id=user.id,
            code=otp_code,
            expires_at=datetime.utcnow() + timedelta(minutes=5)
        )

        db.session.add(otp)
        db.session.commit()

        # ==========================
        # Send OTP Email
        # ==========================

        msg = Message(
            "Your OTP Code",
            sender=app.config["MAIL_USERNAME"],
            recipients=[user.email]
        )

        msg.body = f"""
Your OTP code is: {otp_code}

This code expires in 5 minutes.
"""

        mail.send(msg)

        # ==========================
        # Store user info in session
        # ==========================

        session["otp_user"] = user.id

        # NEW: store role
        session["otp_role"] = user.role

        flash("OTP sent to your email", "info")

        return redirect(url_for("verify_otp"))

    return render_template("login.html")



@app.route("/verify-otp", methods=["GET", "POST"])
def verify_otp():

    if "otp_user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        code = request.form["otp"]

        otp = OTPCode.query.filter_by(
            user_id=session["otp_user"],
            code=code
        ).first()

        if not otp or otp.expires_at < datetime.utcnow():

            flash("Invalid or expired OTP", "danger")
            return redirect(url_for("verify_otp"))

        # ==========================
        # Login success
        # ==========================

        session["user_id"] = session["otp_user"]
        session["role"] = session["otp_role"]

        # remove temp session
        session.pop("otp_user", None)
        session.pop("otp_role", None)

        # redirect based on role
        if session["role"] == "admin":
            return redirect(url_for("admin_dashboard"))
        else:
            return redirect(url_for("index"))

    return render_template("verify_otp.html")

@app.route("/admin_dashboard")
def admin_dashboard():

    # check if user logged in
    if "user_id" not in session:
        flash("Please login first", "warning")
        return redirect(url_for("login"))

    # get current user
    user = User.query.get(session["user_id"])

    # check if admin
    if user.role != "admin":
        flash("Access denied. Admin only.", "danger")
        return redirect(url_for("dashboard"))

    # get all users
    users = User.query.all()

    # get all transactions
    transactions = Transaction.query.order_by(Transaction.created_at.desc()).all()

    return render_template(
        "admin_dashboard.html",
        users=users,
        transactions=transactions
    )





@app.route("/admin/user/<int:user_id>")
def admin_user_details(user_id):

    user = User.query.get_or_404(user_id)

    # -----------------------------------
    # Get datasets of the user
    # -----------------------------------
    datasets = Dataset.query.filter_by(user_id=user_id).all()
    dataset_ids = [d.id for d in datasets]

    # -----------------------------------
    # Get transactions from those datasets
    # -----------------------------------
    transactions = Transaction.query.filter(
        Transaction.dataset_id.in_(dataset_ids)
    ).all()

    # -----------------------------------
    # Fraud vs Safe
    # -----------------------------------

    fraud_count = 0
    safe_count = 0

    for t in transactions:
        if t.risk == "High Risk":
            fraud_count += 1
        else:
            safe_count += 1

    # -----------------------------------
    # Fraud Risk Distribution
    # -----------------------------------

    risk_counter = Counter([t.risk for t in transactions])

    high_risk = risk_counter.get("High Risk", 0)
    medium_risk = risk_counter.get("Medium Risk", 0)
    low_risk = risk_counter.get("Low Risk", 0)

    # -----------------------------------
    # Fraud by Location
    # -----------------------------------

    location_counter = Counter(
        [t.location for t in transactions if t.location]
    )

    location_labels = list(location_counter.keys())
    location_values = list(location_counter.values())

    # -----------------------------------
    # Fraud Trend Over Time
    # -----------------------------------

    date_counter = Counter()

    for t in transactions:
        if t.created_at:
            date = t.created_at.strftime("%Y-%m-%d")
            date_counter[date] += 1

    trend_labels = list(date_counter.keys())
    trend_values = list(date_counter.values())

    # -----------------------------------
    # Send everything to template
    # -----------------------------------

    return render_template(
        "admin_user_details.html",
        user=user,
        datasets=datasets,
        transactions=transactions,

        fraud_count=fraud_count,
        safe_count=safe_count,

        high_risk=high_risk,
        medium_risk=medium_risk,
        low_risk=low_risk,

        location_labels=location_labels,
        location_values=location_values,

        trend_labels=trend_labels,
        trend_values=trend_values
    )



@app.route("/admin/users")
@admin_required
def admin_users():

    users = User.query.all()

    return render_template(
        "admin/users.html",
        users=users
    )





@app.route("/account")
def account():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user = User.query.get(session["user_id"])

    datasets = Dataset.query.filter_by(user_id=user.id).all()

    total_datasets = len(datasets)

    total_transactions = (
        db.session.query(Transaction)
        .join(Dataset)
        .filter(Dataset.user_id == user.id)
        .count()
    )

    fraud_count = (
    db.session.query(Transaction)
    .join(Dataset)
    .filter(
        Dataset.user_id == user.id,
        Transaction.risk == "High Risk"
    )
    .count()        
    )


    return render_template(
        "account.html",
        user=user,
        datasets=datasets,
        total_datasets=total_datasets,
        total_transactions=total_transactions,
        fraud_count=fraud_count
    )



@app.route("/delete_dataset/<int:dataset_id>", methods=["POST"])
def delete_dataset(dataset_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    dataset = Dataset.query.get_or_404(dataset_id)

    # Security: make sure dataset belongs to user
    if dataset.user_id != session["user_id"]:
        return "Unauthorized", 403

    # delete all transactions first
    Transaction.query.filter_by(dataset_id=dataset_id).delete()

    # delete dataset
    db.session.delete(dataset)
    db.session.commit()

    flash("Dataset deleted successfully", "success")

    return redirect(url_for("account"))

@app.route("/delete_transaction/<int:transaction_id>", methods=["POST"])
def delete_transaction(transaction_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    transaction = Transaction.query.get_or_404(transaction_id)

    dataset = Dataset.query.get(transaction.dataset_id)

    if dataset.user_id != session["user_id"]:
        return "Unauthorized", 403

    db.session.delete(transaction)
    db.session.commit()

    flash("Transaction deleted", "success")

    return redirect(url_for("account"))






@app.route("/send-report/<int:dataset_id>")
def send_report(dataset_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    user = User.query.get(session["user_id"])
    dataset = Dataset.query.get_or_404(dataset_id)

    # ===============================
    # GET ALL TRANSACTIONS FOR DATASET
    # ===============================
    transactions = Transaction.query.filter_by(dataset_id=dataset.id).all()

    total = len(transactions)
    high_count = sum(t.risk == "High Risk" for t in transactions)
    medium_count = sum(t.risk == "Medium Risk" for t in transactions)
    low_count = sum(t.risk == "Low Risk" for t in transactions)

    stats = {
        "total": total,
        "fraud": high_count,
        "medium": medium_count,
        "low": low_count
    }

    # ===============================
    # GENERATE PDF
    # ===============================
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        pdf_path = tmp.name

    generate_report(pdf_path, user, dataset, stats)

    # ===============================
    # SEND EMAIL WITH ATTACHMENT
    # ===============================
    msg = Message(
        subject="Your Fraud Detection Audit Report",
        recipients=[user.email]
    )

    msg.body = (
        f"Hello {user.name},\n\n"
        "Please find attached your detailed fraud detection audit report.\n\n"
        "Best regards,\nFraud Detection System"
    )

    with open(pdf_path, "rb") as f:
        msg.attach(
            filename="fraud_audit_report.pdf",
            content_type="application/pdf",
            data=f.read()
        )

    mail.send(msg)

    flash("📧 Detailed report sent to your email!", "success")
    return redirect(url_for("account"))




@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ======================
# Dashboard
# ======================
@app.route("/dashboard")
def index():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("index.html")


# ======================
# Train model from CSV
# ======================
@app.route("/train", methods=["POST"])
def train_from_csv():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if "file" not in request.files:
        flash("No file uploaded", "danger")
        return redirect(url_for("dashboard"))

    file = request.files["file"]
    target_column = request.form.get("target")

    if file.filename == "":
        flash("No file selected", "danger")
        return redirect(url_for("dashboard"))

    # ----------------------
    # Save raw uploaded CSV
    # ----------------------
    raw_path = os.path.join(DATA_DIR, f"{uuid.uuid4()}.csv")
    file.save(raw_path)

    df = pd.read_csv(raw_path)

    # ----------------------
    # Create dataset record
    # ----------------------
    dataset = Dataset(
        user_id=session["user_id"],
        filename=file.filename,
        num_rows=len(df)
    )
    db.session.add(dataset)
    db.session.commit()

    dataset_id = dataset.id  # ✅ SINGLE SOURCE OF TRUTH

    try:
        # ----------------------
        # Prepare data
        # ----------------------
        prepare_data(
            raw_path=raw_path,
            save_path=PROCESSED_DIR,
            target_column=target_column
        )

        # ----------------------
        # Create USER-SPECIFIC model directory
        # ----------------------
        user_model_dir = os.path.join(
            MODEL_DIR,
            f"user_{session['user_id']}",
            f"dataset_{dataset_id}"
        )
        os.makedirs(user_model_dir, exist_ok=True)

        # ----------------------
        # Train model (saved per user)
        # ----------------------
        metrics = train_models(
            processed_data_path=PROCESSED_DIR,
            model_dir=user_model_dir
        )

        # ----------------------
        # Load trained artifacts
        # ----------------------
        model = joblib.load(os.path.join(user_model_dir, "best_model.pkl"))
        scaler = joblib.load(os.path.join(user_model_dir, "scaler.pkl"))
        features = joblib.load(os.path.join(user_model_dir, "features.pkl"))

        # ----------------------
        # Align features
        # ----------------------
        for col in features:
            if col not in df.columns:
                df[col] = 0

        X = scaler.transform(df[features])

        df["fraud_probability"] = model.predict_proba(X)[:, 1]
        df["risk"] = df["fraud_probability"].apply(interpret_risk)

        # ----------------------
        # Save transactions
        # ----------------------
        for _, row in df.iterrows():
            tx = Transaction(
                dataset_id=dataset_id,
                fraud_probability=float(row["fraud_probability"]),
                risk=row["risk"],
                created_at=datetime.now(timezone.utc)
            )
            db.session.add(tx)

        # ----------------------
        # Save model path in DB
        # ----------------------
        dataset.model_path = user_model_dir
        db.session.commit()

        flash("✅ Model trained & predictions completed!", "success")
        return redirect(url_for("results", dataset_id=dataset_id))

    except Exception as e:
        db.session.rollback()
        flash(f"Training failed: {e}", "danger")
        return redirect(url_for("index"))



# ======================
# Upload & Predict
# ======================
@app.route("/predict", methods=["POST"])
def predict():
    file = request.files["file"]
    df = pd.read_csv(file)

    dataset = Dataset(
        filename=file.filename,
        user_id=session["user_id"]
    )
    db.session.add(dataset)
    db.session.commit()

    model = joblib.load("models/best_model.pkl")
    scaler = joblib.load("models/scaler.pkl")
    features = joblib.load("models/features.pkl")

    for col in features:
        if col not in df.columns:
            df[col] = 0

    X = scaler.transform(df[features])
    df["fraud_probability"] = model.predict_proba(X)[:, 1]
    df["risk"] = df["fraud_probability"].apply(interpret_risk)

    for _, row in df.iterrows():
        tx = Transaction(
            dataset_id=dataset.id,
            fraud_probability=row["fraud_probability"],
            risk=row["risk"],
            amount=row.get("Amount"),
            location=row.get("location"),
            timestamp=row.get("timestamp")
        )
        db.session.add(tx)

    db.session.commit()

    high_count = Transaction.query.filter_by(
        dataset_id=dataset.id,
        risk="High Risk"
    ).count()

    return redirect(url_for("results", dataset_id=dataset.id))

# ======================
# Results
# ======================
@app.route("/results/<int:dataset_id>")
def results(dataset_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    transactions = Transaction.query.filter_by(
        dataset_id=dataset_id
    ).order_by(Transaction.fraud_probability.desc()).all()

    total = len(transactions)
    high_count = sum(t.risk == "High Risk" for t in transactions)
    medium_count = sum(t.risk == "Medium Risk" for t in transactions)
    low_count = sum(t.risk == "Low Risk" for t in transactions)

    avg_proba = round(
        sum(t.fraud_probability for t in transactions) / total, 3
    ) if total else 0

    return render_template(
        "results.html",
        total=total,
        flagged=high_count,
        avg_proba=avg_proba,
        rows=transactions[:20],
        low_count=low_count,
        medium_count=medium_count,
        high_count=high_count,
        dataset_id=dataset_id
    )


# ======================
# Transaction Details
# ======================
@app.route("/transaction/<int:tx_id>")
def transaction_details(tx_id):
    tx = Transaction.query.get_or_404(tx_id)
    return render_template("transaction_details.html", transaction=tx)


@app.route("/new_transaction", methods=["GET", "POST"])
def new_transaction():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        user_id = session["user_id"]

        amount = float(request.form["amount"])
        location = request.form["location"]
        device = request.form["device"]

        user_models_dir = os.path.join(MODEL_DIR, f"user_{user_id}")

        predictions = []

        if os.path.exists(user_models_dir):

            for dataset_name in os.listdir(user_models_dir):

                dataset_dir = os.path.join(user_models_dir, dataset_name)

                model_path = os.path.join(dataset_dir, "best_model.pkl")
                scaler_path = os.path.join(dataset_dir, "scaler.pkl")
                features_path = os.path.join(dataset_dir, "features.pkl")

                if not all(os.path.exists(p) for p in [model_path, scaler_path, features_path]):
                    continue

                # Load model components
                model = joblib.load(model_path)
                scaler = joblib.load(scaler_path)
                features = joblib.load(features_path)

                print("MODEL FEATURES:", features)

                # Create empty dataframe with EXACT features considered during training
                full_df = pd.DataFrame(0, index=[0], columns=features)

                # Fill numeric feature
                if "Amount" in full_df.columns:
                    full_df["Amount"] = amount


                # Handle LOCATION (One-hot encoding safe handling)
                for col in features:
                    if col.lower() == f"location_{location.lower()}":
                        full_df[col] = 1

                # Handle DEVICE (One-hot encoding safe handling)
                for col in features:
                    if col.lower() == f"device_{device.lower()}":
                        full_df[col] = 1

                print("INPUT VECTOR SENT TO MODEL:")
                print(full_df)

                # Scale
                X = scaler.transform(full_df)

                # Predict
                fraud_prob = model.predict_proba(X)[0][1]

                print("FRAUD PROBABILITY:", fraud_prob)

                predictions.append(fraud_prob)

        # Average prediction across datasets
        avg_fraud_prob = sum(predictions) / len(predictions) if predictions else 0

        # Risk classification
        if avg_fraud_prob < 0.3:
            risk = "Low Risk"
        elif avg_fraud_prob < 0.7:
            risk = "Medium Risk"
        else:
            risk = "High Risk"

        # Save temporarily
        session["pending_tx"] = {
            "amount": amount,
            "location": location,
            "fraud_probability": avg_fraud_prob,
            "risk": risk
        }

        return render_template(
            "new_transaction.html",
            show_popup=True,
            fraud_probability=round(avg_fraud_prob * 100, 2),
            risk=risk
        )

    return render_template("new_transaction.html")




@app.route("/save_transaction_decision", methods=["POST"])
def save_transaction_decision():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if "pending_tx" not in session:
        return redirect(url_for("new_transaction"))

    user_id = session["user_id"]

    decision = request.form["decision"]

    pending = session["pending_tx"]

    # create dataset entry
    dataset = Dataset(
        user_id=user_id,
        filename="Manual Transaction",
        num_rows=1
    )

    db.session.add(dataset)
    db.session.commit()

    # save transaction
    tx = Transaction(
        dataset_id=dataset.id,
        amount=pending["amount"],
        location=pending["location"],
        fraud_probability=pending["fraud_probability"],
        risk=pending["risk"],
        decision=decision
    )

    db.session.add(tx)
    db.session.commit()

    # clear pending
    session.pop("pending_tx", None)

    return redirect(url_for("index"))



# ======================
# High Risk Page
# ======================
@app.route("/high-risk/<int:dataset_id>")
def high_risk(dataset_id):
    rows = Transaction.query.filter_by(
        dataset_id=dataset_id,
        risk="High Risk"
    ).all()

    return render_template("high_risks.html", rows=rows)







    










@app.route("/ai-helper", methods=["POST"])
def ai_helper():

    data = request.get_json()
    question = data.get("question", "").strip()

    if not question:
        return jsonify({"answer": "Please ask a question."})

    # 🔐 Ensure user logged in
    if "user_id" not in session:
        return jsonify({"answer": "Please login to use the AI assistant."})

    user_id = session["user_id"]

    # 📊 Fetch user transactions
    transactions = (
        db.session.query(Transaction)
        .join(Dataset)
        .filter(Dataset.user_id == user_id)
        .all()
    )

    if not transactions:
        return jsonify({"answer": "No transaction data available yet."})

    # 📈 Compute statistics safely
    total_transactions = len(transactions)
    high_count = sum(1 for t in transactions if t.risk == "High Risk")
    medium_count = sum(1 for t in transactions if t.risk == "Medium Risk")
    low_count = sum(1 for t in transactions if t.risk == "Low Risk")

    valid_probs = [
        t.fraud_probability for t in transactions
        if t.fraud_probability is not None
    ]

    avg_probability = round(
        sum(valid_probs) / len(valid_probs), 3
    ) if valid_probs else 0

    # 🔎 Latest transaction
    latest_transaction = (
        db.session.query(Transaction)
        .join(Dataset)
        .filter(Dataset.user_id == user_id)
        .order_by(Transaction.id.desc())
        .first()
    )

    latest_risk = latest_transaction.risk if latest_transaction else "N/A"
    latest_proba = latest_transaction.fraud_probability if latest_transaction else "N/A"

    # 🧠 Build AI Context Prompt
    prompt = f"""
SYSTEM FRAUD ANALYTICS SUMMARY

Transaction Statistics:
- Total Transactions: {total_transactions}
- High Risk: {high_count}
- Medium Risk: {medium_count}
- Low Risk: {low_count}
- Average Fraud Probability: {avg_probability}


User Query:
{question}

Provide:
1. Overview
2. Risk Insight
3. Recommended Actions (if applicable)
"""


    # 🔥 New HuggingFace Chat API Payload
    payload = {
    "model": "meta-llama/llama-3-8b-instruct",
    "messages": [
        {
            "role": "system",
            "content": "You are a professional AI Fraud Detection Assistant."
        },
        {
            "role": "user",
            "content": prompt
        }
    ],
    "max_tokens": 300,
    "temperature": 0.6
}


    try:
        response = requests.post(
            AI_URL,
            headers=headers,
            json=payload,
            timeout=60
        )

        if response.status_code != 200:
            return jsonify({
                "answer": f"AI service temporarily unavailable (HF {response.status_code})."
            })

        result = response.json()

        if "choices" in result:
            answer = result["choices"][0]["message"]["content"]
        else:
            answer = "AI response format unexpected."


        return jsonify({"answer": answer})

    except Exception as e:
        return jsonify({
            "answer": f"AI connection error: {str(e)}"
        })



if __name__ == "__main__":
    with app.app_context():
        db.create_all()   # ✅ CREATE ALL TABLES
    app.run(debug=True)


# =========================
# Run App
# =========================
if __name__ == "__main__":
    app.run(debug=True)

migrate = Migrate(app, db)