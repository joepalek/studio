"""
vector_reindex.py
Rebuilds ChromaDB vector store from studio files.
Calls session-startup.py which runs the full reindex.
Zero LLM cost — pure ChromaDB/Ollama.
"""

# EXPECTED_RUNTIME_SECONDS: 300
import sys, os, subprocess
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
STUDIO = "G:/My Drive/Projects/_studio"

def log(msg):
    ts = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    print(ts + " " + msg)

log("VectorReindex starting")

# Run session-startup.py which handles the full reindex pipeline
result = subprocess.run(
    [sys.executable, STUDIO + "/session-startup.py"],
    capture_output=True, text=True,
    encoding='utf-8', errors='replace',
    cwd=STUDIO, timeout=300
)

if result.stdout: 
    for line in result.stdout.strip().split('\n'):
        log(line)
if result.stderr:
    for line in result.stderr.strip().split('\n')[:5]:
        log("STDERR: " + line)

log("VectorReindex complete — exit code " + str(result.returncode))

# Write heartbeat
import json

import sys as _sys
_sys.path.insert(0, "G:/My Drive/Projects/_studio/utilities")
from constraint_gates import hamilton_watchdog
hb_path = STUDIO + "/heartbeat-log.json"
try:
    hb = json.load(open(hb_path, encoding='utf-8')) if os.path.exists(hb_path) else {"entries": []}
    if not isinstance(hb, dict): hb = {"entries": []}
    hb["entries"].append({
        "date": datetime.now().isoformat(),
        "agent": "vector-reindex",
        "status": "clean" if result.returncode == 0 else "error",
        "notes": "reindex complete" if result.returncode == 0 else "exit " + str(result.returncode)
    })
    hb["entries"] = hb["entries"][-200:]
    import tempfile
    tmp = hb_path + ".tmp"
    json.dump(hb, open(tmp, "w", encoding="utf-8"), indent=2)
    os.replace(tmp, hb_path)
except Exception as e:
    log("Heartbeat write failed: " + str(e)[:60])
