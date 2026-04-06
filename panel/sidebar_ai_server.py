"""
Sidebar AI Server - Cloud-first with local fallback, integrated with Option C inbox system.

Architecture:
  Sidebar HTML â†’ This Server (:11435) â†’ Groq/OpenRouter/Ollama â†’ Response
                                      â†“
                              studio_bridge.py (:11435 /inbox-log)
                                      â†“
                              supervisor-inbox.json

Provider Priority:
  1. Garage Ollama (when GPU available)
  2. Groq (free tier, ~100+ tok/s, 500 req/day)
  3. OpenRouter (free tier, ~30-50 tok/s)
  4. Local Ollama (slow fallback)

Security:
  - HMAC-SHA256 signature validation
  - Rate limiting (10 req/min)
  - Audit logging to sidebar-ai-audit.jsonl
  - Path sandboxing to _studio only

Location: G:/My Drive/Projects/_studio/panel/sidebar_ai_server.py
Execute: python panel/sidebar_ai_server.py
"""

# EXPECTED_RUNTIME_SECONDS: 86400  # Long-running server

import os
import re
import json
import hmac
import hashlib
import requests
import threading
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Optional, Tuple, Dict, Any
from flask import Flask, request, jsonify
from flask_cors import CORS

# =============================================================================
# CONFIGURATION - Loads from .studio-vault.json
# =============================================================================

STUDIO = os.environ.get("STUDIO_PATH", "G:/My Drive/Projects/_studio")
VAULT_PATH = os.path.join(STUDIO, ".studio-vault.json")

def load_vault():
    """Load credentials from .studio-vault.json"""
    if os.path.exists(VAULT_PATH):
        try:
            with open(VAULT_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[WARNING] Failed to load vault: {e}")
    return {}

_vault = load_vault()

# Helper to get from env first, then vault
def get_credential(env_key: str, vault_key: str, default: str = "") -> str:
    """Get credential from env var first, then vault file."""
    return os.environ.get(env_key) or _vault.get(vault_key, default)

# Security
SIDEBAR_SECRET = get_credential("SIDEBAR_SECRET", "sidebar_secret", "ebf01941bf149ad43fa607c8d571868eba9826b298297eacbbc9d58c7cc4e643")
PORT = int(os.environ.get("SIDEBAR_PORT", 11435))

# Provider API Keys - loaded from vault
GROQ_API_KEY = get_credential("GROQ_API_KEY", "Groq API Key", "")
OPENROUTER_API_KEY = get_credential("OPENROUTER_API_KEY", "openrouter_api_key", "")

# Garage Ollama (set when GPU arrives)
GARAGE_OLLAMA_URL = os.environ.get("GARAGE_OLLAMA_URL", "")  # e.g., "http://192.168.1.X:11434"
LOCAL_OLLAMA_URL = get_credential("LOCAL_OLLAMA_URL", "ollama_url", "http://localhost:11434")

# Model preferences
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")  # Free tier
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "google/gemma-7b-it:free")
OLLAMA_MODEL = get_credential("OLLAMA_MODEL", "ollama_model", "gemma3:4b")

# Rate limiting
RATE_LIMIT_PER_MIN = 10
_rate_limit_data = defaultdict(list)
_lock = threading.Lock()

# Audit log
AUDIT_LOG = os.path.join(STUDIO, "logs", "sidebar-ai-audit.jsonl")
os.makedirs(os.path.dirname(AUDIT_LOG), exist_ok=True)

# System prompt for sidebar assistant
SYSTEM_PROMPT = """You are the Studio Sidebar Assistant for Joe's autonomous AI studio.

Your capabilities:
- Answer questions about the studio, agents, and workflows
- Help with operational queries (agent status, checkins, inbox items)
- Provide guidance on eBay listing, data analysis, and studio tasks

Context:
- Studio location: G:/My Drive/Projects/_studio
- 16+ agents running via Windows Task Scheduler
- Supabase backend, ChromaDB RAG, Flask sidebar
- Key files: agent_registry.json, supervisor-inbox.json, checkin_queue.jsonl

Be concise and operational. If you don't know something, say so.
"""

# =============================================================================
# FLASK APP
# =============================================================================

app = Flask(__name__)

