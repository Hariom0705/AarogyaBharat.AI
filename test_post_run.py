import urllib.request
import json

# 1. Create the session first
session_url = "http://127.0.0.1:18081/apps/app/users/user/sessions/test_session"
req_session = urllib.request.Request(
    session_url,
    method="POST",
    headers={"Content-Type": "application/json"}
)
try:
    with urllib.request.urlopen(req_session) as f:
        print("Session Created:", f.status, f.read().decode('utf-8'))
except urllib.error.HTTPError as e:
    print("Session Creation Error:", e.code, e.read().decode('utf-8'))

# 2. Now run the message query
data = json.dumps({
    "app_name": "app",
    "user_id": "user",
    "session_id": "test_session",
    "new_message": {
        "role": "user",
        "parts": [{"text": "hello, who are you and what are my symptoms?"}]
    }
}).encode('utf-8')

req = urllib.request.Request(
    "http://127.0.0.1:18081/run",
    data=data,
    headers={"Content-Type": "application/json"},
    method="POST"
)

try:
    with urllib.request.urlopen(req) as f:
        print("Success:", f.status, f.read().decode('utf-8'))
except urllib.error.HTTPError as e:
    print("Error:", e.code, e.read().decode('utf-8'))

