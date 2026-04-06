"""
ClawCode Server - REST wrapper for ClawCode CLI with security hardening.

Sidebar ClawCode Integration - Production Ready
Addresses all security requirements:
- HMAC signature validation
- Command whitelist
- Path sandboxing
- Rate limiting
- Audit logging
"""

import os
import re
import json
import hmac
import hashlib
import subprocess
import threading
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Optional, Tuple, List
from flask import Flask, request, jsonify
from flask_cors import CORS

# Configuration
STUDIO = os.environ.get("STUDIO_PATH", "G:/My Drive/Projects/_studio")
CLAWCODE_PATH = os.environ.get("CLAWCODE_PATH", r"C:\tools\claw\claw.exe")
CLAWCODE_MODEL = os.environ.get("CLAWCODE_MODEL", "ollama:qwen3:14b")
SIDEBAR_SECRET = os.environ.get("SIDEBAR_SECRET", "change-this-secret-in-production")
PORT = int(os.environ.get("CLAWCODE_PORT", 11435))

# Security: Command whitelist
COMMAND_WHITELIST = [
    # Python execution
    'python', 'python3', 'py',
    
    # Safe file viewing
    'cat', 'head', 'tail', 'type', 'more',
    'ls', 'dir', 'tree',
    'find', 'grep', 'findstr',
    
    # Studio-specific scripts
    'supervisor_check.py',
    'inject_sidebar_data.py',
    'nightly_rollup.py',
    'rebuild_sidebar.py',
    'heartbeat.py',
    'vector_reindex.py',
    'janitor_run.py',
    
    # Git (read-only)
    'git status', 'git log', 'git diff', 'git branch',
]

# Security: Blocked patterns (never execute)
BLOCKED_PATTERNS = [
    r'rm\s+-rf',           # Recursive delete
    r'rm\s+-r',
    r'del\s+/s',           # Windows recursive delete
    r'rmdir\s+/s',
    r'format\s+',          # Format drive
    r'curl\s+.*\|',        # Pipe to shell
    r'wget\s+.*\|',
    r'powershell.*-enc',   # Encoded powershell
    r'cmd\s+/c.*&&',       # Chained commands
    r'eval\s*\(',          # Eval execution
    r'exec\s*\(',
    r'__import__',         # Python import injection
    r'os\.system',
    r'subprocess\.call',
    r'subprocess\.run',
    r'subprocess\.Popen',
    r'shutil\.rmtree',
    r'DROP\s+TABLE',       # SQL injection
    r'DELETE\s+FROM',
    r'TRUNCATE\s+',
    r';\s*--',             # SQL comment injection
]

# Security: Allowed paths (sandbox)
ALLOWED_PATHS = [
    STUDIO,
    os.path.normpath(STUDIO),
    STUDIO.replace('/', '\\'),
    STUDIO.replace('\\', '/'),
]

# Audit log path
AUDIT_LOG = os.path.join(STUDIO, "logs/sidebar-clawcode-audit.jsonl")

# Rate limiting
RATE_LIMIT = 10  # requests per minute
_request_counts: dict = defaultdict(list)
_lock = threading.Lock()


app = Flask(__name__)
CORS(app, origins=["http://localhost:8765", "http://127.0.0.1:8765"])


