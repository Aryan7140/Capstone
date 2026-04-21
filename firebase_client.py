import urllib.request
import urllib.error
import json
import base64
from datetime import datetime

PROJECT_ID = "capstone-ea711"
API_KEY = "AIzaSyD51sR8Q_N8YXRl53v1Q-PCTXNv39dJd7Q"
BASE_URL = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents"

def _make_request(url, method="GET", data=None):
    headers = {'Content-Type': 'application/json'}
    req = urllib.request.Request(url, headers=headers, method=method)
    if data:
        req.data = json.dumps(data).encode("utf-8")
    
    try:
        res = urllib.request.urlopen(req)
        return json.loads(res.read().decode("utf-8")), res.status
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None, 404
        print(f"Firebase {method} ERROR:", e.code, e.read().decode("utf-8"))
        return None, e.code
    except Exception as e:
        print(f"Firebase request failed: {e}")
        return None, 500

def _get_entity_doc_id(entity_type, entity_value):
    # Make a safe document ID: e.g., 'phone_9876543210', 'email_abc@dev.com'
    # Firestore allows most characters except '/'
    safe_val = str(entity_value).replace("/", "_").strip().lower()
    return f"{entity_type}_{safe_val}"

def get_entity_statuses(entities):
    """
    Given a list of tuples like [('phone', '9876543210'), ('email', 'test@test.com')]
    Returns a dict mapping (type, value) -> object with status and details
    """
    results = {}
    for etype, evalue in entities:
        doc_id = _get_entity_doc_id(etype, evalue)
        url = f"{BASE_URL}/entities/{doc_id}?key={API_KEY}"
        doc, status_code = _make_request(url, "GET")
        
        if status_code == 200 and doc and "fields" in doc:
            status = doc["fields"].get("status", {}).get("stringValue", "SAFE")
            last_seen = doc["fields"].get("last_seen", {}).get("stringValue", "")
            
            results[(etype, evalue)] = {
                "status": status,
                "last_seen": last_seen
            }
            
    return results

def save_entity(entity_type, entity_value, status, details=None):
    """
    Save or update an entity in Firestore.
    status should be 'FLAGGED' or 'SAFE'.
    If it's already FLAGGED, we don't downgrade it to SAFE.
    """
    doc_id = _get_entity_doc_id(entity_type, entity_value)
    url = f"{BASE_URL}/entities/{doc_id}?key={API_KEY}"
    
    # Check current status
    existing_doc, code = _make_request(url, "GET")
    if code == 200 and existing_doc and "fields" in existing_doc:
        current_status = existing_doc["fields"].get("status", {}).get("stringValue", "SAFE")
        if current_status == "FLAGGED" and status == "SAFE":
            # Don't downgrade a known bad entity
            return
            
    doc_data = {
        "fields": {
            "entity_type": {"stringValue": entity_type},
            "entity_value": {"stringValue": str(entity_value)},
            "status": {"stringValue": status},
            "last_seen": {"stringValue": datetime.utcnow().isoformat() + "Z"}
        }
    }
    
    if details:
        doc_data["fields"]["details"] = {"stringValue": str(details)}

    # We use PATCH to create or update (upsert)
    patch_url = f"{url}&updateMask.fieldPaths=status&updateMask.fieldPaths=last_seen&updateMask.fieldPaths=entity_type&updateMask.fieldPaths=entity_value"
    _make_request(patch_url, "PATCH", data=doc_data)

def save_investigation(record):
    """
    Save the full investigation record to the 'investigations' collection.
    """
    url = f"{BASE_URL}/investigations?key={API_KEY}"
    
    # Very basic conversion of python dict to Firestore REST format
    # Since the record is complex, we just store it as a JSON string for simplicity
    # Or convert strings, booleans, and numbers
    
    # Easiest way to store an unstructured dict in Firestore REST is as a string
    # or implement a deep converter. For simplicity, we stringify the object
    # except for a few top-level queryable fields.
    
    doc_data = {
        "fields": {
            "timestamp": {"stringValue": datetime.utcnow().isoformat() + "Z"},
            "threat_level": {"stringValue": record.get("overall_threat_level", "LOW")},
            "combined_score": {"doubleValue": float(record.get("combined_threat_score", 0))},
            "investigation_data": {"stringValue": json.dumps(record)}
        }
    }
    
    _make_request(url, "POST", data=doc_data)
