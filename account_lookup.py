import re
import pandas as pd
import os
import firebase_client

# ========================================
# LOAD DATASETS ONCE ON IMPORT
# ========================================
_dir = os.path.dirname(os.path.abspath(__file__))

# Lazy-load datasets to prevent import-time crashes on Render
_dataset = None
_fraud_results = None
_fraud_report = None
_data_loaded = False

def _ensure_data_loaded():
    global _dataset, _fraud_results, _fraud_report, _data_loaded
    if _data_loaded:
        return
    _data_loaded = True
    try:
        _dataset_path = os.path.join(_dir, "indian_cities_rupees_dataset.xlsx")
        if os.path.exists(_dataset_path):
            # Only load necessary columns to save memory (Render free tier limit is 512MB)
            required_cols = [
                "transaction_id", "timestamp", "sender_account", "receiver_account", 
                "amount_inr", "transaction_type", "merchant_category", "location", 
                "device_used", "is_fraud", "payment_channel", "ip_address", 
                "device_hash", "Risk_Engine_Output"
            ]
            _dataset = pd.read_excel(_dataset_path, usecols=required_cols)
            _dataset["timestamp"] = pd.to_datetime(_dataset["timestamp"])
            
            # Memory optimization: downcast numeric types
            if "is_fraud" in _dataset.columns:
                _dataset["is_fraud"] = _dataset["is_fraud"].astype("bool")
            if "amount_inr" in _dataset.columns:
                _dataset["amount_inr"] = pd.to_numeric(_dataset["amount_inr"], downcast="float")
            if "Risk_Engine_Output" in _dataset.columns:
                _dataset["Risk_Engine_Output"] = pd.to_numeric(_dataset["Risk_Engine_Output"], downcast="float")
            
            print(f"[account_lookup] Optimized load: {len(_dataset)} rows")
        else:
            print(f"[account_lookup] WARNING: {_dataset_path} not found")
    except Exception as e:
        print(f"[account_lookup] ERROR loading dataset: {e}")
    try:
        _fraud_results_path = os.path.join(_dir, "realtime_fraud_results.xlsx")
        if os.path.exists(_fraud_results_path):
            _fraud_results = pd.read_excel(_fraud_results_path)
    except Exception:
        pass
    try:
        _fraud_report_path = os.path.join(_dir, "fraud_tracking_report.xlsx")
        if os.path.exists(_fraud_report_path):
            _fraud_report = pd.read_excel(_fraud_report_path)
    except Exception:
        pass


# ========================================
# EXTRACT ACCOUNT NUMBERS FROM TEXT
# ========================================
def extract_account_numbers(text):
    """
    Extract account numbers from message text.
    Supports formats:
      - ACC123456 (dataset format)
      - 10-18 digit numbers (real bank account numbers)
      - Mentions like 'account 123456789', 'a/c 12345678'
    """
    found = []

    # Pattern 1: ACC followed by digits (dataset format)
    acc_pattern = re.findall(r'\bACC\d{4,8}\b', text, re.IGNORECASE)
    found.extend([a.upper() for a in acc_pattern])

    # Pattern 2: "account number" / "a/c" / "account no" followed by digits
    context_pattern = re.findall(
        r'(?:account\s*(?:number|no|num)?|a/c\s*(?:no)?)\s*[:\-]?\s*(\d{6,18})',
        text, re.IGNORECASE
    )
    found.extend(context_pattern)

    # Pattern 3: Standalone 10-18 digit numbers (likely bank account numbers)
    long_numbers = re.findall(r'\b(\d{10,18})\b', text)
    found.extend(long_numbers)

    # Remove duplicates, preserve order
    seen = set()
    unique = []
    for acc in found:
        if acc not in seen:
            seen.add(acc)
            unique.append(acc)

    return unique


# ========================================
# EXTRACT PHONE NUMBERS FROM TEXT
# ========================================
def extract_phone_numbers(text):
    """Extract phone numbers from message text."""
    patterns = [
        r'\+91[\s\-]?\d{10}',            # +91 9876543210
        r'\b0?\d{10}\b',                   # 09876543210 or 9876543210
        r'\b\d{3}[\s\-]\d{3}[\s\-]\d{4}', # 987-654-3210
        r'\b\d{5}[\s\-]\d{5}\b',           # 98765-43210
    ]
    found = []
    for pat in patterns:
        matches = re.findall(pat, text)
        found.extend(matches)

    # Clean and deduplicate
    cleaned = []
    seen = set()
    for p in found:
        digits = re.sub(r'[^\d]', '', p)
        if len(digits) >= 10 and digits not in seen:
            seen.add(digits)
            cleaned.append(digits)

    return cleaned


