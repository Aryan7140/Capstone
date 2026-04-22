from flask import Flask, jsonify, send_file, request
from flask_cors import CORS
import pandas as pd
import subprocess
from spam_detection import classify_message, classify_batch, detect_digital_arrest
from account_lookup import investigate_message, lookup_account_history, extract_account_numbers

app = Flask(__name__)
CORS(app)

@app.route("/")
def index():
    return jsonify({
        "status": "online",
        "service": "FraudShield API",
        "endpoints": ["/summary", "/alerts", "/investigate", "/spam/summary", "/spam/check"]
    })

# ========================================
# EXISTING ENDPOINTS (Transaction Fraud)
# ========================================

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
    return jsonify(df.to_dict(orient="records"))

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


# ========================================
# SPAM / DIGITAL ARREST ENDPOINTS
# ========================================

@app.route("/spam/check", methods=["POST"])
def spam_check():
    data = request.get_json()
    if not data or "message" not in data:
        return jsonify({"error": "Missing 'message' field"}), 400
    result = classify_message(data["message"])
    result["message"] = data["message"]
    return jsonify(result)


@app.route("/spam/batch", methods=["POST"])
def spam_batch():
    data = request.get_json()
    if not data or "messages" not in data:
        return jsonify({"error": "Missing 'messages' field"}), 400
    results = classify_batch(data["messages"])
    return jsonify(results)


@app.route("/spam/digital-arrest", methods=["POST"])
def digital_arrest():
    data = request.get_json()
    if not data or "message" not in data:
        return jsonify({"error": "Missing 'message' field"}), 400
    result = detect_digital_arrest(data["message"])
    return jsonify(result)


@app.route("/spam/digital-arrest/batch", methods=["POST"])
def digital_arrest_batch():
    data = request.get_json()
    if not data or "messages" not in data:
        return jsonify({"error": "Missing 'messages' field"}), 400
    results = [detect_digital_arrest(msg) for msg in data["messages"]]
    summary_data = {
        "total": len(results),
        "scam": sum(1 for r in results if r["decision"] == "DIGITAL_ARREST_SCAM"),
        "suspicious": sum(1 for r in results if r["decision"] == "SUSPICIOUS"),
        "safe": sum(1 for r in results if r["decision"] == "SAFE"),
    }
    return jsonify({"results": results, "summary": summary_data})


@app.route("/spam/summary")
def spam_summary():
    sample_messages = [
        "This is CBI officer. You are under digital arrest for money laundering. Transfer Rs 2,00,000 now.",
        "Your parcel contains illegal drugs. Pay fine of Rs 50,000 or get arrested.",
        "WINNER! Claim your Rs 10,00,000 prize now. Call 09876543210.",
        "Hey, are we still meeting for coffee tomorrow?",
        "Your Aadhaar is linked to fraud. Verify identity immediately or face arrest.",
        "Hi Mom, reached safely. Will call you later.",
        "Police here. Your bank account is under investigation. Transfer all funds to this safe account.",
        "Bro can you pick me up from the station?",
    ]
    results = [detect_digital_arrest(msg) for msg in sample_messages]
    summary_data = {
        "total": len(results),
        "scam": sum(1 for r in results if r["decision"] == "DIGITAL_ARREST_SCAM"),
        "suspicious": sum(1 for r in results if r["decision"] == "SUSPICIOUS"),
        "safe": sum(1 for r in results if r["decision"] == "SAFE"),
    }
    return jsonify({"results": results, "summary": summary_data})


# ========================================
# INVESTIGATION ENDPOINTS (Account Lookup)
# ========================================

@app.route("/investigate", methods=["POST"])
def investigate():
    """
    Full investigation: Spam detection + Account extraction + Receiver history.
    Body: {
        "message": "Transfer money to ACC123456 immediately",
        "phone_number": "9876543210",   (optional)
        "name": "Unknown Caller"        (optional)
    }
    """
    data = request.get_json()
    if not data or "message" not in data:
        return jsonify({"error": "Missing 'message' field"}), 400

    result = investigate_message(
        message=data["message"],
        phone_number=data.get("phone_number"),
        caller_name=data.get("name"),
        email=data.get("email") # Pass email to investigate
    )
    return jsonify(result)


@app.route("/account/<account_id>")
def account_detail(account_id):
    """
    Look up a specific account's full transaction history.
    Example: /account/ACC182189
    """
    result = lookup_account_history(account_id)
    return jsonify(result)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=True)
