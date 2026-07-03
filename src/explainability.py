import shap
import numpy as np
import pandas as pd

def get_shap_explainer(model, X_background):
    """
    Automatically choose the correct SHAP explainer
    based on model type.
    """
    model_name = model.__class__.__name__.lower()

    if "xgb" in model_name or "forest" in model_name or "tree" in model_name:
        return shap.TreeExplainer(model)
    else:
        # Logistic Regression, SVM, etc.
        return shap.Explainer(model, X_background)

def explain_single_transaction(model, X_train, X_instance, feature_names, top_k=5):
    """
    Explain why a single transaction was flagged.
    Returns a list of feature contributions.
    """
    explainer = get_shap_explainer(model, X_train)
    shap_values = explainer(X_instance)

    values = shap_values.values[0]
    features = X_instance[0]

    explanations = []

    for i in np.argsort(np.abs(values))[::-1][:top_k]:
        explanations.append({
            "feature": feature_names[i],
            "impact": float(values[i]),
            "value": float(features[i])
        })

    return explanations