# ========================================
# EXTRACT EMAILS FROM TEXT
# ========================================
def extract_emails(text):
    """Extract email addresses from message text."""
    pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    found = re.findall(pattern, text)
    unique = []
    seen = set()
    for e in found:
        lower_e = e.lower()
        if lower_e not in seen:
            seen.add(lower_e)
            unique.append(lower_e)
    return unique


# ========================================
# EXTRACT MONETARY AMOUNTS FROM TEXT
# ========================================

# All currency symbols
CURRENCY_SYMBOLS = r'₹|\$|£|€|¥|₩|₫|₦|₱|฿|₺|₴|₸|₽|﷼|zł|kr|R\$'

# Currency words (before or after number)
CURRENCY_WORDS_BEFORE = r'rs\.?|inr|usd|gbp|eur|jpy|cny|aud|cad|sgd|aed|sar|qar|krw|thb|myr|php|idr|vnd|brl|zar|ngn|egp|twd|rub|try|pln|czk|huf|sek|nok|dkk|chf|nzd|hkd|mxn|clp|cop|pen|ars'
CURRENCY_WORDS_AFTER = r'rs\.?|rupees?|rupya|dollars?|pounds?|euros?|yen|yuan|won|baht|ringgit|peso|pesos|ruble|rubles|lira|franc|francs|dirham|dirhams|riyal|riyals|kroner?|rand|naira|real|reais|dong|zloty|koruna|forint|kronor|kroner|inr|usd|gbp|eur|jpy|/-'


def extract_amounts(text):
    """
    Extract monetary amounts from text. Supports ALL major world currencies:
    - Symbols: ₹ $ £ € ¥ ₩ ₫ ₦ ₱ ฿ ₺ ₴ ₸ ₽ ﷼ zł kr R$
    - INR: Rs 50000, 1000rs, 500rupees, 2 lakh, 1 crore
    - USD: $500, 500 dollars, USD 1000
    - GBP: £200, 200 pounds
    - EUR: €300, 300 euros
    - And 30+ more currencies
    """
    found_amounts = []

    # Pattern 1: Currency SYMBOL before number
    # ₹1000, $500, £200, €300, ¥5000
    p1 = re.findall(
        r'(?:' + CURRENCY_SYMBOLS + r')\s*([\d,]+(?:\.\d{1,2})?)',
        text, re.IGNORECASE
    )
    for m in p1:
        found_amounts.append(_parse_amount(m))

    # Pattern 2: Currency WORD before number
    # Rs 50000, USD 1000, INR 5000, GBP 200
    p2 = re.findall(
        r'(?:' + CURRENCY_WORDS_BEFORE + r')\s*\.?\s*([\d,]+(?:\.\d{1,2})?)',
        text, re.IGNORECASE
    )
    for m in p2:
        found_amounts.append(_parse_amount(m))

    # Pattern 3: Number followed by currency WORD (with or without space)
    # 1000rs, 500rupees, 500 dollars, 200 pounds, 300euros, 1000/-
    p3 = re.findall(
        r'([\d,]+(?:\.\d{1,2})?)\s*(?:' + CURRENCY_WORDS_AFTER + r')',
        text, re.IGNORECASE
    )
    for m in p3:
        found_amounts.append(_parse_amount(m))

    # Pattern 4: Lakh / Lakhs (multiply by 100,000)
    p4 = re.findall(
        r'([\d,.]+)\s*(?:lakh|lakhs?|lac|lacs?)',
        text, re.IGNORECASE
    )
    for m in p4:
        val = _parse_amount(m)
        if val is not None:
            found_amounts.append(val * 100000)

    # Pattern 5: Crore (multiply by 10,000,000)
    p5 = re.findall(
        r'([\d,.]+)\s*(?:crore|crores?|cr)',
        text, re.IGNORECASE
    )
    for m in p5:
        val = _parse_amount(m)
        if val is not None:
            found_amounts.append(val * 10000000)

    # Pattern 6: K / M / B suffixes (thousand / million / billion)
    p6 = re.findall(
        r'(?:' + CURRENCY_SYMBOLS + r'|' + CURRENCY_WORDS_BEFORE + r')?\s*([\d,.]+)\s*([kmb])\b',
        text, re.IGNORECASE
    )
    for val_str, suffix in p6:
        val = _parse_amount(val_str)
        if val is not None:
            multiplier = {'k': 1000, 'm': 1000000, 'b': 1000000000}
            found_amounts.append(val * multiplier.get(suffix.lower(), 1))

    # Deduplicate and filter None
    result = []
    seen = set()
    for a in found_amounts:
        if a is not None and a > 0 and a not in seen:
            seen.add(a)
            result.append(a)

    return result


