# 5G Honeypot Testbed — Code Submission
Bachelor Thesis: Reproducible High-Interaction 5G Honeypot Testbed for ISP Security Research

## Overview
This repository contains the complete configuration and attack scripts for the three-VM
5G honeypot testbed described in the thesis. The testbed consists of three virtual machines
running NixOS, connected via an isolated VMware Workstation virtual network (VMnet2,
192.168.134.0/24).

| VM       | IP Address       | Role                        |
|----------|------------------|-----------------------------|
| sim      | 192.168.134.128  | Open5GS 5G Core + Logging   |
| ran      | 192.168.134.129  | UERANSIM gNB + UE           |
| attacker | 192.168.134.130  | Attack tooling              |

---

## Repository Structure

testbed/

├── README.md
├── sim/
│   ├── configuration.nix
│   ├── hardware-configuration.nix
│   └── open5gs/
│       ├── nrf.yaml
│       ├── amf.yaml
│       ├── smf.yaml
│       ├── upf.yaml
│       ├── ausf.yaml
│       ├── udm.yaml
│       ├── udr.yaml
│       └── pcf.yaml
├── ran/
│   ├── configuration.nix
│   ├── hardware-configuration.nix
│   └── ueransim/
│       ├── gnb.yaml
│       └── ue.yaml
├── attacker/
│   ├── configuration.nix
│   ├── hardware-configuration.nix
│   └── attacks/
│       ├── 01-core-infiltration/
│       │   ├── stage2a_rogue_nf.py
│       │   └── stage4_discovery.py
│       ├── 02-subscriber-exfiltration/
│       │   ├── stage6_udm_query.py
│       │   ├── stage7_bruteforce.py
│       │   ├── stage8_discovery.py
│       │   ├── stage8_jwt_forge.py
│       │   └── stage10_exfil.py
│       └── 03-service-disruption/
│           ├── stage13_rogue_smf.py
│           ├── stage11_gtpu_flood.py
│           ├── stage14_rogue_listener.py
│           ├── stage15a_smf_sbi_flood.py
│           └── stage15b_pfcp_flood.py
└── logs/
    ├── kernel_log.txt
    ├── auditd_attacker_commands.txt
    ├── open5gs/
    │   ├── nrf.log
    │   ├── amf.log
    │   ├── smf.log
    │   ├── upf.log
    │   ├── ausf.log
    │   ├── udm.log
    │   ├── udr.log
    │   └── pcf.log
    └── pcap/
        └── capture_*.pcap


---

## Locating Log Evidence — Four Logging Layers

All logging is instrumented on `sim` (192.168.134.128). SSH in as root to access logs.

### Layer 1 — Network-Level Event Index (iptables LOG)
Connection-level events for all monitored protocols, written to the kernel log.

**Access:**
```bash
# All monitored traffic
journalctl -k | grep -E "N2-NGAP:|N3-GTPU:|N4-PFCP:|SBI:|WebUI:|SSH:"

# Filter by protocol
journalctl -k | grep "SBI:"      # NRF/UDM/SMF SBI traffic (port 7777/7778/7779)
journalctl -k | grep "N2-NGAP:"  # NGAP signalling (port 38412)
journalctl -k | grep "N3-GTPU:"  # GTP-U data plane (port 2152)
journalctl -k | grep "N4-PFCP:"  # PFCP session management (port 8805)
journalctl -k | grep "WebUI:"    # Open5GS WebUI (port 3000)
journalctl -k | grep "SSH:"      # SSH access attempts (port 22)

# Filter by attacker IP
journalctl -k | grep "192.168.134.130"
```

Each log entry contains: timestamp, source IP, destination IP, protocol, port, packet flags.

---

### Layer 2 — Full Packet Capture (pcap)
Complete byte-level capture of all traffic crossing ens33, stored as rotating ring-buffer
files. Decodable in Wireshark for protocol-level analysis including full HTTP/2 SBI payloads.

**Access:**
```bash
# List capture files
ls -la /var/log/pcap/

# Check capture service status
systemctl status pcap-capture

# View pcap from command line (tshark)
tshark -r /var/log/pcap/capture_00001_*.pcap -n host 192.168.134.130

# Filter to specific protocols
tshark -r /var/log/pcap/capture_00001_*.pcap -Y "http2"        # SBI traffic
tshark -r /var/log/pcap/capture_00001_*.pcap -Y "ngap"         # NGAP signalling
tshark -r /var/log/pcap/capture_00001_*.pcap -Y "gtpv1"        # GTP-U traffic
```

**Recommended**: copy files to a Windows/Linux machine and open in Wireshark GUI.
Use `Follow → HTTP/2 Stream` to read full SBI API request/response payloads.

**Copy to local machine:**
```bash
scp root@192.168.134.128:/var/log/pcap/capture_00001_*.pcap ./
```

---

### Layer 3 — Host-Level Command Audit (auditd)
Records every process execution by the `netops` account (auid=1000), attributed to the
authenticated login session. Captures commands run during shell access in Scenario 2.

**Access:**
```bash
# All attacker commands (netops session)
ausearch -k attacker_commands -i

# Filter by time range
ausearch -k attacker_commands -i --start 11:00:00 --end 12:00:00

# Show only executed commands
ausearch -k attacker_commands -i | grep "type=EXECVE" -A1 | grep "a0="
```

Each record contains: timestamp, login UID (auid), effective UID, command executed,
full argument list, working directory.

**Note:** Only covers the `netops` account (auid=1000). Activity under other accounts
is not captured by this rule.

---

