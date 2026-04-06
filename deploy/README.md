# Option C Panel Architecture v3.0 + ClawCode Integration

## Deployment Package

This package contains production-ready implementations for:

1. **Option C v3.0** — Agent communication and quality assurance system (96.6% panel confidence)
2. **ClawCode Integration** — Sidebar chat replacement with local qwen3:14b

---

## Quick Start

```powershell
# 1. Copy to studio
Copy-Item -Recurse studio_deploy "G:\My Drive\Projects\_studio\deploy"

# 2. Run pre-flight checks
cd "G:\My Drive\Projects\_studio\deploy"
python deploy.py --check

# 3. Deploy Day 1 (Security)
python deploy.py --day 1

# 4. Deploy ClawCode server
python deploy.py --clawcode
```

---

## File Structure

```
studio_deploy/
├── deploy.py                    # Deployment script
├── README.md                    # This file
│
├── utilities/
│   └── secret_encryption.py     # DPAPI encryption for agent secrets
│
├── panel/
│   ├── security_events.py       # Security event logging + rate limiting
│   ├── tamper_proof_log.py      # Hash-chained audit logs
│   ├── circuit_breaker.py       # Circuit breaker for external services
│   ├── clawcode_server.py       # ClawCode REST wrapper (Flask)
│   └── clawcode_chat.js         # Sidebar chat UI module
│
├── schemas/
│   └── retention_policy.json    # Data retention policy
│
└── tests/
    └── test_clawcode_integration.py
```

---

## System 1: Option C v3.0

### Day 1: Security Hardening

**Components:**
- `utilities/secret_encryption.py` — DPAPI encryption for agent secrets
- `panel/security_events.py` — Failed auth logging + rate limiting (5/10min)
- `panel/tamper_proof_log.py` — Hash-chained tamper-proof logs

**Deploy:**
```powershell
pip install pywin32
python deploy.py --day 1
```

**Verify:**
```powershell
python utilities/secret_encryption.py health agent_registry.json
```

### Day 2: Resilience Patterns

**Components:**
- `panel/circuit_breaker.py` — Circuit breaker for external services

**Deploy:**
```powershell
python deploy.py --day 2
```

**Verify:**
```powershell
python panel/circuit_breaker.py status
```

### Day 3: Data Governance

**Components:**
- `schemas/retention_policy.json` — Retention policy (7yr/2yr/90d/30d tiers)

**Deploy:**
```powershell
python deploy.py --day 3
```

---

## System 2: ClawCode Integration

### Prerequisites

1. **ClawCode installed** at `C:\tools\claw\claw.exe`
2. **Ollama running** with qwen3:14b model
3. **Flask installed**: `pip install flask flask-cors`

### Deploy

```powershell
python deploy.py --clawcode
```

### Configure

1. Set environment variables:
```powershell
$env:SIDEBAR_SECRET = "your-secure-secret-here"
$env:STUDIO_PATH = "G:\My Drive\Projects\_studio"
$env:CLAWCODE_PATH = "C:\tools\claw\claw.exe"
```

2. Start server:
```powershell
python panel/clawcode_server.py
```

3. Server runs on `http://localhost:11435`

### Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/clawcode/chat` | POST | Send message (requires signature) |
| `/clawcode/health` | GET | Check ClawCode + Ollama health |
| `/clawcode/quick-actions` | GET | Get quick action buttons |
| `/health` | GET | Server health |

### Security Features

- **HMAC-SHA256 signing** — All chat requests must include `X-Sidebar-Signature` header
- **Command whitelist** — Only safe commands allowed
- **Path sandboxing** — File ops restricted to studio directory
- **Rate limiting** — 10 requests/minute per client
- **Audit logging** — All commands logged to `logs/sidebar-clawcode-audit.jsonl`

### Sidebar Integration

Add to your sidebar HTML:
```html
<script src="panel/clawcode_chat.js"></script>
<script>
    ClawCodeChat.configure({
        serverUrl: 'http://localhost:11435',
        secret: 'your-secret-here'
    });
    ClawCodeChat.createChatUI('chat-container');
</script>
```

---

## iPhone/Mobile Access

### Option A: Cloudflare Tunnel (Recommended)

```bash
# Install cloudflared
winget install cloudflare.cloudflared

# Create tunnel
cloudflared tunnel create studio-sidebar
cloudflared tunnel route dns studio-sidebar studio.yourdomain.com

# Configure ~/.cloudflared/config.yml
tunnel: studio-sidebar
credentials-file: ~/.cloudflared/studio-sidebar.json
ingress:
  - hostname: studio.yourdomain.com
    service: http://localhost:11435
  - service: http_status:404

# Run
cloudflared tunnel run studio-sidebar
```

### Option B: ngrok (Simpler)

```bash
ngrok http 11435 --authtoken YOUR_TOKEN
```

---

## Testing

```powershell
# Run unit tests
python deploy.py --test

# Run with integration tests (requires running server)
$env:RUN_INTEGRATION_TESTS = "1"
python deploy.py --test
```

---

## Troubleshooting

### DPAPI not available

```
[WARN] win32crypt not available
```

**Fix:** Install pywin32:
```powershell
pip install pywin32
```

### ClawCode not found

```
ClawCode not found at C:\tools\claw\claw.exe
```

**Fix:** Set `CLAWCODE_PATH` environment variable to correct path.

### Ollama connection failed

```
Circuit ollama is open
```

**Fix:** 
1. Check Ollama is running: `ollama list`
2. Pull model: `ollama pull qwen3:14b`
3. Reset circuit: `python panel/circuit_breaker.py reset ollama`

### Signature validation failed

```
401 Unauthorized: Invalid signature
```

**Fix:** Ensure `SIDEBAR_SECRET` matches between server and client.

---

## Panel Confidence Summary

| Component | Confidence | Status |
|-----------|------------|--------|
| Option C v3.0 Architecture | **96.6%** | ✅ Production Ready |
| Sidebar ClawCode Integration | 86.3% → 95%+ | ✅ Hardened |

---

## Contact

- Studio: `G:\My Drive\Projects\_studio`
- Email: joedealsonline@gmail.com
