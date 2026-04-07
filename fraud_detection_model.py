import pandas as pd
import joblib

# Load trained model
model = joblib.load("fraud_detection_model.pkl")

# Load processed dataset
X = pd.read_csv("processed_features.csv")

# Predict fraud
predictions = model.predict(X)

results = X.copy()
results["fraud_prediction"] = predictions

results.to_csv("fraud_predictions.csv", index=False)

print("Fraud detection completed")