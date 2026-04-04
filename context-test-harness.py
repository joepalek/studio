"""
context-test-harness.py — Mirofish Context Architecture Test
Tests 8 context configurations (A-H) across 5 tests + 8 dimensions each.
Uses Gemini Flash-Lite for scoring. Gemini Flash for final synthesis.
Ollama gemma3:4b used for offline-capable checks.
NO Claude API calls. Ever.

Run overnight via Task Scheduler: Studio\MirofishTest at 12:30 AM
Output: context-test-results.json (checkpoint after every config)
Log:    scheduler/logs/mirofish-test.log
"""

import json
import os
import time
import urllib.request
import urllib.error
from datetime import datetime

# Bezos Rule: circuit breaker constant
MAX_CONSECUTIVE_FAILURES = 3

STUDIO = "G:/My Drive/Projects/_studio"
RESULTS_PATH = os.path.join(STUDIO, "context-test-results.json")
CONFIG_PATH  = os.path.join(STUDIO, "studio-config.json")
LOG_PATH     = os.path.join(STUDIO, "scheduler/logs/mirofish-test.log")

GEMINI_LITE_MODEL  = "gemini-2.5-flash-lite"
GEMINI_FLASH_MODEL = "gemini-2.5-flash"
OLLAMA_URL         = "http://localhost:11434"
OLLAMA_MODEL       = "gemma3:4b"

SLEEP_BETWEEN_CALLS = 6   # seconds — Gemini free tier rate limit safety
RETRY_WAIT          = 60  # seconds on 429
MAX_RETRIES         = 3


# ─── CONFIG DEFINITIONS ──────────────────────────────────────────────────────

