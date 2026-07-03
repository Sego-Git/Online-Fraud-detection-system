from extensions import db
from datetime import datetime, timezone


# =========================
# USER MODEL
# =========================
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    role = db.Column(db.String(20), default="analyst")  # analyst | admin

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    datasets = db.relationship("Dataset", backref="user", lazy=True)
    otp_codes = db.relationship("OTPCode", backref="user", lazy=True)
    trusted_devices = db.relationship("TrustedDevice", backref="user", lazy=True)
    trained_models = db.relationship("TrainedModel", backref="user", lazy=True)


# =========================
# DATASET HISTORY
# =========================
class Dataset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=True)

    num_rows = db.Column(db.Integer)
    num_columns = db.Column(db.Integer)

    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )
    model_path = db.Column(db.String(255))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    # Relationships
    transactions = db.relationship("Transaction", backref="dataset", lazy=True)
    trained_models = db.relationship("TrainedModel", backref="dataset", lazy=True)


# =========================
# FRAUD TRANSACTIONS
# =========================
class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    dataset_id = db.Column(
        db.Integer,
        db.ForeignKey("dataset.id"),
        nullable=False
    )

    amount = db.Column(db.Float)
    location = db.Column(db.String(100))

    fraud_probability = db.Column(db.Float)
    risk = db.Column(db.String(20))

    # ✅ ADD THIS
    decision = db.Column(db.String(20))  # Accept / Block / Flag

    # Optional but recommended
    status = db.Column(db.String(20), default="Pending")

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )



# =========================
# TRAINED ML MODELS
# =========================
class TrainedModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    dataset_id = db.Column(db.Integer, db.ForeignKey("dataset.id"), nullable=False)

    model_name = db.Column(db.String(100))  # RandomForest, SVM, etc.
    accuracy = db.Column(db.Float)

    model_path = db.Column(db.String(500))  # saved .pkl file

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# =========================
# OTP AUTHENTICATION
# =========================
class OTPCode(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    code = db.Column(db.String(6), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    verified = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def is_expired(self):
        return datetime.utcnow() > self.expires_at


# =========================
# TRUSTED DEVICES (SKIP OTP)
# =========================
class TrustedDevice(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    device_hash = db.Column(db.String(256), nullable=False)
    last_used = db.Column(db.DateTime, default=datetime.utcnow)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