@app.after_request
def add_cors_headers(response):
    """Manual CORS headers for all responses."""
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, X-Sidebar-Signature'
    return response

@app.route('/', methods=['OPTIONS'])
@app.route('/<path:path>', methods=['OPTIONS'])
def handle_options(path=None):
    return '', 204

# =============================================================================
# SECURITY
# =============================================================================

def validate_hmac(signature: str, payload: bytes) -> Tuple[bool, str]:
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
        # Clean old entries
        _rate_limit_data[client_ip] = [
            ts for ts in _rate_limit_data[client_ip] if ts > cutoff
        ]
        
        if len(_rate_limit_data[client_ip]) >= RATE_LIMIT_PER_MIN:
            return False, f"Rate limit exceeded ({RATE_LIMIT_PER_MIN}/min)"
        
        _rate_limit_data[client_ip].append(now)
        return True, "OK"


def audit_log(event: str, data: Dict[str, Any], success: bool = True):
    """Append to audit log."""
    try:
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event": event,
            "success": success,
            "data": data
        }
        with open(AUDIT_LOG, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry) + '\n')
    except Exception as e:
        print(f"[AUDIT ERROR] {e}")

# =============================================================================
# AI PROVIDERS
# =============================================================================

def call_groq(message: str, conversation_history: list = None) -> Tuple[bool, str, str]:
    """Call Groq API (free tier: llama-3.1-8b-instant)."""
    if not GROQ_API_KEY:
        return False, "", "GROQ_API_KEY not set"
    
    try:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        if conversation_history:
            messages.extend(conversation_history)
        messages.append({"role": "user", "content": message})
        
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": GROQ_MODEL,
                "messages": messages,
                "max_tokens": 1024,
                "temperature": 0.7
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return True, content, "groq"
        else:
            return False, "", f"Groq error {response.status_code}: {response.text[:200]}"
    
    except requests.Timeout:
        return False, "", "Groq timeout"
    except Exception as e:
        return False, "", f"Groq exception: {e}"


def call_openrouter(message: str, conversation_history: list = None) -> Tuple[bool, str, str]:
    """Call OpenRouter API (free tier models)."""
    if not OPENROUTER_API_KEY:
        return False, "", "OPENROUTER_API_KEY not set"
    
    try:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        if conversation_history:
            messages.extend(conversation_history)
        messages.append({"role": "user", "content": message})
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:11435",
                "X-Title": "Studio Sidebar"
            },
            json={
                "model": OPENROUTER_MODEL,
                "messages": messages,
                "max_tokens": 1024
            },
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return True, content, "openrouter"
        else:
            return False, "", f"OpenRouter error {response.status_code}: {response.text[:200]}"
    
    except requests.Timeout:
        return False, "", "OpenRouter timeout"
    except Exception as e:
        return False, "", f"OpenRouter exception: {e}"


def call_ollama(message: str, conversation_history: list = None, use_garage: bool = False) -> Tuple[bool, str, str]:
    """Call Ollama API (local or garage)."""
    
    # Choose endpoint
    if use_garage and GARAGE_OLLAMA_URL:
        base_url = GARAGE_OLLAMA_URL
        provider_name = "ollama-garage"
    else:
        base_url = LOCAL_OLLAMA_URL
        provider_name = "ollama-local"
    
    try:
        # Build prompt with history
        full_prompt = f"{SYSTEM_PROMPT}\n\n"
        if conversation_history:
            for msg in conversation_history:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                full_prompt += f"{role.upper()}: {content}\n"
        full_prompt += f"USER: {message}\nASSISTANT:"
        
        response = requests.post(
            f"{base_url}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "num_predict": 1024,
                    "temperature": 0.7
                }
            },
            timeout=120  # Longer timeout for CPU inference
        )
        
        if response.status_code == 200:
            data = response.json()
            content = data.get("response", "")
            return True, content, provider_name
        else:
            return False, "", f"Ollama error {response.status_code}: {response.text[:200]}"
    
    except requests.Timeout:
        return False, "", f"{provider_name} timeout"
    except requests.ConnectionError:
        return False, "", f"{provider_name} connection failed"
    except Exception as e:
        return False, "", f"{provider_name} exception: {e}"


