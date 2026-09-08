import os

from xgboost import XGBClassifier

import hybrid_ids.config as config
from hybrid_ids.device_config import get_xgboost_params


def create_xgboost_model(number_of_classes):
    """Create and return an XGBoost multi-class classifier."""
    print("\n")
    print("=" * 70)
    print("STAGE 2: XGBOOST ATTACK CLASSIFICATION")
    print("=" * 70)
    print("\nNumber of classes:", number_of_classes)

    device_params = get_xgboost_params()

    return XGBClassifier(
        n_estimators=500,
        max_depth=6,
        learning_rate=0.03,
        subsample=0.9,
        colsample_bytree=0.8,
        objective="multi:softprob",
        num_class=number_of_classes,
        eval_metric="mlogloss",
        random_state=config.RANDOM_STATE,
        early_stopping_rounds=25,
        **device_params,
    )


def print_class_mapping(label_encoder):
    """Print the integer-to-label class mapping."""
    print("\nClasses:")
    for index, label in enumerate(label_encoder.classes_):
        print(index, "->", label)


def train_xgboost(xgb_model, X_train_np, y_train_np, X_validation_np, y_validation_np):
    """Train the XGBoost classifier with early stopping."""
    print("\nTraining XGBoost...")
    xgb_model.fit(
        X_train_np,
        y_train_np,
        eval_set=[(X_validation_np, y_validation_np)],
        verbose=50,
    )
    best_iteration = xgb_model.best_iteration
    if best_iteration is not None:
        print(f"\nBest iteration: {best_iteration} (early stopping applied)")


def save_xgboost_model(xgb_model):
    """Persist the trained XGBoost model to disk."""
    xgb_model.save_model(os.path.join(config.MODEL_FOLDER, "xgboost_model.json"))
    print("\nXGBoost model saved.")
