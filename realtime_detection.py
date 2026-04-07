import pandas as pd
import joblib
from sklearn.preprocessing import LabelEncoder
from user_behavior_engine import UserBehaviorTracker, behaviour_risk_score

# Load trained model
model = joblib.load("xgb_model.pkl")

# Load dataset
df = pd.read_excel("indian_cities_rupees_dataset.xlsx")
df["timestamp"] = pd.to_datetime(df["timestamp"])

# Initialize encoders (same columns used in training)
categorical_cols = [
    "transaction_type",
    "merchant_category",
    "location",
    "device_used",
    "payment_channel"
]

encoders = {}
for col in categorical_cols:
    le = LabelEncoder()
    df[col] = le.fit_transform(df[col].astype(str))
    encoders[col] = le

# Initialize tracker
tracker = UserBehaviorTracker()

results = []

# 🔁 Real-time simulation
for _, row in df.iterrows():

    # Step 1: Behavioral features
    features = tracker.compute_features(row)

    # Step 2: Risk score
    risk = behaviour_risk_score(features)

    # Step 3: Prepare model input (MATCH TRAINING EXACTLY)
    X_input = pd.DataFrame([[
        row["amount"],
        row["Amount_conversion"],
        row["transaction_type"],
        row["merchant_category"],
        row["location"],
        row["device_used"],
        row["time_since_last_transaction"],
        row["spending_deviation_score"],
        row["velocity_score"],
        row["geo_anomaly_score"],
        row["payment_channel"],
        row["User_Behavioral_History"],
        row["Beneficiary_Intelligence"],
        row["Transaction_Velocity"],
        row["Behavioral_Deviation"],
        row["amount_inr"]
    ]], columns=[
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
    ])

    # Ensure numeric dtype
    X_input = X_input.astype(float)

    # Step 4: ML prediction
    ml_pred = model.predict(X_input)[0]

    # Step 5: Decision logic
    if risk >= 4 or ml_pred == 1:
        decision = "FRAUD"
    elif risk >= 2:
        decision = "SUSPICIOUS"
    else:
        decision = "SAFE"

    # Step 6: Store result
    results.append({
        "transaction_id": row["transaction_id"],
        "decision": decision,
        "risk_score": risk
    })

    # Step 7: Update behavior
    tracker.update_profile(row)

# Save output
pd.DataFrame(results).to_excel("realtime_fraud_results.xlsx", index=False)

print("✅ Real-time detection completed successfully")