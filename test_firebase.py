import urllib.request
import urllib.error
import json

project_id = "capstone-ea711"
api_key = "AIzaSyD51sR8Q_N8YXRl53v1Q-PCTXNv39dJd7Q"

def test_firestore():
    url = f"https://firestore.googleapis.com/v1/projects/{project_id}/databases/(default)/documents/test_collection?key={api_key}"
    data = json.dumps({"fields": {"test": {"stringValue": "hello"}}}).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method='POST')
    try:
        res = urllib.request.urlopen(req)
        print("Firestore POST:", res.status, res.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print("Firestore POST ERROR:", e.code, e.read().decode("utf-8"))

def test_rtdb():
    url = f"https://{project_id}-default-rtdb.firebaseio.com/test.json?key={api_key}"
    data = json.dumps({"test": "hello"}).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method='PUT')
    try:
        res = urllib.request.urlopen(req)
        print("RTDB PUT:", res.status, res.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print("RTDB PUT ERROR:", e.code, e.read().decode("utf-8"))

test_firestore()
test_rtdb()
