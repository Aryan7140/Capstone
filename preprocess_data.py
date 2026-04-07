import pandas as pd
from sklearn.preprocessing import LabelEncoder

# Load dataset
df = pd.read_excel("indian_cities_rupees_dataset.xlsx")

# Columns used later for investigation
investigation_cols = [
    "transaction_id",
    "timestamp",
    "sender_account",
    "receiver_account",
    "ip_address",
    "device_hash"
]

investigation_data = df[investigation_cols]

# Remove investigation columns from training data
X = df.drop(columns=investigation_cols + ["is_fraud"])
y = df["is_fraud"]

# Encode categorical variables
encoder = LabelEncoder()

for col in X.select_dtypes(include="object"):
    X[col] = encoder.fit_transform(X[col])

# Save processed data
X.to_csv("processed_features.csv", index=False)
y.to_csv("labels.csv", index=False)
investigation_data.to_csv("investigation_data.csv", index=False)

print("Data preprocessing completed")