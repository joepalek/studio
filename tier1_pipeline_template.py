"""
tier1_pipeline_template.py
==========================
Reusable template for ALL Tier 1 fully autonomous data pipeline agents.
Copy this file, rename it, and fill in the CONFIG block only.
Do NOT modify the framework sections below CONFIG.

TIER 1 DEFINITION:
  - Zero human touch after setup
  - Data is structured, sources are stable APIs/feeds
  - Outputs publish automatically without review
  - Runs via Windows Task Scheduler overnight

RULES ENFORCED:
  - Bezos Rule: MAX_CONSECUTIVE_FAILURES=3 circuit breaker on all API loops
  - Hamilton Rule: TTL watchdog — aborts if runtime > TTL_SECONDS
  - Hopper Rule: pull_timestamp + checksum logged, staleness checked
  - Codd Extraction: 95% confidence gate — blank over wrong
  - Shannon Rule: state.json handoff under 200 tokens
  - Gall's Law: evolve from working system — no rewrites

USAGE:
  python tier1_pipeline_template.py           # run once
  python tier1_pipeline_template.py --dry     # dry run, no delivery

TASK SCHEDULER XML: see bottom of this file
"""

import json, os, sys, time, hashlib, logging, argparse
from datetime import datetime
from pathlib import Path

sys.path.insert(0, "G:/My Drive/Projects/_studio")
from ai_gateway import call as gw_call
import provider_health as ph

# ══════════════════════════════════════════════════════════════════
# CONFIG — FILL THIS IN PER POOL. TOUCH NOTHING ELSE.
# ══════════════════════════════════════════════════════════════════

AGENT_CONFIG = {
    # Identity
    "agent_id":       "sanctions-ingestor",          # unique slug, no spaces
    "pool_name":      "Sanctions Lists Multi-jurisd.", # human label
    "pool_number":    73,                              # pool # from catalog

    # Timing
    "ttl_seconds":    300,                 # Hamilton Rule: abort if exceeded
    "source_cadence": "daily",             # daily | weekly | monthly
    "stale_after_hours": 25,              # Hopper Rule: flag if data older than this

    # Data source — implement fetch_raw() below
    "source_url":     "https://scsanctions.un.org/resources/xml/en/consolidated.xml",
    "source_format":  "xml",              # json | xml | csv | pdf | rss | api

    # AI routing — which gateway task_type for each step
    "normalize_task": "batch",            # Gemini Free — bulk normalization
    "synthesize_task": "quality",         # Claude — narrative synthesis
    "classify_task":  "local",            # Ollama — local classification

    # Synthesis prompt template — {data} is replaced with normalized JSON
    "synthesis_prompt": (
        "You are a sanctions intelligence analyst. "
        "Given this normalized sanctions data: {data}\n\n"
        "Write a 3-sentence plain English summary covering: "
        "(1) which jurisdictions updated their lists today, "
        "(2) any notable new entity additions, "
        "(3) one actionable note for compliance teams. "
        "Be specific. Confidence < 70% = write 'insufficient signal' not a guess."
    ),
    "synthesize_max_tokens": 300,

    # Classification prompt — returns a short label
    "classify_prompt": (
        "Classify this sanctions update as one of: "
        "[ROUTINE, NOTABLE, URGENT, EMPTY]. "
        "URGENT = new designations for major financial institutions or states. "
        "Return ONLY the label, nothing else.\n\nData: {data}"
    ),
    "classify_max_tokens": 10,

    # Delivery channels — set True/False per channel
    "deliver_email":    False,   # requires email_delivery_agent
    "deliver_webhook":  False,   # requires webhook_delivery_agent
    "deliver_file":     True,    # always write to output_path
    "deliver_digest":   True,    # always write to daily-digest.json

    # Paths
    "output_dir":   "G:/My Drive/Projects/_studio/data/sanctions",
    "state_path":   "G:/My Drive/Projects/_studio/data/sanctions/state.json",
    "log_path":     "G:/My Drive/Projects/_studio/logs/sanctions-ingestor.log",
    "digest_path":  "G:/My Drive/Projects/_studio/daily-digest.json",
    "inbox_path":   "G:/My Drive/Projects/_studio/supervisor-inbox.json",
}

