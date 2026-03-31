import http.server, os

PORT = 8765
DIR = "G:/My Drive/Projects/_studio"

class NoCacheHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=DIR, **kw)
    def end_headers(self):
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()
    def log_message(self, fmt, *args): pass

os.chdir(DIR)
server = http.server.HTTPServer(("localhost", PORT), NoCacheHandler)
print("Sidebar server: http://localhost:" + str(PORT) + "/sidebar.html")
server.serve_forever()
