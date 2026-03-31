"""
studio_bridge.py — Local HTTP bridge for sidebar chat
Port 11435. Endpoints: GET /ping  GET /context  POST /chat
"""
import http.server, json, subprocess, sys, os, urllib.request

PORT = 11435
STUDIO = "G:/My Drive/Projects/_studio"
OLLAMA = "http://localhost:11434"

def get_context(query=None, budget=2000):
    """Get studio context with larger budget for targeted queries."""
    try:
        sys.path.insert(0, STUDIO)
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "cvs", STUDIO + "/context-vector-store.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        import chromadb
        client = chromadb.PersistentClient(path=STUDIO + "/vector-memory")
        collection = client.get_or_create_collection(
            name="studio_context",
            metadata={"hnsw:space": "cosine"}
        )

        q = query or "current state active projects recent decisions priorities"
        results = collection.query(query_texts=[q], n_results=10)

        chunks = results["documents"][0] if results["documents"] else []
        sources = [m.get("source","?") for m in (results["metadatas"][0] if results["metadatas"] else [])]

        output_lines = []
        used = 0
        for chunk, source in zip(chunks, sources):
            entry = f"[{source}]\n{chunk}"
            if used + len(entry) > budget:
                break
            output_lines.append(entry)
            used += len(entry)

        return "\n\n".join(output_lines) if output_lines else "[no relevant context found]"

    except Exception as e:
        try:
            result = subprocess.run(
                [sys.executable, STUDIO + "/session-startup.py"],
                capture_output=True, text=True, timeout=10, cwd=STUDIO)
            return result.stdout.strip()
        except Exception as e2:
            return "[context unavailable: " + str(e2)[:80] + "]"

def ollama_generate(model, prompt):
    data = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode()
    req = urllib.request.Request(OLLAMA + "/api/generate", data=data,
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read()).get("response", "")

class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *args): pass

    def cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200); self.cors(); self.end_headers()

    def do_GET(self):
        if self.path.startswith("/context"):
            ctx = get_context()
            body = json.dumps({"context": ctx}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.cors(); self.end_headers()
            self.wfile.write(body)
        elif self.path == "/ping":
            self.send_response(200); self.cors()
            self.end_headers(); self.wfile.write(b"ok")
        else:
            self.send_response(404); self.end_headers()

    def do_POST(self):
        if self.path == "/chat":
            length = int(self.headers.get("Content-Length", 0))
            payload = json.loads(self.rfile.read(length))
            model   = payload.get("model", "gemma3:4b")
            message = payload.get("message", "")
            ctx     = get_context(message, budget=2500)
            prompt = (
                "You are the Studio AI for Joe Palek's autonomous AI studio.\n"
                "Answer ONLY from the context below. Be concise and direct.\n"
                "If the context does not contain the answer, say so clearly.\n\n"
                "STUDIO CONTEXT:\n" + ctx + "\n\n"
                "User: " + message + "\nAssistant:"
            )
            try:
                response = ollama_generate(model, prompt)
                body = json.dumps({"response": response, "ctx_len": len(ctx)}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.cors(); self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                err = json.dumps({"error": str(e)}).encode()
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.cors(); self.end_headers()
                self.wfile.write(err)
        else:
            self.send_response(404); self.end_headers()

if __name__ == "__main__":
    server = http.server.HTTPServer(("localhost", PORT), Handler)
    print("Studio bridge on http://localhost:" + str(PORT))
    server.serve_forever()
