import pandas as pd

fraud_data = pd.read_excel("fraud_tracking_report.xlsx")

# Most suspicious accounts
fraud_accounts = fraud_data["receiver_account"].value_counts()

print("Top Fraud Accounts")
print(fraud_accounts.head())

# Suspicious IP addresses
fraud_ips = fraud_data["ip_address"].value_counts()

print("Top Fraud IP Addresses")
print(fraud_ips.head())

# Fraud timeline
fraud_data["timestamp"] = pd.to_datetime(fraud_data["timestamp"])

timeline = fraud_data.groupby(
    fraud_data["timestamp"].dt.date
).size()

print("Fraud Timeline")
print(timeline)