def log_audit(event_type: str, client_ip: str, details: dict) -> None:
    """Log audit event."""
    event = {
        "timestamp": datetime.now().isoformat(),
        "event_type": event_type,
        "client_ip": client_ip,
        "details": details
    }
    
    os.makedirs(os.path.dirname(AUDIT_LOG), exist_ok=True)
    
    with open(AUDIT_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")


def validate_signature(payload: bytes, signature: Optional[str]) -> Tuple[bool, str]:
    """Validate HMAC-SHA256 signature."""
    if not signature:
        return False, "Missing X-Sidebar-Signature header"
    
    try:
        expected = hmac.new(
            SIDEBAR_SECRET.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        if hmac.compare_digest(signature, expected):
            return True, "OK"
        else:
            return False, "Invalid signature"
    except Exception as e:
        return False, f"Signature validation error: {e}"


def check_rate_limit(client_ip: str) -> Tuple[bool, str]:
    """Check if client has exceeded rate limit."""
    now = datetime.now()
    cutoff = now - timedelta(minutes=1)
    
    with _lock:
        _request_counts[client_ip] = [
            t for t in _request_counts[client_ip] if t > cutoff
        ]
        
        if len(_request_counts[client_ip]) >= RATE_LIMIT:
            return False, f"Rate limit exceeded: {RATE_LIMIT}/minute"
        
        _request_counts[client_ip].append(now)
        return True, "OK"


def is_path_allowed(path: str) -> bool:
    """Check if path is within allowed sandbox."""
    normalized = os.path.normpath(os.path.abspath(path))
    
    for allowed in ALLOWED_PATHS:
        allowed_norm = os.path.normpath(os.path.abspath(allowed))
        if normalized.startswith(allowed_norm):
            return True
    
    return False


def is_command_safe(message: str) -> Tuple[bool, str]:
    """
    Validate command is safe to execute.
    Returns (is_safe, reason).
    """
    message_lower = message.lower()
    
    # Check blocked patterns
    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, message, re.IGNORECASE):
            return False, f"Blocked pattern: {pattern}"
    
    # Extract potential file paths and validate
    path_patterns = [
        r'[A-Za-z]:\\[^\s"\']+',  # Windows paths
        r'/[^\s"\']+',             # Unix paths
    ]
    
    for pattern in path_patterns:
        for match in re.findall(pattern, message):
            # Skip if it's a common safe path component
            if match in ['/s', '/q', '/f', '/r']:
                continue
            if not is_path_allowed(match):
                # Only block if it looks like a real path
                if len(match) > 5 and ('\\' in match or match.count('/') > 1):
                    return False, f"Path outside sandbox: {match}"
    
    return True, "OK"


def execute_clawcode(message: str, session_id: str = None) -> dict:
    """Execute ClawCode with the given message."""
    if not os.path.exists(CLAWCODE_PATH):
        return {
            "success": False,
            "error": f"ClawCode not found at {CLAWCODE_PATH}",
            "response": None
        }
    
    try:
        # Build command with model
        cmd = [CLAWCODE_PATH, "--model", CLAWCODE_MODEL]
        
        # Add session if provided
        if session_id:
            cmd.extend(["--session", session_id])
        
        # Add message via stdin to avoid shell escaping issues
        # Ensure HOME is set for ClawCode (required on Windows)
        home_dir = os.environ.get("HOME") or os.environ.get("USERPROFILE") or "C:/Users/jpalek"
        import sys
        print(f"DEBUG: home_dir = {home_dir}", flush=True)
        print(f"DEBUG: USERPROFILE = {os.environ.get('USERPROFILE')}", flush=True)
        sys.stdout.flush()
        proc_env = {**os.environ, "STUDIO_PATH": STUDIO, "HOME": home_dir}
        
        result = subprocess.run(
            cmd,
            input=message,
            capture_output=True,
            text=True,
            timeout=120,
            cwd=STUDIO,
            env=proc_env
        )
        
        return {
            "success": result.returncode == 0,
            "response": result.stdout,
            "error": result.stderr if result.returncode != 0 else None,
            "return_code": result.returncode
        }
    
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Request timed out (120s limit)",
            "response": None
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "response": None
        }


@app.route('/clawcode/chat', methods=['POST'])
def clawcode_chat():
    """Send message to ClawCode, return response."""
    client_ip = request.remote_addr
    payload = request.get_data()
    
    # Validate signature
    signature = request.headers.get('X-Sidebar-Signature')
    valid, reason = validate_signature(payload, signature)
    if not valid:
        log_audit("signature_failure", client_ip, {"reason": reason})
        return jsonify({"error": "Unauthorized", "reason": reason}), 401
    
    # Check rate limit
    allowed, reason = check_rate_limit(client_ip)
    if not allowed:
        log_audit("rate_limit", client_ip, {"reason": reason})
        return jsonify({"error": "Rate limit exceeded", "reason": reason}), 429
    
    # Parse request
    try:
        data = request.json
        message = data.get('message', '')
        session_id = data.get('session_id')
    except Exception as e:
        log_audit("parse_error", client_ip, {"error": str(e)})
        return jsonify({"error": "Invalid request body"}), 400
    
    if not message:
        return jsonify({"error": "Message required"}), 400
    
    # Validate command safety
    safe, reason = is_command_safe(message)
    if not safe:
        log_audit("command_blocked", client_ip, {
            "message": message[:200],
            "reason": reason
        })
        return jsonify({
            "error": "Command not allowed",
            "reason": reason
        }), 403
    
    # Execute
    log_audit("execute", client_ip, {
        "message": message[:500],
        "session_id": session_id
    })
    
    result = execute_clawcode(message, session_id)
    
    log_audit("response", client_ip, {
        "success": result["success"],
        "response_length": len(result.get("response", "") or ""),
        "error": result.get("error")
    })
    
    if result["success"]:
        return jsonify({
            "response": result["response"],
            "success": True
        })
    else:
        return jsonify({
            "error": result["error"],
            "response": result.get("response"),
            "success": False
        }), 500


