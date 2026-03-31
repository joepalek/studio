"""
Studio Sidebar Local Server
Serves _studio files at http://localhost:8765 with CORS headers.
Run via serve-sidebar.bat
"""
import http.server, socketserver, os, sys

PORT = 8765
STUDIO = r"G:\My Drive\Projects\_studio"

class CORSHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
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
