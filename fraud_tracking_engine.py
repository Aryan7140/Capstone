import pandas as pd

# Load real-time results
realtime = pd.read_excel("realtime_fraud_results.xlsx")

# Load original data
df = pd.read_excel("indian_cities_rupees_dataset.xlsx")

# Merge
merged = pd.merge(realtime, df, on="transaction_id")

fraud_cases = merged[merged["decision"] == "FRAUD"]

tracking_report = fraud_cases[
    [
        "transaction_id",
        "timestamp",
        "sender_account",
        "receiver_account",
        "ip_address",
        "device_hash"
    ]
]

print("Fraud Tracking Results")
print(tracking_report.head())

tracking_report.to_excel("fraud_tracking_report.xlsx", index=False)