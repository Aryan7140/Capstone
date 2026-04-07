import pandas as pd
import joblib
from sklearn.metrics import confusion_matrix, classification_report

# Load model
model = joblib.load("xgb_model.pkl")

# Load dataset
df = pd.read_excel("indian_cities_rupees_dataset.xlsx")

# Create label (if not present)
df["fraud_label"] = (df["Risk_Engine_Output"] > 0.7).astype(int)

# Feature selection
X = df[[
    "amount",
    "Amount_conversion",
    "transaction_type",
    "merchant_category",
    "location",
    "device_used",
    "time_since_last_transaction",
    "spending_deviation_score",
    "velocity_score",
    "geo_anomaly_score",
    "payment_channel",
    "User_Behavioral_History",
    "Beneficiary_Intelligence",
    "Transaction_Velocity",
    "Behavioral_Deviation",
    "amount_inr"
]]

# Encode categorical
X = X.apply(lambda col: col.astype('category').cat.codes if col.dtype == 'object' else col)

y = df["fraud_label"]

# Predictions
y_pred = model.predict(X)

# Confusion Matrix
cm = confusion_matrix(y, y_pred)
print("\nConfusion Matrix:")
print(cm)

# Classification report
print("\nClassification Report:")
print(classification_report(y, y_pred))

# 🔴 FALSE NEGATIVES (MOST IMPORTANT)
false_negatives = df[(y == 1) & (y_pred == 0)]

print("\n🚨 FALSE NEGATIVES COUNT:", len(false_negatives))

# Save them
false_negatives.to_excel("false_negatives.xlsx", index=False)

print("✅ False negatives saved to false_negatives.xlsx")