def get_ai_response(message: str, conversation_history: list = None) -> Tuple[str, str, list]:
    """
    Get AI response using provider fallback chain.
    Returns: (response_text, provider_used, errors_list)
    """
    errors = []
    
    # Priority 1: Garage Ollama (if GPU available)
    if GARAGE_OLLAMA_URL:
        success, response, provider = call_ollama(message, conversation_history, use_garage=True)
        if success:
            return response, provider, errors
        errors.append(f"garage: {provider}")
    
    # Priority 2: Groq (fastest free tier)
    success, response, provider = call_groq(message, conversation_history)
    if success:
        return response, provider, errors
    errors.append(f"groq: {provider}")
    
    # Priority 3: OpenRouter (free tier fallback)
    success, response, provider = call_openrouter(message, conversation_history)
    if success:
        return response, provider, errors
    errors.append(f"openrouter: {provider}")
    
    # Priority 4: Local Ollama (slow but works)
    success, response, provider = call_ollama(message, conversation_history, use_garage=False)
    if success:
        return response, provider, errors
    errors.append(f"local: {provider}")
    
    return "", "none", errors

# =============================================================================
# API ENDPOINTS
# =============================================================================

@app.route('/health', methods=['GET'])
def health():
    """Basic health check."""
    return jsonify({
        "healthy": True,
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0"
    })


@app.route('/clawcode/health', methods=['GET'])
def clawcode_health():
    """
    Health endpoint with provider status.
    Named 'clawcode' for backward compatibility with sidebar JS.
    """
    # Check providers
    providers = {}
    
    # Groq
    providers["groq"] = {
        "available": bool(GROQ_API_KEY),
        "model": GROQ_MODEL if GROQ_API_KEY else None,
        "key_preview": f"{GROQ_API_KEY[:8]}..." if GROQ_API_KEY else None
    }
    
    # OpenRouter
    providers["openrouter"] = {
        "available": bool(OPENROUTER_API_KEY),
        "model": OPENROUTER_MODEL if OPENROUTER_API_KEY else None,
        "key_preview": f"{OPENROUTER_API_KEY[:8]}..." if OPENROUTER_API_KEY else None
    }
    
    # Garage Ollama
    if GARAGE_OLLAMA_URL:
        try:
            r = requests.get(f"{GARAGE_OLLAMA_URL}/api/tags", timeout=5)
            garage_models = [m["name"] for m in r.json().get("models", [])] if r.ok else []
            providers["ollama_garage"] = {
                "available": r.ok,
                "url": GARAGE_OLLAMA_URL,
                "models": garage_models
            }
        except:
            providers["ollama_garage"] = {"available": False, "url": GARAGE_OLLAMA_URL}
    
    # Local Ollama
    try:
        r = requests.get(f"{LOCAL_OLLAMA_URL}/api/tags", timeout=5)
        local_models = [m["name"] for m in r.json().get("models", [])] if r.ok else []
        providers["ollama_local"] = {
            "available": r.ok,
            "url": LOCAL_OLLAMA_URL,
            "models": local_models
        }
    except:
        providers["ollama_local"] = {"available": False, "url": LOCAL_OLLAMA_URL}
    
    # Determine primary provider
    if GARAGE_OLLAMA_URL:
        primary = "ollama-garage"
    elif GROQ_API_KEY:
        primary = "groq"
    elif OPENROUTER_API_KEY:
        primary = "openrouter"
    else:
        primary = "ollama-local"
    
    return jsonify({
        "healthy": True,
        "timestamp": datetime.now().isoformat(),
        "providers": providers,
        "primary": primary,
        "vault_loaded": bool(_vault)
    })


@app.route('/clawcode/quick-actions', methods=['GET'])
def quick_actions():
    """Quick action buttons for sidebar."""
    actions = [
        {
            "id": "agent_status",
            "label": "ðŸ“Š Agent Status",
            "command": "Show me current agent health and status from agent_registry.json"
        },
        {
            "id": "check_inbox",
            "label": "ðŸ“¥ Check Inbox",
            "command": "Show pending items from supervisor-inbox.json"
        },
        {
            "id": "recent_checkins",
            "label": "ðŸ“‹ Recent Checkins",
            "command": "Show the 5 most recent checkins from checkin_queue.jsonl"
        },
        {
            "id": "whiteboard",
            "label": "ðŸ“ Whiteboard",
            "command": "Show current whiteboard contents from whiteboard.json"
        },
        {
            "id": "run_supervisor",
            "label": "ðŸ”„ Run Supervisor",
            "command": "What would supervisor_check.py do if run right now?"
        },
        {
            "id": "system_health",
            "label": "ðŸ’š System Health",
            "command": "Check overall studio system health: Ollama status, recent errors, agent activity"
        }
    ]
    return jsonify(actions)