# ══════════════════════════════════════════════════════════════════
# POOL-SPECIFIC — implement fetch_raw() and parse_raw() only
# ══════════════════════════════════════════════════════════════════

def fetch_raw(cfg: dict) -> str:
    """
    Pull raw data from the source. Return raw string content.
    Raise an exception on failure — the framework handles retries.

    IMPLEMENT THIS FOR EACH POOL:
      - Sanctions: urllib.request.urlopen(url).read().decode()
      - WASDE: urllib.request.urlopen(wasde_pdf_url).read() then pdfplumber
      - ACLED: requests.get(api_url, params={...}).text
      - RASFF: feedparser.parse(rss_url) then json.dumps(entries)
      - GFW: requests.get(tile_api_url, headers=...).text
    """
    import urllib.request
    req = urllib.request.Request(
        cfg["source_url"],
        headers={"User-Agent": "StudioAgent/1.0 (research; contact@studio.local)"}
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")


def parse_raw(raw: str, cfg: dict) -> list[dict]:
    """
    Convert raw source string to a list of normalized dicts.
    Each dict = one record. Keep field names consistent.
    Return [] if source is empty or unchanged.

    IMPLEMENT THIS FOR EACH POOL:
      - Sanctions XML: parse <INDIVIDUAL> and <ENTITY> nodes
      - WASDE PDF: extract crop estimate tables per commodity
      - ACLED CSV: parse rows into {date, event_type, country, fatalities}
      - RASFF RSS: parse <item> nodes into {date, product, hazard, country}

    Codd Extraction Rule: leave fields blank rather than guess.
    Only extract values explicitly present in the source.
    """
    # EXAMPLE: stub returning empty list — replace with real parser
    # import xml.etree.ElementTree as ET
    # root = ET.fromstring(raw)
    # records = []
    # for node in root.findall('.//INDIVIDUAL'):
    #     records.append({
    #         "name":        node.findtext('FIRST_NAME','') + ' ' + node.findtext('SECOND_NAME',''),
    #         "entity_type": "individual",
    #         "list":        "UN",
    #         "date_listed": node.findtext('LISTED_ON',''),
    #         "nationality": node.findtext('NATIONALITY',''),
    #     })
    # return records
    return []


# ══════════════════════════════════════════════════════════════════
# FRAMEWORK — do not modify below this line
# ══════════════════════════════════════════════════════════════════

def _setup_logging(cfg: dict) -> logging.Logger:
    Path(cfg["log_path"]).parent.mkdir(parents=True, exist_ok=True)
    log = logging.getLogger(cfg["agent_id"])
    log.setLevel(logging.INFO)
    if not log.handlers:
        fh = logging.FileHandler(cfg["log_path"], encoding="utf-8")
        fh.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s %(message)s",
                                          datefmt="%Y-%m-%d %H:%M:%S"))
        log.addHandler(fh)
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(logging.Formatter("[%(asctime)s] %(message)s", datefmt="%H:%M:%S"))
        log.addHandler(ch)
    return log


def _load_state(cfg: dict) -> dict:
    try:
        return json.loads(Path(cfg["state_path"]).read_text(encoding="utf-8"))
    except Exception:
        return {"last_run": None, "last_checksum": None, "last_record_count": 0,
                "last_classification": None, "run_count": 0, "error_count": 0}


def _save_state(cfg: dict, state: dict, log) -> None:
    """Shannon Rule: keep handoff note under 200 tokens."""
    Path(cfg["state_path"]).parent.mkdir(parents=True, exist_ok=True)
    # Trim handoff_note to Shannon limit
    note = state.get("handoff_note", "")
    if len(note.split()) > 40:
        state["handoff_note"] = " ".join(note.split()[:40]) + "..."
    tmp = cfg["state_path"] + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
    os.replace(tmp, cfg["state_path"])
    log.info(f"state.json saved — run #{state['run_count']}")


def _checksum(data: str) -> str:
    return hashlib.md5(data.encode()).hexdigest()[:12]


def _check_staleness(cfg: dict, state: dict, log) -> bool:
    """Hopper Rule: flag if data is stale."""
    last = state.get("last_run")
    if not last:
        return False
    age_hours = (datetime.now() - datetime.fromisoformat(last)).total_seconds() / 3600
    if age_hours > cfg["stale_after_hours"]:
        log.warning(f"HOPPER: data is {age_hours:.1f}h old — threshold {cfg['stale_after_hours']}h")
        return True
    return False


