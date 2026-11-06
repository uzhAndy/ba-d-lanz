#!/usr/bin/env python3
"""
Simple exfiltration receiver — accepts POSTed files, writes them to disk.
Stands in for 'the attacker's server' without simulating a full C2 framework.
"""

from http.server import BaseHTTPRequestHandler, HTTPServer
import datetime

class ReceiverHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        data = self.rfile.read(length)

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"loot/exfil_{timestamp}.dat"
        with open(filename, "wb") as f:
            f.write(data)

        print(f"[+] Received {length} bytes from {self.client_address[0]} -> saved as {filename}")
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, format, *args):
        pass  # suppress default noisy logging

if __name__ == "__main__":
    print("[*] Exfil receiver listening on 0.0.0.0:8001")
    HTTPServer(("0.0.0.0", 8001), ReceiverHandler).serve_forever()
