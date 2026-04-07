import pandas as pd

# Load real-time detection output
df = pd.read_excel("realtime_fraud_results.xlsx")

print("\n🚨 FRAUD ALERT SYSTEM STARTED 🚨\n")

fraud_count = 0
suspicious_count = 0

for _, row in df.iterrows():

    if row["decision"] == "FRAUD":
        fraud_count += 1
        print(f"🔴 FRAUD ALERT → Transaction ID: {row['transaction_id']} | Risk Score: {row['risk_score']}")

    elif row["decision"] == "SUSPICIOUS":
        suspicious_count += 1
        print(f"🟡 SUSPICIOUS → Transaction ID: {row['transaction_id']} | Risk Score: {row['risk_score']}")

print("\n📊 ALERT SUMMARY")
print(f"Total FRAUD cases: {fraud_count}")
print(f"Total SUSPICIOUS cases: {suspicious_count}")

# Save alerts separately
alerts_df = df[df["decision"].isin(["FRAUD", "SUSPICIOUS"])]
alerts_df.to_excel("fraud_alerts.xlsx", index=False)

print("\n✅ Alerts saved to fraud_alerts.xlsx")