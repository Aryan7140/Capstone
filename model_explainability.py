import pandas as pd
import joblib
import shap
import matplotlib.pyplot as plt

# Load model
model = joblib.load("xgb_model.pkl")

# Load dataset
df = pd.read_excel("indian_cities_rupees_dataset.xlsx")

# Select features
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

# Sample
X_sample = X.sample(200, random_state=42)

# SHAP explainer
explainer = shap.Explainer(model.predict_proba, X_sample)

shap_values = explainer(X_sample)

# ✅ FIX: select fraud class only
shap_values = shap_values[..., 1]

# =========================
# Visualizations
# =========================

# Summary
shap.plots.beeswarm(shap_values, show=False)
plt.savefig("shap_summary.png")
plt.close()

# Feature importance
shap.plots.bar(shap_values, show=False)
plt.savefig("shap_bar.png")
plt.close()

# Single prediction
shap.plots.waterfall(shap_values[0], show=False)
plt.savefig("shap_waterfall.png")
plt.close()

print("✅ SHAP analysis completed successfully")