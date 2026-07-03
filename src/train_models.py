# src/train_models.py
import os
import joblib
import pandas as pd

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score

def load_processed_data(path):
    X_train = pd.read_csv(os.path.join(path, "X_train.csv"))
    X_test = pd.read_csv(os.path.join(path, "X_test.csv"))
    y_train = pd.read_csv(os.path.join(path, "y_train.csv")).values.ravel()
    y_test = pd.read_csv(os.path.join(path, "y_test.csv")).values.ravel()
    return X_train, X_test, y_train, y_test

def evaluate_model(model, X_test, y_test):
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]
    return {
        "accuracy": round(accuracy_score(y_test, y_pred), 3),
        "precision": round(precision_score(y_test, y_pred), 3),
        "recall": round(recall_score(y_test, y_pred), 3),
        "f1_score": round(f1_score(y_test, y_pred), 3),
        "roc_auc": round(roc_auc_score(y_test, y_prob), 3)
    }

def train_models(processed_data_path, model_dir):
    os.makedirs(model_dir, exist_ok=True)

    # Load data
    X_train, X_test, y_train, y_test = load_processed_data(processed_data_path)

    # Load scaler & features (already saved by data_prep.py)
    scaler = joblib.load(os.path.join(processed_data_path, "scaler.pkl"))
    features = joblib.load(os.path.join(processed_data_path, "features.pkl"))

    X_train_scaled = scaler.transform(X_train[features])
    X_test_scaled = scaler.transform(X_test[features])

    # Train models
    print("📌 Training Logistic Regression...")
    lr = LogisticRegression(max_iter=2000)
    lr.fit(X_train_scaled, y_train)

    print("🌳 Training Random Forest...")
    rf = RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42)
    rf.fit(X_train_scaled, y_train)

    print("⚡ Training XGBoost...")
    xgb = XGBClassifier(
        n_estimators=300, max_depth=6, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8, eval_metric="logloss",
        random_state=42
    )
    xgb.fit(X_train_scaled, y_train)

    # Evaluate
    models = {"LogisticRegression": lr, "RandomForest": rf, "XGBoost": xgb}
    metrics = {}
    best_model = None
    best_score = 0

    for name, model in models.items():
        score = evaluate_model(model, X_test_scaled, y_test)
        metrics[name] = score
        if score["roc_auc"] > best_score:
            best_score = score["roc_auc"]
            best_model = model

    # Save best model
    joblib.dump(best_model, os.path.join(model_dir, "best_model.pkl"))
    joblib.dump(scaler, os.path.join(model_dir, "scaler.pkl"))
    joblib.dump(features, os.path.join(model_dir, "features.pkl"))
    print(f"💾 Best model saved to: {model_dir}/best_model.pkl")

    return metrics

# =========================
# CLI test
# =========================
if __name__ == "__main__":
    processed_data_path = os.path.join("data", "processed")
    model_dir = os.path.join("models")
    metrics = train_models(processed_data_path, model_dir)
    print("✅ Training completed. Metrics:")
    print(metrics)