@app.route('/clawcode/chat', methods=['POST'])
def chat():
    """
    Main chat endpoint with HMAC validation.
    Named 'clawcode' for backward compatibility with sidebar JS.
    """
    client_ip = request.remote_addr
    
    # Validate HMAC
    signature = request.headers.get('X-Sidebar-Signature', '')
    payload = request.get_data()
    
    valid, msg = validate_hmac(signature, payload)
    if not valid:
        audit_log("chat_rejected", {"reason": msg, "ip": client_ip}, success=False)
        return jsonify({"success": False, "error": msg}), 401
    
    # Rate limit
    allowed, msg = check_rate_limit(client_ip)
    if not allowed:
        audit_log("rate_limited", {"ip": client_ip}, success=False)
        return jsonify({"success": False, "error": msg}), 429
    
    # Parse request
    try:
        data = request.json
        message = data.get("message", "").strip()
        conversation_history = data.get("history", [])
        
        if not message:
            return jsonify({"success": False, "error": "Empty message"}), 400
        
    except Exception as e:
        return jsonify({"success": False, "error": f"Invalid JSON: {e}"}), 400
    
    # Get AI response
    start_time = datetime.now()
    response_text, provider, errors = get_ai_response(message, conversation_history)
    elapsed = (datetime.now() - start_time).total_seconds()
    
    if not response_text:
        audit_log("chat_failed", {
            "message": message[:100],
            "errors": errors,
            "ip": client_ip
        }, success=False)
        return jsonify({
            "success": False,
            "error": "All providers failed",
            "details": errors
        }), 503
    
    # Success
    audit_log("chat_success", {
        "message": message[:100],
        "provider": provider,
        "elapsed_s": elapsed,
        "response_len": len(response_text),
        "ip": client_ip
    })
    
    return jsonify({
        "success": True,
        "response": response_text,
        "provider": provider,
        "elapsed_s": round(elapsed, 2)
    })


@app.route('/clawcode/inbox-submit', methods=['POST'])
def inbox_submit():
    """
    Submit an item to the supervisor inbox.
    Integrates with studio_bridge.py flow.
    """
    client_ip = request.remote_addr
    
    # Validate HMAC
    signature = request.headers.get('X-Sidebar-Signature', '')
    payload = request.get_data()
    
    valid, msg = validate_hmac(signature, payload)
    if not valid:
        audit_log("inbox_rejected", {"reason": msg, "ip": client_ip}, success=False)
        return jsonify({"success": False, "error": msg}), 401
    
    try:
        data = request.json
        item_id = data.get("id", f"sidebar-{datetime.now().timestamp()}")
        title = data.get("title", "Sidebar Submission")
        finding = data.get("finding", data.get("content", ""))
        urgency = data.get("urgency", "INFO")
        project = data.get("project", "studio")
        
        # Load supervisor inbox
        inbox_path = os.path.join(STUDIO, "supervisor-inbox.json")
        
        if os.path.exists(inbox_path):
            with open(inbox_path, 'r', encoding='utf-8') as f:
                inbox_data = json.load(f)
        else:
            inbox_data = {"items": []}
        
        # Handle both formats (list or dict with items)
        if isinstance(inbox_data, list):
            items = inbox_data
        else:
            items = inbox_data.get("items", [])
        
        # Add new item
        new_item = {
            "id": item_id,
            "source": "sidebar-ai",
            "type": "human_request",
            "urgency": urgency,
            "title": title,
            "finding": finding,
            "status": "PENDING",
            "date": datetime.now().isoformat(),
            "project": project
        }
        items.append(new_item)
        
        # Save
        if isinstance(inbox_data, list):
            inbox_data = items
        else:
            inbox_data["items"] = items
        
        with open(inbox_path, 'w', encoding='utf-8') as f:
            json.dump(inbox_data, f, indent=2)
        
        # Also log to inbox-log.jsonl for sidebar reconciliation
        inbox_log_path = os.path.join(STUDIO, "inbox-log.jsonl")
        log_entry = {
            "id": item_id,
            "answer": finding,
            "timestamp": datetime.now().isoformat(),
            "question": title,
            "source": "sidebar-ai",
            "urgency": urgency,
            "project": project,
            "type": "submission"
        }
        with open(inbox_log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry) + '\n')
        
        audit_log("inbox_submit", {
            "item_id": item_id,
            "title": title[:50],
            "urgency": urgency,
            "ip": client_ip
        })
        
        return jsonify({
            "success": True,
            "item_id": item_id,
            "message": "Added to supervisor inbox"
        })
    
    except Exception as e:
        audit_log("inbox_error", {"error": str(e), "ip": client_ip}, success=False)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/clawcode/inbox-status', methods=['GET'])