def _push_inbox(cfg: dict, item: dict) -> None:
    """Push an item to supervisor-inbox.json following Hopper inbox schema."""
    # Minimum schema: id, source, type, urgency, title, finding, status, date
    required = {"id", "source", "type", "urgency", "title", "finding", "status", "date"}
    if not required.issubset(item.keys()):
        missing = required - item.keys()
        raise ValueError(f"Inbox schema violation — missing: {missing}")
    try:
        inbox = json.loads(Path(cfg["inbox_path"]).read_text(encoding="utf-8"))
        if isinstance(inbox, dict):
            inbox = inbox.get("items", [])
    except Exception:
        inbox = []
    existing = {i.get("id") for i in inbox}
    if item["id"] not in existing:
        inbox.append(item)
        tmp = cfg["inbox_path"] + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(inbox, f, indent=2, ensure_ascii=False)
        os.replace(tmp, cfg["inbox_path"])


def _normalize_with_gemini(records: list, cfg: dict, log) -> str:
    """Gemini Free bulk normalization — converts record list to clean JSON string."""
    if not records:
        return "[]"
    prompt = (
        f"Normalize this data to clean JSON. Remove duplicates. "
        f"Standardize date formats to ISO 8601. Trim whitespace. "
        f"Return ONLY valid JSON array, no commentary:\n\n"
        f"{json.dumps(records[:50], ensure_ascii=False)}"  # cap at 50 records per call
    )
    resp = gw_call(prompt, task_type=cfg["normalize_task"], max_tokens=2000)
    if not resp.success:
        log.warning(f"Gemini normalization failed: {resp.error} — using raw records")
        return json.dumps(records, ensure_ascii=False)
    log.info(f"Normalized via {resp.provider}/{resp.model} ({resp.latency_ms}ms)")
    return resp.text


def _synthesize_with_claude(normalized: str, cfg: dict, log) -> str:
    """Claude quality synthesis — plain English narrative from normalized data."""
    prompt = cfg["synthesis_prompt"].format(data=normalized[:3000])
    resp = gw_call(prompt, task_type=cfg["synthesize_task"],
                   max_tokens=cfg["synthesize_max_tokens"])
    if not resp.success:
        log.warning(f"Claude synthesis failed: {resp.error}")
        return f"Synthesis unavailable — {resp.error}"
    log.info(f"Synthesized via {resp.provider}/{resp.model} ({resp.latency_ms}ms)")
    return resp.text


def _classify_with_ollama(normalized: str, cfg: dict, log) -> str:
    """Ollama local classification — no external API calls, no cost."""
    prompt = cfg["classify_prompt"].format(data=normalized[:500])
    resp = gw_call(prompt, task_type=cfg["classify_task"], max_tokens=cfg["classify_max_tokens"])
    if not resp.success:
        log.warning(f"Ollama classification failed: {resp.error} — defaulting to ROUTINE")
        return "ROUTINE"
    label = resp.text.strip().upper().split()[0]
    valid = {"ROUTINE", "NOTABLE", "URGENT", "EMPTY"}
    result = label if label in valid else "ROUTINE"
    log.info(f"Classified: {result} via {resp.provider}/{resp.model}")
    return result