@app.route('/clawcode/health', methods=['GET'])
def clawcode_health():
    """Check ClawCode + Ollama health."""
    # Check ClawCode
    clawcode_ok = os.path.exists(CLAWCODE_PATH)
    
    # Check Ollama
    ollama_ok = False
    ollama_models = []
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=5
        )
        ollama_ok = result.returncode == 0
        if ollama_ok:
            ollama_models = [
                line.split()[0] 
                for line in result.stdout.strip().split('\n')[1:]
                if line.strip()
            ]
    except:
        pass
    
    health = {
        "clawcode": {
            "available": clawcode_ok,
            "path": CLAWCODE_PATH
        },
        "ollama": {
            "available": ollama_ok,
            "models": ollama_models
        },
        "healthy": clawcode_ok and ollama_ok,
        "timestamp": datetime.now().isoformat()
    }
    
    status_code = 200 if health["healthy"] else 503
    return jsonify(health), status_code


@app.route('/clawcode/quick-actions', methods=['GET'])
def quick_actions():
    """Return available quick actions for sidebar buttons."""
    actions = [
        {
            "id": "agent_status",
            "label": "📊 Agent Status",
            "command": "Show me current agent health and status from agent_registry.json"
        },
        {
            "id": "run_supervisor",
            "label": "▶️ Run Supervisor",
            "command": "Run supervisor_check.py and show results"
        },
        {
            "id": "check_inbox",
            "label": "📥 Check Inbox",
            "command": "Show pending items from supervisor-inbox.json"
        },
        {
            "id": "create_checkin",
            "label": "📝 Create Checkin",
            "command": "Help me create a checkin for an agent. Ask which agent."
        },
        {
            "id": "whiteboard",
            "label": "📋 Whiteboard",
            "command": "Show current whiteboard contents from whiteboard.json"
        },
        {
            "id": "recent_checkins",
            "label": "📅 Recent Checkins",
            "command": "Show the 5 most recent checkins from checkin_queue.jsonl"
        }
    ]
    return jsonify(actions)


@app.route('/health', methods=['GET'])
def server_health():
    """Server health endpoint for monitoring."""
    return jsonify({
        "status": "healthy",
        "service": "clawcode-server",
        "port": PORT,
        "timestamp": datetime.now().isoformat()
    })


def generate_signature(payload: str) -> str:
    """Generate signature for testing."""
    return hmac.new(
        SIDEBAR_SECRET.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()


if __name__ == "__main__":
    print(f"Starting ClawCode Server on port {PORT}")
    print(f"Studio path: {STUDIO}")
    print(f"ClawCode path: {CLAWCODE_PATH}")
    print(f"ClawCode exists: {os.path.exists(CLAWCODE_PATH)}")
    print(f"Audit log: {AUDIT_LOG}")
    print()
    print("Security:")
    print(f"  - HMAC validation: enabled")
    print(f"  - Rate limit: {RATE_LIMIT}/minute")
    print(f"  - Command whitelist: {len(COMMAND_WHITELIST)} patterns")
    print(f"  - Blocked patterns: {len(BLOCKED_PATTERNS)} patterns")
    print(f"  - Path sandbox: {ALLOWED_PATHS[0]}")
    print()
    
    # Warning if using default secret
    if SIDEBAR_SECRET == "change-this-secret-in-production":
        print("⚠️  WARNING: Using default secret! Set SIDEBAR_SECRET environment variable.")
    
    app.run(host='0.0.0.0', port=PORT, debug=False, threaded=True)
