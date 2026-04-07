import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report, roc_auc_score
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
import joblib

# -----------------------------
# LOAD DATA
# -----------------------------
df = pd.read_csv("processed_features.csv")

# -----------------------------
# CREATE TARGET VARIABLE
# -----------------------------
# Using Risk_Engine_Output as base
df["fraud_label"] = (df["Risk_Engine_Output"] > 0.7).astype(int)

# -----------------------------
# REMOVE DATA LEAKAGE
# -----------------------------
df = df.drop(columns=["fraud_type", "Risk_Engine_Output"])

# -----------------------------
# SPLIT FEATURES / TARGET
# -----------------------------
y = df["fraud_label"]
X = df.drop(columns=["fraud_label"])

# -----------------------------
# ENCODE CATEGORICAL VARIABLES
# -----------------------------
for col in X.select_dtypes(include="object").columns:
    le = LabelEncoder()
    X[col] = le.fit_transform(X[col])

# -----------------------------
# TRAIN TEST SPLIT
# -----------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# -----------------------------
# HANDLE CLASS IMBALANCE
# -----------------------------
fraud_ratio = (y_train == 0).sum() / (y_train == 1).sum()

# -----------------------------
# MODEL 1: RANDOM FOREST
# -----------------------------
rf_model = RandomForestClassifier(
    n_estimators=200,
    max_depth=10,
    class_weight="balanced",
    random_state=42
)

rf_model.fit(X_train, y_train)

# -----------------------------
# MODEL 2: XGBOOST
# -----------------------------
xgb_model = XGBClassifier(
    n_estimators=300,
    max_depth=6,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    scale_pos_weight=fraud_ratio,
    random_state=42,
    eval_metric="logloss"
)

xgb_model.fit(X_train, y_train)

# -----------------------------
# RANDOM FOREST EVALUATION
# -----------------------------
rf_pred = rf_model.predict(X_test)
rf_prob = rf_model.predict_proba(X_test)[:, 1]

rf_acc = accuracy_score(y_test, rf_pred)
rf_auc = roc_auc_score(y_test, rf_prob)

print("\n==============================")
print("RANDOM FOREST RESULTS")
print("==============================")
print(f"Accuracy: {rf_acc:.4f}")
print(f"ROC-AUC: {rf_auc:.4f}")
print(classification_report(y_test, rf_pred))

# -----------------------------
# XGBOOST EVALUATION
# -----------------------------
xgb_pred = xgb_model.predict(X_test)
xgb_prob = xgb_model.predict_proba(X_test)[:, 1]

xgb_acc = accuracy_score(y_test, xgb_pred)
xgb_auc = roc_auc_score(y_test, xgb_prob)

print("\n==============================")
print("XGBOOST RESULTS")
print("==============================")
print(f"Accuracy: {xgb_acc:.4f}")
print(f"ROC-AUC: {xgb_auc:.4f}")
print(classification_report(y_test, xgb_pred))

# -----------------------------
# FINAL COMPARISON
# -----------------------------
print("\n==============================")
print("MODEL COMPARISON")
print("==============================")
print(f"Random Forest Accuracy : {rf_acc:.4f}")
print(f"XGBoost Accuracy      : {xgb_acc:.4f}")
print(f"Random Forest ROC-AUC : {rf_auc:.4f}")
print(f"XGBoost ROC-AUC       : {xgb_auc:.4f}")

# -----------------------------
# SAVE MODELS
# -----------------------------
joblib.dump(rf_model, "rf_model.pkl")
joblib.dump(xgb_model, "xgb_model.pkl")

print("\nBoth models saved successfully")