from flask import Flask, jsonify, send_file
from flask_cors import CORS
import pandas as pd
import subprocess

app = Flask(__name__)
CORS(app)

@app.route("/summary")
def summary():
    df = pd.read_excel("realtime_fraud_results.xlsx")

    fraud = len(df[df["decision"] == "FRAUD"])
    suspicious = len(df[df["decision"] == "SUSPICIOUS"])
    safe = len(df[df["decision"] == "SAFE"])

    return jsonify([
        {"name": "FRAUD", "value": fraud},
        {"name": "SUSPICIOUS", "value": suspicious},
        {"name": "SAFE", "value": safe}
    ])

@app.route("/alerts")
def alerts():
    df = pd.read_excel("realtime_fraud_results.xlsx")
    return df.to_dict(orient="records")

@app.route("/run")
def run():
    subprocess.run(["python", "realtime_detection.py"])
    return "Done"

@app.route("/shap_summary")
def shap():
    return send_file("shap_summary.png", mimetype="image/png")

@app.route("/network")
def network():
    return send_file("fraud_network.png", mimetype="image/png")

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=True)