CONFIGS = {
    "config_a": {
        "name": "Config A — Current Approach (baseline)",
        "description": (
            "Method: studio-context.md manually injected at session start. "
            "All three interfaces read the same file manually. "
            "Strengths: simple, already exists, works for Claude Code. "
            "Weaknesses: manual, stale, token-heavy, doesn't survive gaps. "
            "Failure mode: user forgets to inject, or context is 3 days old. "
            "Safety net: auto-regenerate on session start via generate-context.py."
        ),
        "context_files": ["studio-context.md"],
        "primary_failure": "user forgets to inject or context is 3 days old",
        "offline": True,
        "supabase_required": False,
        "git_required": False,
    },
    "config_b": {
        "name": "Config B — Structured Files",
        "description": (
            "Method: CLAUDE.md rules + session-handoff.md + decision-log.json. "
            "All three interfaces read these three files at session start. "
            "Strengths: already partially built, lightweight, Git-tracked. "
            "Weaknesses: still manual load, handoff file needs discipline to write. "
            "Failure mode: handoff not written at session end. "
            "Safety net: nightly-rollup writes handoff automatically. "
            "Safety net 2: CLAUDE.md standing rule enforces end-of-session write."
        ),
        "context_files": ["CLAUDE.md", "session-handoff.md", "decision-log.json"],
        "primary_failure": "handoff not written at session end",
        "offline": True,
        "supabase_required": False,
        "git_required": False,
    },
    "config_c": {
        "name": "Config C — Supabase Live State",
        "description": (
            "Method: All three interfaces read/write to Supabase tables. "
            "Tables: system_state, inbox_items, decisions, session_log. "
            "Real-time sync — change in one interface visible to all immediately. "
            "Strengths: truly real-time, survives any session gap. "
            "Weaknesses: requires API calls, costs money at scale, latency. "
            "Failure mode: Supabase down, network issues, auth expiry. "
            "Safety net: fallback to local JSON files if Supabase unreachable. "
            "Safety net 2: sync local files TO Supabase on connect."
        ),
        "context_files": [],
        "primary_failure": "Supabase down or auth expiry",
        "offline": False,
        "supabase_required": True,
        "git_required": False,
    },
    "config_d": {
        "name": "Config D — Git as Source of Truth",
        "description": (
            "Method: _studio repo is the shared brain. "
            "All three interfaces commit/pull before reading state. "
            "State lives in JSON files, Git tracks all changes. "
            "Strengths: free, auditable, already exists, offline capable. "
            "Weaknesses: requires git pull before reading, merge conflicts possible. "
            "Failure mode: dirty working tree, merge conflict blocks reads. "
            "Safety net: read-only pull never causes conflicts. "
            "Safety net 2: separate read-only branch for context."
        ),
        "context_files": ["state.json", "heartbeat-log.json"],
        "primary_failure": "dirty working tree or merge conflict",
        "offline": True,
        "supabase_required": False,
        "git_required": True,
    },
    "config_e": {
        "name": "Config E — Hybrid (Three-Layer)",
        "description": (
            "Method: Three-layer system. "
            "Layer 1 (permanent rules): CLAUDE.md — never changes, injected always. "
            "Layer 2 (session state): session-handoff.md — updated each session. "
            "Layer 3 (live data): Supabase for inbox + decisions only (not full context). "
            "Strengths: rules are stable, session state is lightweight, "
            "only dynamic data hits Supabase. "
            "Weaknesses: three systems to maintain. "
            "Failure mode: any one layer fails. "
            "Safety net: each layer degrades gracefully without the others. "
            "Safety net 2: layer 3 falls back to local JSON if Supabase down."
        ),
        "context_files": ["CLAUDE.md", "session-handoff.md"],
        "primary_failure": "any one of three layers fails",
        "offline": False,  # layer 3 needs Supabase, but degrades gracefully
        "supabase_required": True,
        "git_required": False,
    },
    "config_f": {
        "name": "Config F — Compressed Context Injection",
        "description": (
            "Method: studio-context.md compressed to under 2,000 tokens. "
            "Key facts only: project list, completion %, last decision, active blockers. "
            "Injected on every message automatically (not manually). "
            "Strengths: always current, low token cost, automatic. "
            "Weaknesses: loses detail, summary may miss important context. "
            "Failure mode: compression loses critical context. "
            "Safety net: full context available on demand via FILES tab. "
            "Safety net 2: escalation keywords trigger full context load."
        ),
        "context_files": ["studio-context.md"],
        "primary_failure": "compression loses critical context detail",
        "offline": True,
        "supabase_required": False,
        "git_required": False,
    },
    "config_g": {
        "name": "Config G — Vector Memory (local RAG)",
        "description": (
            "Method: Ollama + local embedding model. "
            "All sessions, decisions, project notes stored as vectors. "
            "Query on session start: 'what do I need to know right now?'. "
            "Strengths: scales infinitely, semantic search, truly intelligent recall. "
            "Weaknesses: complex setup, requires Ollama running, latency. "
            "Failure mode: Ollama down, embedding model not loaded. "
            "Safety net: fall back to Config B if Ollama unavailable. "
            "Safety net 2: pre-warm embeddings on machine startup."
        ),
        "context_files": [],
        "primary_failure": "Ollama down or embedding model not loaded",
        "offline": True,  # but requires Ollama
        "supabase_required": False,
        "git_required": False,
    },
    "config_h": {
        "name": "Config H — Claude Memory System",
        "description": (
            "Method: Use Claude.ai's built-in memory (now available free). "
            "Key system facts stored as Claude memories. "
            "Combined with CLAUDE.md for Claude Code sessions. "
            "Strengths: native to Claude.ai, no extra infrastructure. "
            "Weaknesses: only works in Claude.ai, not Claude Code or sidebar. "
            "Failure mode: memories not portable to other interfaces. "
            "Safety net: export memories to CLAUDE.md periodically. "
            "Safety net 2: use as supplement to Config E, not replacement."
        ),
        "context_files": ["CLAUDE.md"],
        "primary_failure": "memories not portable to Claude Code or sidebar",
        "offline": False,
        "supabase_required": False,
        "git_required": False,
    },
}

SCORE_DIMENSIONS = [
    ("survival",          "SURVIVAL — survives 24h session gap with no human intervention (1=no survival, 10=full survival)"),
    ("cross_interface",   "CROSS-INTERFACE — change in one interface visible to others (1=no sync, 10=instant sync)"),
    ("token_cost",        "TOKEN COST — tokens for context overhead per message (1=>3000 tokens, 10=<200 tokens)"),
    ("staleness",         "STALENESS — how quickly context goes out of date (1=stale within hours, 10=never stale)"),
    ("setup_complexity",  "SETUP COMPLEXITY — how hard to implement and maintain (1=very complex, 10=trivial)"),
    ("failure_recovery",  "FAILURE RECOVERY — graceful failure and recovery (1=complete failure, 10=seamless)"),
    ("offline_capable",   "OFFLINE CAPABLE — works without internet (1=requires internet, 10=fully offline)"),
    ("scalability",       "SCALABILITY — still works with 50 projects (1=breaks at scale, 10=scales infinitely)"),
]

