import pandas as pd
import numpy as np
import os
import joblib

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier

from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score
)

def load_processed_data(path):
    """Load processed training/testing datasets."""
    X_train = pd.read_csv(os.path.join(path, "X_train.csv"))
    X_test = pd.read_csv(os.path.join(path, "X_test.csv"))
    y_train = pd.read_csv(os.path.join(path, "y_train.csv")).values.ravel()
    y_test = pd.read_csv(os.path.join(path, "y_test.csv")).values.ravel()

    return X_train, X_test, y_train, y_test

def evaluate_model(model, X_test, y_test):
    """Calculate evaluation metrics."""
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    return {
        "accuracy": accuracy_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred),
        "recall": recall_score(y_test, y_pred),
        "f1_score": f1_score(y_test, y_pred),
        "roc_auc": roc_auc_score(y_test, y_prob)
    }

def train_models(X_train, y_train):
    """Train Logistic Regression, Random Forest, XGBoost."""

    print("📌 Training Logistic Regression...")
    lr = LogisticRegression(max_iter=2000)
    lr.fit(X_train, y_train)

    print("🌳 Training Random Forest...")
    rf = RandomForestClassifier(
        n_estimators=200,
        max_depth=10,
        random_state=42
    )
    rf.fit(X_train, y_train)

    print("⚡ Training XGBoost...")
    xgb = XGBClassifier(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        eval_metric="logloss",
        random_state=42
    )
    xgb.fit(X_train, y_train)

    return {
        "LogisticRegression": lr,
        "RandomForest": rf,
        "XGBoost": xgb
    }

def save_best_model(model, save_path="models"):
    """Save the best model using joblib."""
    os.makedirs(save_path, exist_ok=True)
    joblib.dump(model, os.path.join(save_path, "best_model.pkl"))
    print(f"💾 Best model saved to: {save_path}/best_model.pkl")

def main():
    print("📥 Loading processed data...")
    X_train, X_test, y_train, y_test = load_processed_data("data/processed")

    print("🏋️ Training models...")
    models = train_models(X_train, y_train)

    print("\n📊 Evaluating models...")
    results = {}

    for name, model in models.items():
        results[name] = evaluate_model(model, X_test, y_test)
        print(f"\n==== {name} ====")
        for metric, value in results[name].items():
            print(f"{metric}: {value:.4f}")

    print("\n🏆 Selecting best model based on ROC-AUC...")
    best_model_name = max(results, key=lambda x: results[x]["roc_auc"])
    best_model = models[best_model_name]

    print(f"➡ Best Model: {best_model_name}")
    print(f"➡ ROC-AUC: {results[best_model_name]['roc_auc']:.4f}")

    save_best_model(best_model)

if __name__ == "__main__":
    main()