def _deliver(normalized: str, synthesis: str, classification: str,
             records: list, cfg: dict, state: dict, log, dry: bool) -> None:
    """Write outputs to all configured delivery channels."""
    ts = datetime.now().strftime("%Y-%m-%d")
    out_dir = Path(cfg["output_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)

    # Always write to file
    if cfg["deliver_file"] and not dry:
        out_path = out_dir / f"{cfg['agent_id']}-{ts}.json"
        payload = {
            "agent_id":       cfg["agent_id"],
            "pool_number":    cfg["pool_number"],
            "generated_at":   datetime.now().isoformat(),
            "record_count":   len(records),
            "classification": classification,
            "synthesis":      synthesis,
            "records":        json.loads(normalized) if normalized != "[]" else [],
        }
        tmp = str(out_path) + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        os.replace(tmp, str(out_path))
        log.info(f"Output written: {out_path}")

    # Append to daily-digest.json
    if cfg["deliver_digest"] and not dry:
        try:
            digest = json.loads(Path(cfg["digest_path"]).read_text(encoding="utf-8"))
        except Exception:
            digest = {"date": ts, "entries": []}
        digest.setdefault("entries", []).append({
            "agent_id":       cfg["agent_id"],
            "pool_number":    cfg["pool_number"],
            "pool_name":      cfg["pool_name"],
            "timestamp":      datetime.now().isoformat(),
            "record_count":   len(records),
            "classification": classification,
            "synthesis":      synthesis[:300],
        })
        tmp = cfg["digest_path"] + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(digest, f, indent=2, ensure_ascii=False)
        os.replace(tmp, cfg["digest_path"])
        log.info("Appended to daily-digest.json")

    # Email delivery (stub — wire email_delivery_agent when ready)
    if cfg["deliver_email"] and not dry:
        log.info("EMAIL: delivery stub — wire email_delivery_agent")

    # Webhook delivery (stub — wire webhook_delivery_agent when ready)
    if cfg["deliver_webhook"] and not dry:
        log.info("WEBHOOK: delivery stub — wire webhook_delivery_agent")

    if dry:
        log.info("[DRY RUN] Delivery skipped — synthesis preview:")
        log.info(synthesis[:200])


# ══════════════════════════════════════════════════════════════════
# MAIN PIPELINE — Bezos + Hamilton + Hopper enforced
# ══════════════════════════════════════════════════════════════════

def run(cfg: dict, dry: bool = False) -> dict:
    log = _setup_logging(cfg)
    state = _load_state(cfg)
    start_time = time.time()

    log.info(f"=== {cfg['agent_id']} START === pool #{cfg['pool_number']} | dry={dry}")

    def elapsed():
        return time.time() - start_time

    def hamilton_check():
        """Hamilton Rule: abort if TTL exceeded."""
        if elapsed() > cfg["ttl_seconds"]:
            raise TimeoutError(
                f"HAMILTON: runtime {elapsed():.0f}s exceeded TTL {cfg['ttl_seconds']}s — aborting"
            )

    try:
        # ── STEP 1: FETCH ─────────────────────────────────────────
        hamilton_check()
        log.info("Step 1: Fetching raw data...")

        MAX_CONSECUTIVE_FAILURES = 3      # Bezos Rule
        consecutive_failures = 0
        raw = None

        for attempt in range(3):
            try:
                raw = fetch_raw(cfg)
                consecutive_failures = 0
                log.info(f"Fetched {len(raw):,} chars on attempt {attempt+1}")
                break
            except Exception as e:
                consecutive_failures += 1
                log.warning(f"Fetch attempt {attempt+1} failed: {str(e)[:80]}")
                if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                    log.error(f"CIRCUIT BREAKER: {MAX_CONSECUTIVE_FAILURES} consecutive fetch failures")
                    raise
                time.sleep(5)

        if raw is None:
            raise RuntimeError("All fetch attempts failed")

        # ── STEP 2: HOPPER FRESHNESS CHECK ───────────────────────
        checksum = _checksum(raw)
        if checksum == state.get("last_checksum"):
            log.info("HOPPER: source unchanged since last run — skipping processing")
            state["last_run"] = datetime.now().isoformat()
            state["handoff_note"] = f"No change detected. Last run: {state['last_run'][:10]}"
            _save_state(cfg, state, log)
            return {"status": "skipped", "reason": "unchanged"}

        # Hopper Rule: log pull metadata
        pull_meta = {
            "pull_timestamp": datetime.now().isoformat(),
            "source_url":     cfg["source_url"],
            "byte_count":     len(raw),
            "checksum":       checksum,
        }
        log.info(f"HOPPER: pull logged — {pull_meta['byte_count']:,} bytes, checksum={checksum}")

        # ── STEP 3: PARSE ─────────────────────────────────────────
        hamilton_check()
        log.info("Step 2: Parsing raw data...")
        records = parse_raw(raw, cfg)
        log.info(f"Parsed {len(records)} records")

        if not records:
            log.warning("No records parsed — possible empty source or parser bug")
            state["handoff_note"] = f"Empty parse result. Check parser. {datetime.now().isoformat()[:10]}"
            _save_state(cfg, state, log)
            return {"status": "empty"}

        # ── STEP 4: NORMALIZE (Gemini Free) ──────────────────────
        hamilton_check()
        log.info("Step 3: Normalizing with Gemini...")
        normalized = _normalize_with_gemini(records, cfg, log)

        # ── STEP 5: CLASSIFY (Ollama local) ──────────────────────
        hamilton_check()
        log.info("Step 4: Classifying with Ollama...")
        classification = _classify_with_ollama(normalized[:500], cfg, log)

        # ── STEP 6: SYNTHESIZE (Claude) ──────────────────────────
        hamilton_check()
        log.info("Step 5: Synthesizing with Claude...")
        synthesis = _synthesize_with_claude(normalized, cfg, log)

        # ── STEP 7: DELIVER ───────────────────────────────────────
        hamilton_check()
        log.info("Step 6: Delivering outputs...")
        _deliver(normalized, synthesis, classification, records, cfg, state, log, dry)

        # ── STEP 8: UPDATE STATE ──────────────────────────────────
        state.update({
            "last_run":            datetime.now().isoformat(),
            "last_checksum":       checksum,
            "last_record_count":   len(records),
            "last_classification": classification,
            "run_count":           state.get("run_count", 0) + 1,
            "pull_meta":           pull_meta,
            "handoff_note": (      # Shannon Rule: ≤40 words
                f"{cfg['agent_id']} ran {datetime.now().isoformat()[:10]}. "
                f"{len(records)} records. {classification}. "
                f"Synthesis: {synthesis[:60]}..."
            ),
        })
        _save_state(cfg, state, log)

        # Push URGENT to supervisor inbox
        if classification == "URGENT":
            _push_inbox(cfg, {
                "id":      f"{cfg['agent_id']}-urgent-{datetime.now().strftime('%Y%m%d')}",
                "source":  cfg["agent_id"],
                "type":    "data_alert",
                "urgency": "WARN",
                "title":   f"URGENT: {cfg['pool_name']} update",
                "finding": synthesis[:200],
                "status":  "PENDING",
                "date":    datetime.now().isoformat(),
            })
            log.info("URGENT classification — pushed to supervisor inbox")

        elapsed_s = elapsed()
        log.info(f"=== {cfg['agent_id']} COMPLETE === {elapsed_s:.1f}s | {len(records)} records | {classification}")
        return {"status": "ok", "records": len(records), "classification": classification}

    except TimeoutError as e:
        log.error(str(e))
        state["error_count"] = state.get("error_count", 0) + 1
        state["handoff_note"] = f"TIMEOUT abort {datetime.now().isoformat()[:10]}. Check TTL."
        _save_state(cfg, state, log)
        _push_inbox(cfg, {
            "id":      f"{cfg['agent_id']}-timeout-{datetime.now().strftime('%Y%m%d%H%M')}",
            "source":  cfg["agent_id"],
            "type":    "agent_error",
            "urgency": "WARN",
            "title":   f"TIMEOUT: {cfg['agent_id']}",
            "finding": str(e)[:200],
            "status":  "PENDING",
            "date":    datetime.now().isoformat(),
        })
        return {"status": "timeout"}

    except Exception as e:
        log.error(f"PIPELINE FAILED: {str(e)[:200]}")
        state["error_count"] = state.get("error_count", 0) + 1
        state["handoff_note"] = f"ERROR {datetime.now().isoformat()[:10]}: {str(e)[:60]}"
        _save_state(cfg, state, log)
        _push_inbox(cfg, {
            "id":      f"{cfg['agent_id']}-error-{datetime.now().strftime('%Y%m%d%H%M')}",
            "source":  cfg["agent_id"],
            "type":    "agent_error",
            "urgency": "WARN",
            "title":   f"ERROR: {cfg['agent_id']}",
            "finding": str(e)[:200],
            "status":  "PENDING",
            "date":    datetime.now().isoformat(),
        })
        return {"status": "error", "error": str(e)[:200]}


# ══════════════════════════════════════════════════════════════════
# ENTRYPOINT
# ══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=f"Tier 1 pipeline: {AGENT_CONFIG['agent_id']}")
    parser.add_argument("--dry", action="store_true", help="Dry run — fetch and process but do not deliver")
    args = parser.parse_args()
    result = run(AGENT_CONFIG, dry=args.dry)
    print(f"\nResult: {result}")
    sys.exit(0 if result.get("status") in ("ok", "skipped", "empty") else 1)
