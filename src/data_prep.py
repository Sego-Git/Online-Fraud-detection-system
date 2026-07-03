import pandas as pd
import numpy as np
import os
import joblib

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from imblearn.over_sampling import SMOTE

# =========================
# Utility functions
# =========================

def load_data(path):
    """Load dataset from CSV"""
    if not os.path.exists(path):
        raise FileNotFoundError(f"❌ File not found: {path}")
    return pd.read_csv(path)


def clean_data(df):
    """Basic cleaning: drop duplicates, keep numeric, fill missing"""
    df = df.drop_duplicates()
    df = df.select_dtypes(include=[np.number])
    df = df.fillna(df.median())
    return df


def detect_target_column(df):
    """
    Automatically detect fraud target column
    Must be binary (0/1) and match common target names
    """
    possible_names = ["isfraud", "fraud", "class", "label", "target"]

    # Name-based detection
    for col in df.columns:
        col_lower = col.lower()
        if any(name in col_lower for name in possible_names):
            unique_vals = df[col].unique()
            if set(unique_vals).issubset({0, 1}):
                return col

    # Fallback: any binary column
    for col in df.columns:
        unique_vals = df[col].unique()
        if set(unique_vals).issubset({0, 1}):
            return col

    raise ValueError("❌ No valid target column found (binary 0/1)")


def prepare_data(raw_path, save_path, target_column=None):
    """
    Prepares dataset for training.
    :param raw_path: path to raw CSV
    :param save_path: directory to save processed files
    :param target_column: optional, user-specified target column
    """
    print("📥 Loading data...")
    df = load_data(raw_path)

    print("🧹 Cleaning data...")
    df = clean_data(df)

    # Determine target column
    if target_column:
        if target_column not in df.columns:
            raise ValueError(f"❌ Target column '{target_column}' not found in dataset.")
        if not set(df[target_column].unique()).issubset({0, 1}):
            raise ValueError(f"❌ Target column '{target_column}' must be binary (0/1).")
        print(f"✅ Using user-specified target column: {target_column}")
    else:
        print("🎯 Detecting target column...")
        target_column = detect_target_column(df)
        print(f"✅ Target column auto-detected: {target_column}")

    # Split features & target
    print("✂ Splitting features & target...")
    X = df.drop(columns=[target_column])
    y = df[target_column]

    os.makedirs(save_path, exist_ok=True)

    # Save feature names
    joblib.dump(X.columns.tolist(), os.path.join(save_path, "features.pkl"))

    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Scale features
    print("📏 Scaling features...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    X_train_scaled = pd.DataFrame(X_train_scaled, columns=X.columns)
    X_test_scaled = pd.DataFrame(X_test_scaled, columns=X.columns)

    # Handle imbalance
    print("⚖ Handling imbalance with SMOTE...")
    smote = SMOTE(random_state=42)
    X_train_resampled, y_train_resampled = smote.fit_resample(X_train_scaled, y_train)

    # Save processed data
    print("💾 Saving processed data...")
    X_train_resampled.to_csv(os.path.join(save_path, "X_train.csv"), index=False)
    X_test_scaled.to_csv(os.path.join(save_path, "X_test.csv"), index=False)
    y_train_resampled.to_csv(os.path.join(save_path, "y_train.csv"), index=False)
    y_test.to_csv(os.path.join(save_path, "y_test.csv"), index=False)

    joblib.dump(scaler, os.path.join(save_path, "scaler.pkl"))

    print("✅ Data preparation completed successfully!")

    return target_column


# =========================
# CLI test (optional)
# =========================
if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    RAW_DATA_PATH = os.path.join(
        BASE_DIR, "..", "data", "raw", "PS_20174392719_1491204439457_log.csv"
    )

    SAVE_PATH = os.path.join(BASE_DIR, "..", "data", "processed")

    # Pass target_column=None to auto-detect
    prepare_data(RAW_DATA_PATH, SAVE_PATH, target_column=None)