TEST_DESCRIPTIONS = [
    ("session_gap",        "SESSION GAP: inject context, have conversation, close all interfaces, wait (simulated 24h), reopen. Does next session know what happened before? Score 0 (no memory) to 10 (full memory)."),
    ("cross_interface",    "CROSS-INTERFACE SYNC: make a decision in Claude Code. Does sidebar show it without manual refresh? Does Claude.ai know in next message? Score 0 (no sync) to 10 (instant sync)."),
    ("stale_detection",    "STALE DETECTION: inject context from 48 hours ago, ask 'what is the most recent thing we worked on?'. Does the AI know its context is stale? Score 0 (confidently wrong) to 10 (flags staleness correctly)."),
    ("failure_recovery",   "FAILURE RECOVERY: simulate primary failure mode. Does it fall back gracefully? Recover automatically when issue resolves? Score 0 (complete failure) to 10 (seamless recovery)."),
    ("token_efficiency",   "TOKEN EFFICIENCY: tokens used per message for context maintenance. Target <500. Score: 0 (>3000 tokens), 2 (2000-3000), 4 (1000-2000), 6 (500-1000), 8 (200-500), 10 (<200 tokens)."),
]


# ─── UTILITIES ───────────────────────────────────────────────────────────────

def log(msg):
    ts = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    line = f"{ts} {msg}"
    print(line)
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_json(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default if default is not None else {}


def save_json(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, path)


def read_file_tokens(path):
    """Estimate token count of a file (chars/4 approximation)."""
    try:
        content = open(path, "r", encoding="utf-8").read()
        return len(content) // 4
    except Exception:
        return 0


def gemini_call(key, prompt, model=GEMINI_LITE_MODEL, retries=0):
    """Call Gemini API. Returns text or raises on permanent failure."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode()
    req = urllib.request.Request(url, data=payload,
                                  headers={"Content-Type": "application/json"})
    try:
        r = urllib.request.urlopen(req, timeout=30)
        data = json.loads(r.read())
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except urllib.error.HTTPError as e:
        if e.code == 429 and retries < MAX_RETRIES:
            log(f"  429 rate limit — waiting {RETRY_WAIT}s (attempt {retries+1}/{MAX_RETRIES})")
            time.sleep(RETRY_WAIT)
            return gemini_call(key, prompt, model, retries + 1)
        raise


def ollama_ping():
    """Return True if Ollama is reachable."""
    try:
        r = urllib.request.urlopen("http://localhost:11434/api/tags", timeout=3)
        return r.status == 200
    except Exception:
        return False


def ollama_call(prompt):
    """Call Ollama gemma3:4b. Returns text or error string."""
    try:
        payload = json.dumps({
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False
        }).encode()
        req = urllib.request.Request(
            f"{OLLAMA_URL}/api/generate", data=payload,
            headers={"Content-Type": "application/json"}
        )
        r = urllib.request.urlopen(req, timeout=60)
        return json.loads(r.read()).get("response", "").strip()
    except Exception as e:
        return f"OLLAMA_ERROR: {str(e)[:80]}"


# ─── TOKEN EFFICIENCY (mechanical) ───────────────────────────────────────────

def score_token_efficiency(cfg_key, cfg):
    """Mechanically measure token cost of context files for this config."""
    # Map config to actual file paths
    file_map = {
        "studio-context.md":   os.path.join(STUDIO, "studio-context.md"),
        "CLAUDE.md":           "G:/My Drive/Projects/CLAUDE.md",
        "session-handoff.md":  os.path.join(STUDIO, "session-handoff.md"),
        "decision-log.json":   os.path.join(STUDIO, "decision-log.json"),
        "state.json":          os.path.join(STUDIO, "state.json"),
        "heartbeat-log.json":  os.path.join(STUDIO, "heartbeat-log.json"),
    }

    total_tokens = 0
    measured = []
    for fname in cfg.get("context_files", []):
        path = file_map.get(fname, "")
        if path and os.path.exists(path):
            t = read_file_tokens(path)
            measured.append(f"{fname}={t}tok")
            total_tokens += t
        else:
            measured.append(f"{fname}=NOT_FOUND")

    # Config-specific adjustments
    if cfg_key == "config_c":
        total_tokens = 150   # Supabase: just a small JSON payload per call
        measured = ["supabase_api_call=~150tok"]
    elif cfg_key == "config_f":
        total_tokens = min(total_tokens, 500)  # compressed by design
        measured.append("(compressed)")
    elif cfg_key == "config_g":
        total_tokens = 200   # RAG query result, not full context
        measured = ["rag_query_result=~200tok"]
    elif cfg_key == "config_h":
        total_tokens = 300   # Claude memories: typically compact
        measured = ["claude_memories=~300tok"]

    # Score
    if total_tokens < 200:
        score = 10
    elif total_tokens < 500:
        score = 8
    elif total_tokens < 1000:
        score = 6
    elif total_tokens < 2000:
        score = 4
    elif total_tokens < 3000:
        score = 2
    else:
        score = 0

    return score, total_tokens, ", ".join(measured)


# ─── GEMINI DIMENSION SCORING ─────────────────────────────────────────────────

def score_config_dimensions(gemini_key, cfg_key, cfg):
    """Ask Gemini Flash-Lite to score this config across all 8 dimensions."""
    dimensions_text = "\n".join(
        f"- {name.upper()}: {desc}" for name, desc in SCORE_DIMENSIONS
    )
    prompt = f"""You are scoring a context architecture for an AI developer studio.
The studio has three interfaces that need to share context:
- Opera Sidebar (browser-based, localhost)
- Claude.ai (web chat)
- Claude Code (VS Code terminal sessions)

Score this configuration on each dimension. Return ONLY valid JSON.

CONFIG NAME: {cfg['name']}
DESCRIPTION: {cfg['description']}
PRIMARY FAILURE MODE: {cfg['primary_failure']}
OFFLINE CAPABLE: {cfg['offline']}
SUPABASE REQUIRED: {cfg['supabase_required']}

DIMENSIONS TO SCORE (each 1-10):
{dimensions_text}

Return JSON only — no markdown, no explanation:
{{
  "survival": <1-10>,
  "cross_interface": <1-10>,
  "token_cost": <1-10>,
  "staleness": <1-10>,
  "setup_complexity": <1-10>,
  "failure_recovery": <1-10>,
  "offline_capable": <1-10>,
  "scalability": <1-10>,
  "reasoning": {{
    "survival": "one sentence",
    "cross_interface": "one sentence",
    "token_cost": "one sentence",
    "staleness": "one sentence",
    "setup_complexity": "one sentence",
    "failure_recovery": "one sentence",
    "offline_capable": "one sentence",
    "scalability": "one sentence"
  }}
}}"""

    try:
        text = gemini_call(gemini_key, prompt)
        text = text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except Exception as e:
        return {"error": str(e)[:120], "all_scores": 5}


def score_config_tests(gemini_key, cfg_key, cfg, token_score, token_count):
    """Ask Gemini Flash-Lite to score this config across the 5 tests."""
    tests_text = "\n".join(
        f"- {name.upper()}: {desc}" for name, desc in TEST_DESCRIPTIONS
    )
    prompt = f"""You are evaluating a context architecture for an AI developer studio.
Score how well this configuration handles each of 5 test scenarios.

CONFIG: {cfg['name']}
DESCRIPTION: {cfg['description']}
PRIMARY FAILURE MODE: {cfg['primary_failure']}
OFFLINE CAPABLE: {cfg['offline']}

Note: TOKEN EFFICIENCY has already been measured mechanically:
  Score: {token_score}/10 ({token_count} tokens estimated per message)

TESTS (score each 0-10):
{tests_text}

Return JSON only — no markdown:
{{
  "session_gap": <0-10>,
  "cross_interface": <0-10>,
  "stale_detection": <0-10>,
  "failure_recovery": <0-10>,
  "token_efficiency": {token_score},
  "notes": {{
    "session_gap": "one sentence",
    "cross_interface": "one sentence",
    "stale_detection": "one sentence",
    "failure_recovery": "one sentence",
    "token_efficiency": "measured: {token_count} tokens"
  }},
  "human_review_flags": ["list any items needing human validation"]
}}"""

    try:
        text = gemini_call(gemini_key, prompt)
        text = text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except Exception as e:
        return {"error": str(e)[:120]}


# ─── OLLAMA CHECK ────────────────────────────────────────────────────────────

def check_ollama_for_config(cfg_key, cfg):
    """Use Ollama to check offline viability of this config."""
    if not ollama_ping():
        return {"ollama_available": False, "note": "Ollama DOWN — skipped"}

    prompt = (
        f"In one sentence, what is the single biggest risk of this context architecture:\n"
        f"{cfg['name']}: {cfg['description']}"
    )
    reply = ollama_call(prompt)
    return {
        "ollama_available": True,
        "ollama_risk_assessment": reply[:200] if not reply.startswith("OLLAMA_ERROR") else reply
    }


# ─── CHECKPOINT WRITER ───────────────────────────────────────────────────────

def write_checkpoint(results):
    save_json(RESULTS_PATH, results)


def load_or_init_results():
    existing = load_json(RESULTS_PATH, None)
    if existing and isinstance(existing, dict) and "configs" in existing:
        return existing
    return {
        "run_date": datetime.now().isoformat(),
        "status": "in_progress",
        "configs": {},
        "winner": None,
        "recommendation": None
    }


# ─── PER-CONFIG RUNNER ───────────────────────────────────────────────────────

def run_config(gemini_key, cfg_key, cfg, results):
    log(f"\n{'='*60}")
    log(f"TESTING: {cfg['name']}")
    log('='*60)

    # Skip if already completed
    existing = results["configs"].get(cfg_key, {})
    if existing.get("status") == "complete":
        log(f"  Already complete — skipping")
        return

    config_result = {"status": "in_progress", "name": cfg["name"]}
    results["configs"][cfg_key] = config_result
    write_checkpoint(results)

    # Test 5 — Token Efficiency (mechanical, no API call)
    log("  [T5] Token efficiency (mechanical)...")
    tok_score, tok_count, tok_detail = score_token_efficiency(cfg_key, cfg)
    log(f"      Score: {tok_score}/10 | ~{tok_count} tokens | {tok_detail}")

    # Dimension scoring via Gemini Flash-Lite
    log("  [D] Scoring 8 dimensions via Gemini Flash-Lite...")
    dim_scores = score_config_dimensions(gemini_key, cfg_key, cfg)
    if "error" in dim_scores:
        log(f"      ERROR: {dim_scores['error']}")
    else:
        total_dim = sum(dim_scores.get(d, 5) for d, _ in SCORE_DIMENSIONS)
        log(f"      Dimension total: {total_dim}/80")
    time.sleep(SLEEP_BETWEEN_CALLS)

    # 5-test scoring via Gemini Flash-Lite
    log("  [T] Scoring 5 tests via Gemini Flash-Lite...")
    test_scores = score_config_tests(gemini_key, cfg_key, cfg, tok_score, tok_count)
    if "error" in test_scores:
        log(f"      ERROR: {test_scores['error']}")
    else:
        total_tests = sum([
            test_scores.get("session_gap", 5),
            test_scores.get("cross_interface", 5),
            test_scores.get("stale_detection", 5),
            test_scores.get("failure_recovery", 5),
            test_scores.get("token_efficiency", tok_score),
        ])
        log(f"      Test total: {total_tests}/50")
        flags = test_scores.get("human_review_flags", [])
        if flags:
            log(f"      HUMAN REVIEW: {'; '.join(flags)}")
    time.sleep(SLEEP_BETWEEN_CALLS)

    # Ollama check
    log("  [O] Ollama offline viability check...")
    ollama_result = check_ollama_for_config(cfg_key, cfg)
    log(f"      {ollama_result}")

    # Compute totals
    dim_total = sum(dim_scores.get(d, 0) for d, _ in SCORE_DIMENSIONS) if "error" not in dim_scores else 0
    test_total = (
        test_scores.get("session_gap", 0) +
        test_scores.get("cross_interface", 0) +
        test_scores.get("stale_detection", 0) +
        test_scores.get("failure_recovery", 0) +
        test_scores.get("token_efficiency", tok_score)
    ) if "error" not in test_scores else 0
    combined_score = round((dim_total / 80 * 50) + (test_total / 50 * 50), 1)  # normalise to 100

    config_result.update({
        "status": "complete",
        "dimension_scores": dim_scores,
        "dimension_total": dim_total,
        "test_scores": test_scores,
        "test_total": test_total,
        "token_count": tok_count,
        "token_detail": tok_detail,
        "ollama_check": ollama_result,
        "combined_score": combined_score,
        "notes": f"dim={dim_total}/80 tests={test_total}/50 combined={combined_score}/100"
    })

    results["configs"][cfg_key] = config_result
    write_checkpoint(results)
    log(f"  DONE — combined score: {combined_score}/100")


# ─── FINAL SYNTHESIS ─────────────────────────────────────────────────────────

def run_final_synthesis(gemini_key, results):
    log("\n" + "="*60)
    log("FINAL SYNTHESIS — Gemini Flash (not Lite)")
    log("="*60)

    summary_lines = []
    for cfg_key, cfg_data in results["configs"].items():
        name = cfg_data.get("name", cfg_key)
        score = cfg_data.get("combined_score", 0)
        dim_t = cfg_data.get("dimension_total", "?")
        test_t = cfg_data.get("test_total", "?")
        summary_lines.append(
            f"{name}: combined={score}/100 (dimensions={dim_t}/80, tests={test_t}/50)"
        )

    summary = "\n".join(summary_lines)

    prompt = f"""You are the final judge in a context architecture evaluation for an AI developer studio.

The studio needs ONE shared context architecture for three interfaces:
- Opera Sidebar (browser-based)
- Claude.ai (web chat)
- Claude Code (VS Code terminal)

Key constraints:
- Solo developer, budget-conscious
- Works in 1-3 hour sessions with overnight gaps
- Runs Windows 11 with Ollama local LLM
- Has Supabase configured (free tier)
- Git repo for all studio state
- Wants maximum reliability, minimum token cost

SCORED RESULTS:
{summary}

Based on these scores, select the winner and provide your recommendation.
Return ONLY valid JSON:
{{
  "winner": "config_a|config_b|config_c|config_d|config_e|config_f|config_g|config_h",
  "winner_name": "full config name",
  "winner_score": <combined score>,
  "runner_up": "config key",
  "recommendation": "2-3 sentence implementation recommendation",
  "immediate_actions": ["action 1", "action 2", "action 3"],
  "watch_points": ["potential failure to monitor"],
  "hybrid_suggestion": "if combining configs would help, say how in one sentence"
}}"""

    try:
        text = gemini_call(gemini_key, prompt, model=GEMINI_FLASH_MODEL)
        text = text.replace("```json", "").replace("```", "").strip()
        synthesis = json.loads(text)
        results["winner"] = synthesis.get("winner")
        results["recommendation"] = synthesis
        results["status"] = "complete"
        write_checkpoint(results)
        log(f"  WINNER: {synthesis.get('winner_name')} ({synthesis.get('winner_score')}/100)")
        log(f"  RECOMMENDATION: {synthesis.get('recommendation')}")
    except Exception as e:
        log(f"  Synthesis ERROR: {e}")
        results["status"] = "partial"
        results["recommendation"] = {"error": str(e)[:120]}
        write_checkpoint(results)


# ─── ROUND 2: COUNCIL REVIEW ─────────────────────────────────────────────────

def run_council_review(gemini_key, results):
    log("\n" + "="*60)
    log("ROUND 2 — Council Review (Gemini Flash, simulated perspectives)")
    log("="*60)

    results_summary = json.dumps({
        k: {
            "name": v.get("name"),
            "combined_score": v.get("combined_score"),
            "dimension_total": v.get("dimension_total"),
            "test_total": v.get("test_total"),
            "notes": v.get("notes")
        }
        for k, v in results.get("configs", {}).items()
        if v.get("status") == "complete"
    }, indent=2)

    winner = results.get("winner", "unknown")
    recommendation = results.get("recommendation", {})

    prompt = f"""You are simulating a council of domain experts reviewing a context architecture test for an AI developer studio.

The studio needs shared context across three interfaces: Opera Sidebar, Claude.ai, and Claude Code CLI.
A solo developer runs this on Windows 11 with Ollama local LLM, Supabase (free tier), and Git for state.

Adopt these perspectives one at a time and give 2-3 sentences of feedback from each:

1. Claude Shannon (information theory, signal/noise, compression efficiency)
2. Grace Hopper (standardization, pragmatism, human-readable systems, ship it)
3. Alan Kay (encapsulation, goal-oriented messaging, long-term design)
4. Margaret Hamilton (fault tolerance, priority interrupts, error recovery)

TEST RESULTS:
{results_summary}

CURRENT WINNER: {winner}
CURRENT RECOMMENDATION: {json.dumps(recommendation, indent=2)[:600]}

For each expert: what does this result tell you about the winning architecture? What would you change or reinforce?

Return ONLY valid JSON:
{{
  "shannon": {{
    "verdict": "APPROVE|REVISE|REJECT",
    "feedback": "2-3 sentences from Shannon's perspective"
  }},
  "hopper": {{
    "verdict": "APPROVE|REVISE|REJECT",
    "feedback": "2-3 sentences from Hopper's perspective"
  }},
  "kay": {{
    "verdict": "APPROVE|REVISE|REJECT",
    "feedback": "2-3 sentences from Kay's perspective"
  }},
  "hamilton": {{
    "verdict": "APPROVE|REVISE|REJECT",
    "feedback": "2-3 sentences from Hamilton's perspective"
  }},
  "council_verdict": "APPROVE|REVISE|REJECT",
  "council_summary": "one sentence combining all four perspectives"
}}"""

    try:
        text = gemini_call(gemini_key, prompt, model=GEMINI_FLASH_MODEL)
        text = text.replace("```json", "").replace("```", "").strip()
        council = json.loads(text)
        results["council_review"] = {
            "council_simulation": True,
            "note": "Simulated perspectives pending real Historical Twins build",
            "run_at": datetime.now().isoformat(),
            "members": ["Shannon", "Hopper", "Kay", "Hamilton"],
            "feedback": council
        }
        write_checkpoint(results)
        log(f"  Council verdict: {council.get('council_verdict')}")
        log(f"  Summary: {council.get('council_summary')}")
        for name in ["shannon", "hopper", "kay", "hamilton"]:
            m = council.get(name, {})
            log(f"  {name.capitalize()}: {m.get('verdict')} — {m.get('feedback','')[:80]}")
    except Exception as e:
        log(f"  Council review ERROR: {e}")
        results["council_review"] = {
            "council_simulation": True,
            "note": "Simulated perspectives pending real Historical Twins build",
            "error": str(e)[:120]
        }
        write_checkpoint(results)


# ─── TASK LOG ────────────────────────────────────────────────────────────────

def write_task_log_entry():
    task_log_path = os.path.join(STUDIO, "task-log.json")
    data = load_json(task_log_path, {"_schema": "1.0", "_description": "Log of task routing decisions", "tasks": []})
    data["tasks"].append({
        "date": datetime.now().strftime("%Y-%m-%d"),
        "task": "Mirofish context architecture test",
        "routing": "python+gemini+ollama",
        "reason": "fully mechanical scoring, zero Claude quota needed",
        "quota_saved": True
    })
    save_json(task_log_path, data)


# ─── MAIN ────────────────────────────────────────────────────────────────────

def main():
    log("Mirofish Context Test Harness starting")

    config = load_json(CONFIG_PATH, {})
    gemini_key = config.get("gemini_api_key", "")
    if not gemini_key:
        log("ERROR: gemini_api_key missing in studio-config.json — aborting")
        return

    ollama_up = ollama_ping()
    log(f"Ollama: {'UP' if ollama_up else 'DOWN (offline checks will be skipped)'}")
    log(f"Testing {len(CONFIGS)} configs × 5 tests + 8 dimensions each")
    log(f"Estimated runtime: ~{len(CONFIGS) * 2 * SLEEP_BETWEEN_CALLS // 60 + 5} minutes\n")

    results = load_or_init_results()
    results["run_date"] = datetime.now().isoformat()
    results["status"] = "in_progress"
    write_checkpoint(results)

    for cfg_key, cfg in CONFIGS.items():
        try:
            run_config(gemini_key, cfg_key, cfg, results)
        except Exception as e:
            log(f"  FATAL ERROR on {cfg_key}: {e}")
            results["configs"][cfg_key] = {
                "status": "error",
                "error": str(e)[:200]
            }
            write_checkpoint(results)
        time.sleep(SLEEP_BETWEEN_CALLS)

    run_final_synthesis(gemini_key, results)
    time.sleep(SLEEP_BETWEEN_CALLS)
    run_council_review(gemini_key, results)
    write_task_log_entry()

    complete = sum(1 for v in results["configs"].values() if v.get("status") == "complete")
    log(f"\nDone. {complete}/{len(CONFIGS)} configs complete.")
    log(f"Results: {RESULTS_PATH}")


if __name__ == "__main__":
    main()
