"""
Studio Sidebar Local Server
Serves _studio files at http://localhost:8765 with CORS headers.
POST /rebuild  — runs rebuild_sidebar.py and returns JSON result.
Run via serve-sidebar.bat
"""

# EXPECTED_RUNTIME_SECONDS: 300
import http.server, socketserver, os, sys, subprocess, json

import sys as _sys
_sys.path.insert(0, "G:/My Drive/Projects/_studio/utilities")
from constraint_gates import hamilton_watchdog

PORT = 8765
STUDIO = r"G:\My Drive\Projects\_studio"

class CORSHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_POST(self):
        if self.path == '/rebuild':
            try:
                result = subprocess.run(
                    [sys.executable, STUDIO + r'\rebuild_sidebar.py'],
                    capture_output=True, text=True, timeout=30
                )
                ok = result.returncode == 0
                body = json.dumps({'ok': ok, 'output': result.stdout[:200]}).encode()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', len(body))
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                body = json.dumps({'ok': False, 'output': str(e)}).encode()
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', len(body))
                self.end_headers()
                self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Only log non-200 responses to reduce noise
        if args and str(args[1]) != "200":
            super().log_message(format, *args)

os.chdir(STUDIO)
print("=" * 50)
print(f"Studio Sidebar Server running on port {PORT}")
print(f"Serving: {STUDIO}")
print(f"URL: http://localhost:{PORT}")
print("Press Ctrl+C to stop")
print("=" * 50)

with socketserver.TCPServer(("", PORT), CORSHandler) as httpd:
    httpd.allow_reuse_address = True
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
