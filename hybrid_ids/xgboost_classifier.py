import os

from xgboost import XGBClassifier

from hybrid_ids.config import MODEL_FOLDER, RANDOM_STATE


def create_xgboost_model(number_of_classes):
    """Create and return an XGBoost multi-class classifier."""
    print("\n")
    print("=" * 70)
    print("STAGE 2: XGBOOST ATTACK CLASSIFICATION")
    print("=" * 70)
    print("\nNumber of classes:", number_of_classes)

    return XGBClassifier(
        n_estimators=300,
        max_depth=8,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        objective="multi:softprob",
        num_class=number_of_classes,
        eval_metric="mlogloss",
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )


def print_class_mapping(label_encoder):
    """Print the integer-to-label class mapping."""
    print("\nClasses:")
    for index, label in enumerate(label_encoder.classes_):
        print(index, "->", label)


def train_xgboost(xgb_model, X_train_np, y_train_np, X_validation_np, y_validation_np):
    """Train the XGBoost classifier."""
    print("\nTraining XGBoost...")
    xgb_model.fit(
        X_train_np,
        y_train_np,
        eval_set=[(X_validation_np, y_validation_np)],
        verbose=True,
    )


def save_xgboost_model(xgb_model):
    """Persist the trained XGBoost model to disk."""
    xgb_model.save_model(os.path.join(MODEL_FOLDER, "xgboost_model.json"))
    print("\nXGBoost model saved.")