def inbox_status():
    """Get current inbox status summary."""
    try:
        inbox_path = os.path.join(STUDIO, "supervisor-inbox.json")
        
        if not os.path.exists(inbox_path):
            return jsonify({"pending": 0, "items": []})
        
        with open(inbox_path, 'r', encoding='utf-8') as f:
            inbox_data = json.load(f)
        
        if isinstance(inbox_data, list):
            items = inbox_data
        else:
            items = inbox_data.get("items", [])
        
        # Filter pending
        pending = [i for i in items if i.get("status") in ["PENDING", "pending", "new"]]
        
        return jsonify({
            "total": len(items),
            "pending": len(pending),
            "items": pending[-10:]  # Last 10 pending
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =============================================================================
# LEGACY COMPATIBILITY ROUTES
# These match the endpoints sidebar-agent.html expects from the old studio_bridge
# =============================================================================

@app.route('/ping', methods=['GET'])
def legacy_ping():
    """Legacy ping for sidebar compatibility."""
    return jsonify({"status": "ok", "server": "sidebar-ai-v2"})


@app.route('/chat', methods=['POST'])
def legacy_chat():
    """Legacy chat endpoint - no HMAC for local requests."""
    client_ip = request.remote_addr
    if client_ip not in ['127.0.0.1', '::1', 'localhost']:
        return jsonify({"success": False, "error": "Legacy endpoint only available locally"}), 403
    
    data = request.json or {}
    message = data.get('message') or data.get('prompt', '')
    
    if not message:
        return jsonify({"success": False, "error": "No message provided"}), 400
    
    import time as _time
    _start = _time.time()
    response, provider, errors = get_ai_response(message)
    elapsed = _time.time() - _start
    
    audit_log("chat_success" if response else "chat_fail", {
        "message": message[:100],
        "provider": provider,
        "elapsed_s": round(elapsed, 3) if elapsed else None,
        "response_len": len(response) if response else 0,
        "ip": client_ip,
        "legacy": True
    }, success=bool(response))
    
    return jsonify({
        "success": True,
        "response": response or "(no response)",
        "provider": provider,
        "elapsed_s": round(elapsed, 3) if elapsed else None
    })


@app.route('/inbox', methods=['GET'])
def legacy_inbox():
    """Legacy inbox endpoint for sidebar."""
    try:
        inbox_path = os.path.join(STUDIO, "supervisor-inbox.json")
        if not os.path.exists(inbox_path):
            return jsonify([])
        with open(inbox_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, list):
            return jsonify(data)
        return jsonify(data.get("items", []))
    except:
        return jsonify([])


@app.route('/inbox-log', methods=['GET', 'POST'])
def legacy_inbox_log():
    """Legacy inbox log for sidebar reconciliation."""
    inbox_log_path = os.path.join(STUDIO, "inbox-log.jsonl")
    
    if request.method == 'GET':
        try:
            if not os.path.exists(inbox_log_path):
                return jsonify([])
            entries = []
            with open(inbox_log_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        entries.append(json.loads(line))
                    except:
                        pass
            return jsonify(entries)
        except:
            return jsonify([])
    else:
        try:
            data = request.json or {}
            with open(inbox_log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(data) + '\n')
            return jsonify({"success": True})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500


@app.route('/answer', methods=['POST'])
def legacy_answer():
    """Legacy answer submission."""
    client_ip = request.remote_addr
    if client_ip not in ['127.0.0.1', '::1', 'localhost']:
        return jsonify({"success": False, "error": "Legacy endpoint only available locally"}), 403
    
    data = request.json or {}
    item_id = data.get('id') or data.get('item_id', f"answer-{int(datetime.now().timestamp())}")
    answer = data.get('answer', '')
    
    inbox_log_path = os.path.join(STUDIO, "inbox-log.jsonl")
    log_entry = {
        "id": item_id,
        "answer": answer,
        "timestamp": datetime.now().isoformat(),
        "source": "sidebar-legacy",
        "type": "answer"
    }
    try:
        with open(inbox_log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry) + '\n')
        return jsonify({"success": True, "logged": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/whiteboard', methods=['GET'])
def legacy_whiteboard():
    """Legacy whiteboard endpoint."""
    try:
        wb_path = os.path.join(STUDIO, "whiteboard.json")
        if not os.path.exists(wb_path):
            return jsonify({"items": []})
        with open(wb_path, 'r', encoding='utf-8') as f:
            return jsonify(json.load(f))
    except:
        return jsonify({"items": []})


@app.route('/supervisor-inbox-log', methods=['GET'])
def legacy_supervisor_log():
    """Alias for inbox-log."""
    return legacy_inbox_log()


@app.route('/restart', methods=['POST'])
def restart_server():
    """Restart the server (for sidebar button)."""
    client_ip = request.remote_addr
    if client_ip not in ['127.0.0.1', '::1', 'localhost']:
        return jsonify({"success": False, "error": "Only available locally"}), 403
    
    import subprocess
    try:
        subprocess.Popen(['schtasks', '/Run', '/TN', 'Studio\\SidebarAIServer'], 
                        creationflags=subprocess.CREATE_NO_WINDOW)
        def delayed_exit():
            import time
            time.sleep(1)
            os._exit(0)
        import threading
        threading.Thread(target=delayed_exit, daemon=True).start()
        return jsonify({"success": True, "message": "Restarting..."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# =============================================================================
# MAIN
# =============================================================================

if __name__ == '__main__':
    # Print startup banner (ASCII-safe for Windows console)
    groq_status = f"[OK] Loaded from vault ({GROQ_API_KEY[:12]}...)" if GROQ_API_KEY else "[X] Not found"
    openrouter_status = f"[OK] Loaded from vault ({OPENROUTER_API_KEY[:12]}...)" if OPENROUTER_API_KEY else "[X] Not found"
    garage_status = f"[OK] {GARAGE_OLLAMA_URL}" if GARAGE_OLLAMA_URL else "[X] Not configured (set GARAGE_OLLAMA_URL)"
    vault_status = "[OK] Loaded" if _vault else "[X] Not found"
    
    print(f"""
+--------------------------------------------------------------------------+
|  Sidebar AI Server v2.0 - Cloud-first with Inbox Integration             |
+--------------------------------------------------------------------------+
|  Port: {PORT}
|  Studio: {STUDIO}
|  Vault: {vault_status}
|
|  Provider Priority (fallback chain):
|    1. Garage Ollama: {garage_status}
|    2. Groq:          {groq_status}
|    3. OpenRouter:    {openrouter_status}
|    4. Local Ollama:  {LOCAL_OLLAMA_URL}
|
|  Security:
|    - HMAC: Enabled
|    - Rate limit: {RATE_LIMIT_PER_MIN}/min
|    - Audit log: {AUDIT_LOG}
|
|  Endpoints:
|    GET  /health              - Basic health
|    GET  /clawcode/health     - Provider status
|    GET  /clawcode/quick-actions - Quick action buttons
|    POST /clawcode/chat       - Chat (HMAC required)
|    POST /clawcode/inbox-submit - Submit to inbox (HMAC)
|    GET  /clawcode/inbox-status - Inbox summary
+--------------------------------------------------------------------------+
""")
    
    app.run(host='0.0.0.0', port=PORT, debug=False, threaded=True)