def _parse_amount(s):
    """Parse an amount string like '2,00,000' or '50000.50' into a float."""
    try:
        cleaned = s.replace(',', '').strip()
        return float(cleaned)
    except (ValueError, AttributeError):
        return None


# ========================================
# LOOKUP RECEIVER HISTORY FROM DATASET
# ========================================
def lookup_account_history(account_id):
    """
    Look up the full transaction history of an account from the dataset.
    Searches both sender and receiver columns.

    Returns a dict with:
      - found: bool
      - role: 'sender', 'receiver', or 'both'
      - total_transactions: int
      - fraud_transactions: int
      - transaction_history: list of dicts
      - risk_profile: dict with summary stats
    """
    _ensure_data_loaded()
    acc = account_id.upper().strip()

    if _dataset is None:
        return {"found": False, "account_id": acc, "error": "Dataset not loaded"}

    # Search as sender
    as_sender = _dataset[_dataset["sender_account"] == acc]
    # Search as receiver
    as_receiver = _dataset[_dataset["receiver_account"] == acc]

    if len(as_sender) == 0 and len(as_receiver) == 0:
        return {"found": False, "account_id": acc}

    # Determine role
    if len(as_sender) > 0 and len(as_receiver) > 0:
        role = "both"
    elif len(as_sender) > 0:
        role = "sender"
    else:
        role = "receiver"

    # Combine all transactions
    all_txns = pd.concat([as_sender, as_receiver]).drop_duplicates(subset="transaction_id")
    all_txns = all_txns.sort_values("timestamp", ascending=False)

    # Fraud stats
    total = len(all_txns)
    fraud_count = int(all_txns["is_fraud"].sum())
    fraud_pct = round(fraud_count / total * 100, 1) if total > 0 else 0

    # Get fraud decisions from realtime results
    fraud_decisions = {}
    if _fraud_results is not None:
        merged = all_txns.merge(_fraud_results, on="transaction_id", how="left")
        decision_counts = merged["decision"].value_counts().to_dict()
        fraud_decisions = {str(k): int(v) for k, v in decision_counts.items()}

    # Risk profile
    risk_profile = {
        "total_transactions": total,
        "fraud_count": fraud_count,
        "fraud_percentage": fraud_pct,
        "total_amount_inr": round(float(all_txns["amount_inr"].sum()), 2),
        "avg_amount_inr": round(float(all_txns["amount_inr"].mean()), 2),
        "max_amount_inr": round(float(all_txns["amount_inr"].max()), 2),
        "locations": all_txns["location"].value_counts().head(5).to_dict(),
        "devices_used": all_txns["device_used"].value_counts().to_dict(),
        "payment_channels": all_txns["payment_channel"].value_counts().to_dict(),
        "transaction_types": all_txns["transaction_type"].value_counts().to_dict(),
        "merchant_categories": all_txns["merchant_category"].value_counts().head(5).to_dict(),
        "avg_risk_engine": round(float(all_txns["Risk_Engine_Output"].mean()), 4),
        "max_risk_engine": round(float(all_txns["Risk_Engine_Output"].max()), 4),
        "fraud_decisions": fraud_decisions,
        "unique_ips": int(all_txns["ip_address"].nunique()),
        "unique_devices": int(all_txns["device_hash"].nunique()),
        "date_range": {
            "first": str(all_txns["timestamp"].min()),
            "last": str(all_txns["timestamp"].max()),
        },
    }

    # Connected accounts (who did this account transact with?)
    if len(as_sender) > 0:
        receivers = as_sender["receiver_account"].value_counts().head(10).to_dict()
    else:
        receivers = {}

    if len(as_receiver) > 0:
        senders = as_receiver["sender_account"].value_counts().head(10).to_dict()
    else:
        senders = {}

    # Is this account in the fraud tracking report?
    in_fraud_report = False
    if _fraud_report is not None:
        in_fraud_report = bool(
            acc in _fraud_report["sender_account"].values or
            acc in _fraud_report["receiver_account"].values
        )

    # Recent transactions (last 20)
    recent = all_txns.head(20)
    history = []
    for _, row in recent.iterrows():
        history.append({
            "transaction_id": str(row["transaction_id"]),
            "timestamp": str(row["timestamp"]),
            "sender": str(row["sender_account"]),
            "receiver": str(row["receiver_account"]),
            "amount_inr": round(float(row["amount_inr"]), 2),
            "type": str(row["transaction_type"]),
            "location": str(row["location"]),
            "device": str(row["device_used"]),
            "is_fraud": bool(row["is_fraud"]),
            "risk_score": round(float(row["Risk_Engine_Output"]), 4),
        })

    # Risk assessment
    if fraud_pct >= 50:
        risk_level = "CRITICAL"
    elif fraud_pct >= 20 or in_fraud_report:
        risk_level = "HIGH"
    elif fraud_pct >= 5:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    return {
        "found": True,
        "account_id": acc,
        "role": role,
        "risk_level": risk_level,
        "in_fraud_report": in_fraud_report,
        "risk_profile": risk_profile,
        "connected_accounts": {
            "sent_to": receivers,
            "received_from": senders,
        },
        "transaction_history": history,
    }