### Layer 4 — NF Application Logs
Structured log output from each Open5GS network function, capturing protocol-level
decisions, NF registration events, authentication outcomes and session state changes.

**Access:**
```bash
# Individual NF logs
tail -f /var/log/open5gs/nrf.log    # NF registration and discovery events
tail -f /var/log/open5gs/amf.log    # UE registration, SMF selection
tail -f /var/log/open5gs/smf.log    # PDU session management
tail -f /var/log/open5gs/upf.log    # User plane, GTP-U processing
tail -f /var/log/open5gs/ausf.log   # Authentication
tail -f /var/log/open5gs/udm.log    # Subscriber data queries
tail -f /var/log/open5gs/udr.log    # Database operations
tail -f /var/log/open5gs/pcf.log    # Policy decisions

# Search across all NF logs
grep -r "192.168.134.130" /var/log/open5gs/   # Attacker IP
grep -r "imsi-999700000000001" /var/log/open5gs/  # Test subscriber
grep -r "REGISTERED" /var/log/open5gs/nrf.log     # NF registrations
```

---

## Running the Attack Scripts

All scripts run from the `attacker` VM (192.168.134.130). SSH in as root.

**Prerequisites:**
- All three VMs running and healthy
- gNB running on `ran`: `sudo nr-gnb -c /etc/ueransim/gnb.yaml`
- UE attached on `ran`: `sudo nr-ue -c /etc/ueransim/ue.yaml`

**Scenario 1 — Core Infiltration:**
```bash
cd /opt/attacks/01-core-infiltration
python3 stage2a_rogue_nf.py        # Rogue NF registration
python3 stage4_discovery.py        # Topology enumeration
```

**Scenario 2 — Subscriber Data Exfiltration:**
```bash
cd /opt/attacks/02-subscriber-exfiltration
python3 stage6_udm_query.py        # UDM enumeration
python3 stage7_bruteforce.py       # SSH brute-force
python3 stage8_discovery.py        # File discovery
python3 stage8_jwt_forge.py        # JWT forgery
```

**Scenario 3 — Service Disruption:**
```bash
cd /opt/attacks/03-service-disruption
python3 stage13_rogue_smf.py       # Rogue SMF registration
sudo python3 stage11_gtpu_flood.py # GTP-U flood (requires root for raw sockets)
python3 stage15a_smf_sbi_flood.py  # SMF SBI flood
sudo python3 stage15b_pfcp_flood.py # PFCP flood
python3 stage14_rogue_listener.py  # Rogue SMF listener (run before UE attach)
```

---

## Important Notes

**Credentials (synthetic lab values only — not real operator data):**
- `netops` account on `sim`: username `netops`, password `Summer2024!`
  (deliberately seeded weak credential for Scenario 2, Stage 7)
- Subscriber credentials: IMSI `999700000000001`, K `465B5CE8B199B49FAA5F0A2EE238A6BC`,
  OPc `E8ED289DEBA952E4283B54E88E6183CA`
  (test PLMN 999/70 — not a real operator)
- JWT signing secret in `/var/lib/webui/.env` on `sim` — recovered organically
  during Stage 8 execution, not known prior to that stage

**Network isolation:**
The testbed runs on VMware Workstation's VMnet2 (192.168.134.0/24), isolated from
production networks. `sim` has a second interface (ens37) for package management only.

**Reproducibility gaps (documented in thesis Section 7.5):**
- Open5GS YAML configs were edited at runtime and are not generated from the NixOS
  configuration — apply the provided YAML files manually after nixos-rebuild
- Attack scripts are separate artifacts not declared in the NixOS configuration
- `schemathesis` was installed via pip venv, not Nix — not required for any executed scenario

## Provided Log Evidence

Pre-collected log evidence from the scenario execution runs described in the thesis
is provided in the `logs/` directory for reference and verification.

### logs/kernel_log.txt
Kernel-level iptables LOG entries covering all monitored protocols during scenario
execution. Filter by protocol prefix or attacker IP:
- `grep "SBI:" kernel_log.txt` — NRF/UDM/SMF SBI interactions
- `grep "N2-NGAP:" kernel_log.txt` — NGAP signalling during UE attach
- `grep "192.168.134.130" kernel_log.txt` — all attacker-originated traffic

### logs/auditd_attacker_commands.txt
auditd records of every process execution by the `netops` account (auid=1000)
during Scenario 2 shell access. Key entries to look for:
- `cat /var/lib/webui/.env` — JWT secret recovery (Stage 8)
- `sudo whoami` — privilege escalation confirmation (Stage 7)
- Any `scp` or file transfer commands (Stage 10)

### logs/open5gs/
Individual NF application logs from scenario execution:
- `nrf.log` — rogue NF registration events (Stages 2a, 13)
- `amf.log` — SMF selection decisions (Stage 14)
- `smf.log` — SBI parse rejections from flood attempts (Stage 15a)
- `upf.log` — GTP-U type rejections from flood attempts (Stage 11)
- `udm.log` — subscriber enumeration queries (Stage 6)

### logs/pcap/
Full packet captures from scenario execution, readable in Wireshark.
Recommended filters:
- `http2 && ip.addr == 192.168.134.130` — all SBI interactions from attacker
- `ngap` — NGAP signalling during UE attach (Stage 5)
- `ip.addr == 192.168.134.130 && tcp.port == 3000` — WebUI interactions
  (Stages 2b, 8x, 9)

**Note on pcap file size**: captures use a 200MB ring buffer. Files covering the
scenario execution period are included; earlier captures from testbed setup may
be omitted to reduce submission size.