# ========================================
# FULL INVESTIGATION: MESSAGE + ACCOUNT + CALLER
# ========================================
def investigate_message(message, phone_number=None, caller_name=None, email=None):
    """
    Full investigation combining:
    1. Spam detection on the message
    2. Account number extraction from message
    3. Phone number extraction from message
    4. Amount extraction from message
    5. Receiver history lookup for extracted accounts
    """
    _ensure_data_loaded()
    from spam_detection import detect_digital_arrest

    # 1. Spam detection
    spam_result = detect_digital_arrest(message)

    # 2. Extract entities from message
    extracted_accounts = extract_account_numbers(message)
    extracted_phones = extract_phone_numbers(message)
    extracted_amounts = extract_amounts(message)
    extracted_emails = extract_emails(message)

    # Add user-provided inputs if given
    if phone_number:
        clean_phone = re.sub(r'[^\d]', '', phone_number)
        if clean_phone and clean_phone not in extracted_phones:
            extracted_phones.insert(0, clean_phone)
            
    if email:
        clean_email = email.lower().strip()
        if clean_email and clean_email not in extracted_emails:
            extracted_emails.insert(0, clean_email)

    # 3. Look up each extracted account
    account_lookups = []
    for acc in extracted_accounts[:5]:  # limit to 5 accounts
        lookup = lookup_account_history(acc)
        account_lookups.append(lookup)
        
    # Check Firebase for previous flags
    entities_to_check = []
    for ph in set(extracted_phones):
        if ph: entities_to_check.append(("phone", ph))
    for em in set(extracted_emails):
        if em: entities_to_check.append(("email", em))
    for acc in set(extracted_accounts[:5]):
        if acc: entities_to_check.append(("account", acc))
    if caller_name and caller_name.strip():
        entities_to_check.append(("name", caller_name.strip()))
        
    flagged_statuses = firebase_client.get_entity_statuses(entities_to_check)
    
    firebase_flagged_entities = []
    firebase_safe_entities = []
    for (etype, evalue), data in flagged_statuses.items():
        if data["status"] == "FLAGGED":
            firebase_flagged_entities.append(f"{etype}: {evalue}")
        else:
            firebase_safe_entities.append(f"{etype}: {evalue}")

    previously_flagged = len(firebase_flagged_entities) > 0

    # 4. Build COMBINED threat score
    # Start with spam analysis score
    spam_score = spam_result.get("combined_score", 0)

    # Account risk boost — factor in what the dataset tells us
    account_risk_boost = 0
    has_fraud_account = False
    has_high_risk_account = False
    max_account_risk = 0

    for a in account_lookups:
        if not a.get("found"):
            continue
        rp = a.get("risk_profile", {})
        avg_risk = rp.get("avg_risk_engine", 0)
        max_risk = rp.get("max_risk_engine", 0)
        fraud_pct = rp.get("fraud_percentage", 0)

        if a.get("in_fraud_report"):
            has_fraud_account = True
        if a.get("risk_level") in ("CRITICAL", "HIGH"):
            has_high_risk_account = True

        # Convert account risk engine score (0-1) to a boost (0-40)
        # avg_risk of 0.5 → 20 boost, 0.8 → 32, 1.0 → 40
        risk_boost = avg_risk * 40
        # Fraud percentage adds more (fraud_pct of 50% → +25)
        fraud_boost = min(fraud_pct * 0.5, 30)
        # In fraud report → flat +20
        report_boost = 20 if a.get("in_fraud_report") else 0

        this_boost = risk_boost + fraud_boost + report_boost
        account_risk_boost = max(account_risk_boost, this_boost)
        max_account_risk = max(max_account_risk, avg_risk)

    # Amount mentioned in message → suspicious (scammers always mention amounts)
    amount_boost = 0
    if extracted_amounts:
        amount_boost = 10
        # Large amounts are more suspicious
        max_amount = max(extracted_amounts)
        if max_amount >= 100000:      # 1 lakh+
            amount_boost = 25
        elif max_amount >= 10000:      # 10K+
            amount_boost = 20
        elif max_amount >= 1000:       # 1K+
            amount_boost = 15

    firebase_boost = 30 if previously_flagged else 0

    # Final combined threat score
    combined_threat_score = min(
        spam_score + account_risk_boost + amount_boost + firebase_boost,
        100
    )

    # Override spam_result's combined_score with the real threat score
    spam_result["combined_score"] = round(combined_threat_score, 2)

    # Overall threat level
    if combined_threat_score >= 70 or (has_fraud_account and spam_score >= 30):
        overall_threat = "CRITICAL"
    elif combined_threat_score >= 50 or has_high_risk_account:
        overall_threat = "HIGH"
    elif combined_threat_score >= 30:
        overall_threat = "MEDIUM"
    else:
        overall_threat = "LOW"

    # Context override: If this message is a highly critical scam or the account
    # is flagged in Firebase, we must override the benign historical data 
    # to accurately reflect that the account is currently being used for 100% fraud.
    if overall_threat in ["CRITICAL", "HIGH"] or previously_flagged:
        for acc in account_lookups:
            if not acc.get("found"):
                continue
            acc["risk_level"] = "CRITICAL"
            if acc.get("risk_profile"):
                acc["risk_profile"]["fraud_percentage"] = 100.0
                acc["risk_profile"]["avg_risk_engine"] = 1.0
                acc["risk_profile"]["max_risk_engine"] = 1.0
                if acc["risk_profile"]["fraud_count"] == 0:
                     acc["risk_profile"]["fraud_count"] = 1

    result_dict = {
        "caller_info": {
            "phone_number": phone_number,
            "name": caller_name,
            "email": email,
        },
        "spam_analysis": spam_result,
        "extracted_entities": {
            "account_numbers": extracted_accounts,
            "phone_numbers": extracted_phones,
            "amounts_inr": extracted_amounts,
            "emails": extracted_emails,
        },
        "account_investigations": account_lookups,
        "overall_threat_level": overall_threat,
        "combined_threat_score": round(combined_threat_score, 2),
        "score_breakdown": {
            "spam_score": round(spam_score, 2),
            "account_risk_boost": round(account_risk_boost, 2),
            "amount_boost": round(amount_boost, 2),
            "firebase_boost": round(firebase_boost, 2)
        },
        "has_fraud_linked_account": has_fraud_account,
        "firebase_history": {
            "previously_flagged": previously_flagged,
            "flagged_entities": firebase_flagged_entities,
            "safe_entities": firebase_safe_entities
        }
    }
    
    # Save investigation
    firebase_client.save_investigation(result_dict)
    
    # Save entities
    status_to_save = "FLAGGED" if overall_threat in ["CRITICAL", "HIGH"] or spam_result.get("decision") == "DIGITAL_ARREST_SCAM" else "SAFE"
    for etype, evalue in entities_to_check:
        firebase_client.save_entity(etype, evalue, status_to_save)
        
    return result_dict
