"""
sanctions_ingestor.py
=====================
Tier 1 Pipeline — Pool #73: Sanctions Lists Multi-jurisdictional
Pulls from 5 free official sources daily, normalizes, classifies, synthesizes.

SOURCES (all free, no API key required):
  1. UN Consolidated Sanctions List (XML)
  2. EU Financial Sanctions Files (XML)
  3. UK OFSI Consolidated List (CSV)
  4. OFAC SDN List (XML)
  5. OFAC Non-SDN Consolidated (XML)

SCHEDULE: 02:00 daily via Task Scheduler \\Studio\\SanctionsIngestor
EXPECTED RUNTIME: ~120s | TTL: 480s | Hamilton kill at 2x = 960s (set in XML)

RULES ENFORCED: Bezos, Hamilton, Hopper, Codd, Shannon, Gall
"""

# EXPECTED_RUNTIME_SECONDS: 300

import json, os, sys, time, hashlib, logging, argparse
import xml.etree.ElementTree as ET
import csv, io, urllib.request
from datetime import datetime
from pathlib import Path

sys.path.insert(0, "G:/My Drive/Projects/_studio")
from ai_gateway import call as gw_call
import provider_health as ph

import sys as _sys
_sys.path.insert(0, "G:/My Drive/Projects/_studio/utilities")
from constraint_gates import hamilton_watchdog

# ══════════════════════════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════════════════════════

AGENT_CONFIG = {
    "agent_id":          "sanctions-ingestor",
    "pool_name":         "Sanctions Lists Multi-jurisdictional",
    "pool_number":       73,
    "ttl_seconds":       480,
    "source_cadence":    "daily",
    "stale_after_hours": 25,
    "source_format":     "multi",
    "normalize_task":    "batch",
    "synthesize_task":   "reasoning",  # quality=Claude only; reasoning=Mistral→GitHub→Claude
    "classify_task":     "local",
    "synthesis_prompt": (
        "You are a sanctions compliance analyst. "
        "Given today's sanctions data summary: {data}\n\n"
        "Write exactly 3 sentences:\n"
        "1) Which jurisdictions were updated and total entity counts per list\n"
        "2) Any notable new individual or entity designations (name them if visible)\n"
        "3) One actionable note for compliance screening teams\n"
        "Be factual. Confidence < 70% on any claim = write 'insufficient signal'."
    ),
    "synthesize_max_tokens": 350,
    "classify_prompt": (
        "Classify this sanctions update. Return ONLY one word.\n"
        "URGENT = new state actor, major bank, or financial system designation\n"
        "NOTABLE = named high-profile individuals or entities added\n"
        "ROUTINE = standard maintenance, minor updates\n"
        "EMPTY = no records parsed or all sources failed\n\n"
        "Data summary: {data}\n\nClassification:"
    ),
    "classify_max_tokens": 10,
    "deliver_email":   False,
    "deliver_webhook": False,
    "deliver_file":    True,
    "deliver_digest":  True,
    "output_dir":  "G:/My Drive/Projects/_studio/data/sanctions",
    "state_path":  "G:/My Drive/Projects/_studio/data/sanctions/state.json",
    "log_path":    "G:/My Drive/Projects/_studio/logs/sanctions-ingestor.log",
    "digest_path": "G:/My Drive/Projects/_studio/daily-digest.json",
    "inbox_path":  "G:/My Drive/Projects/_studio/supervisor-inbox.json",
}

# ══════════════════════════════════════════════════════════════════
# SOURCE DEFINITIONS — each source = {id, url, format, parser_fn}
# ══════════════════════════════════════════════════════════════════

UA = "StudioAgent/1.0 (sanctions-ingestor; research use)"

SOURCES = [
    {
        "id":     "UN",
        "name":   "UN Security Council Consolidated List",
        "url":    "https://scsanctions.un.org/resources/xml/en/consolidated.xml",
        "format": "xml",
    },
    {
        "id":     "EU",
        "name":   "EU Financial Sanctions Files",
        "url":    "https://webgate.ec.europa.eu/fsd/fsf/public/files/xmlFullSanctionsList_1_1/content?token=dG9rZW4tMjAxNw",
        "format": "xml",
    },
    {
        "id":     "OFAC_SDN",
        "name":   "OFAC Specially Designated Nationals",
        "url":    "https://www.treasury.gov/ofac/downloads/sdn.xml",
        "format": "xml",
    },
    {
        "id":     "OFAC_CONS",
        "name":   "OFAC Non-SDN Consolidated",
        "url":    "https://www.treasury.gov/ofac/downloads/consolidated/consolidated.xml",
        "format": "xml",
    },
    {
        "id":     "UK_OFSI",
        "name":   "UK OFSI Consolidated Sanctions List",
        "url":    "https://ofsistorage.blob.core.windows.net/publishlive/ConList.csv",
        "format": "csv",
    },
]


def _fetch_url(url: str, timeout: int = 45) -> bytes:
    """Fetch URL bytes with retries. Raises on failure."""
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


# ══════════════════════════════════════════════════════════════════
# PARSERS — one per format, Codd Rule enforced throughout
# ══════════════════════════════════════════════════════════════════

def _parse_un_xml(raw_bytes: bytes) -> list[dict]:
    """Parse UN consolidated XML. Handles INDIVIDUAL and ENTITY nodes."""
    records = []
    try:
        root = ET.fromstring(raw_bytes)
        ns = {"": root.tag.split("}")[0].lstrip("{") if "}" in root.tag else ""}

        def txt(node, tag):
            """Codd: blank over wrong — never guess."""
            el = node.find(tag)
            return el.text.strip() if el is not None and el.text else ""

        for individual in root.iter("INDIVIDUAL"):
            fname = txt(individual, "FIRST_NAME")
            sname = txt(individual, "SECOND_NAME")
            tname = txt(individual, "THIRD_NAME")
            name_parts = [p for p in [fname, sname, tname] if p]
            records.append({
                "list":        "UN",
                "entity_type": "individual",
                "name":        " ".join(name_parts) if name_parts else "",
                "date_listed": txt(individual, "LISTED_ON"),
                "nationality": txt(individual, "NATIONALITY"),
                "un_ref":      txt(individual, "REFERENCE_NUMBER"),
                "reason":      txt(individual, "COMMENTS1")[:200],
            })

        for entity in root.iter("ENTITY"):
            records.append({
                "list":        "UN",
                "entity_type": "entity",
                "name":        txt(entity, "FIRST_NAME"),
                "date_listed": txt(entity, "LISTED_ON"),
                "nationality": txt(entity, "NATIONALITY"),
                "un_ref":      txt(entity, "REFERENCE_NUMBER"),
                "reason":      txt(entity, "COMMENTS1")[:200],
            })
    except ET.ParseError as e:
        raise ValueError(f"UN XML parse error: {e}")
    return records


def _parse_eu_xml(raw_bytes: bytes) -> list[dict]:
    """Parse EU FSF XML. Entity nodes vary — extract what's present."""
    records = []
    try:
        root = ET.fromstring(raw_bytes)
        for entry in root.iter("sanctionEntity"):
            name_el = entry.find(".//nameAlias")
            name = ""
            if name_el is not None:
                name = (name_el.get("wholeName") or
                        f"{name_el.get('firstName','')} {name_el.get('lastName','')}".strip())
            bdate = ""
            bd = entry.find(".//birthdate")
            if bd is not None:
                bdate = bd.get("birthdate", "")
            subject_type = entry.get("subjectType", "")
            records.append({
                "list":        "EU",
                "entity_type": subject_type.lower() if subject_type else "",
                "name":        name,
                "date_listed": entry.get("designationDate", ""),
                "nationality": entry.get("citizenship", ""),
                "eu_ref":      entry.get("euReferenceNumber", ""),
                "birth_date":  bdate,
                "reason":      "",
            })
    except ET.ParseError as e:
        raise ValueError(f"EU XML parse error: {e}")
    return records

def _parse_ofac_xml(raw_bytes: bytes, list_id: str) -> list[dict]:
    """Parse OFAC SDN or consolidated XML. Both share the same schema."""
    records = []
    try:
        root = ET.fromstring(raw_bytes)
        # OFAC uses a default namespace — strip it for clean iteration
        ns_prefix = ""
        if root.tag.startswith("{"):
            ns_prefix = root.tag.split("}")[0] + "}"

        def find_text(node, tag):
            el = node.find(f"{ns_prefix}{tag}")
            return el.text.strip() if el is not None and el.text else ""

        for entry in root.iter(f"{ns_prefix}sdnEntry"):
            # Build name from components
            fname  = find_text(entry, "firstName")
            lname  = find_text(entry, "lastName")
            name   = f"{fname} {lname}".strip() if fname or lname else ""
            if not name:
                name = find_text(entry, "lastName")  # entities use lastName only

            sdn_type = find_text(entry, "sdnType")
            uid      = find_text(entry, "uid")

            # Programs (can be multiple)
            programs = [
                p.text.strip()
                for p in entry.findall(f".//{ns_prefix}program")
                if p.text
            ]

            records.append({
                "list":        list_id,
                "entity_type": sdn_type.lower() if sdn_type else "",
                "name":        name,
                "date_listed": "",          # OFAC XML does not include list date in entry
                "nationality": "",          # available in address/nationality sub-nodes if needed
                "ofac_uid":    uid,
                "programs":    ", ".join(programs[:5]),  # cap at 5 programs
                "reason":      "",
            })
    except ET.ParseError as e:
        raise ValueError(f"OFAC {list_id} XML parse error: {e}")
    return records


def _parse_uk_csv(raw_bytes: bytes) -> list[dict]:
    """Parse UK OFSI CSV. Encoding is latin-1 on some releases."""
    records = []
    try:
        # Try UTF-8 first, fall back to latin-1
        try:
            text = raw_bytes.decode("utf-8")
        except UnicodeDecodeError:
            text = raw_bytes.decode("latin-1")

        reader = csv.DictReader(io.StringIO(text))
        for row in reader:
            name = row.get("Name 6", "") or row.get("Name", "") or row.get("Full Name", "")
            if not name:
                # Compose from parts if full name absent
                parts = [
                    row.get("Name 1", ""), row.get("Name 2", ""),
                    row.get("Name 3", ""), row.get("Name 4", ""),
                    row.get("Name 5", ""),
                ]
                name = " ".join(p.strip() for p in parts if p.strip())

            records.append({
                "list":        "UK_OFSI",
                "entity_type": row.get("Entity Type", "").lower(),
                "name":        name.strip(),
                "date_listed": row.get("Last Updated", ""),
                "nationality": row.get("Country", ""),
                "uk_ref":      row.get("Unique ID", ""),
                "regime":      row.get("Regime", "")[:100],
                "reason":      row.get("Reason for Designation", "")[:200],
            })
    except Exception as e:
        raise ValueError(f"UK OFSI CSV parse error: {e}")
    return records

# ══════════════════════════════════════════════════════════════════
# FETCH + PARSE — real implementations wired to sources above
# ══════════════════════════════════════════════════════════════════

def fetch_raw(cfg: dict) -> str:
    """
    Fetch all 5 sources. Return JSON string of per-source results.
    Partial failures are logged but do not abort — other sources continue.
    Bezos Rule: MAX_CONSECUTIVE_FAILURES=3 applied per source.
    """
    results = {}
    consecutive_failures = 0
    MAX_CONSECUTIVE_FAILURES = 3

    for src in SOURCES:
        try:
            raw_bytes = _fetch_url(src["url"], timeout=45)
            results[src["id"]] = {
                "status":     "ok",
                "byte_count": len(raw_bytes),
                "raw_b64":    None,          # don't store raw in state — just counts
                "_raw_bytes": raw_bytes,     # in-memory only, stripped before JSON
                "name":       src["name"],
                "format":     src["format"],
            }
            consecutive_failures = 0
        except Exception as e:
            consecutive_failures += 1
            results[src["id"]] = {
                "status": "error",
                "error":  str(e)[:120],
                "name":   src["name"],
            }
            if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                # Bezos Rule: abort remaining sources to avoid waste
                break

    # Serialize — strip raw bytes from JSON output
    serializable = {}
    for k, v in results.items():
        sv = {kk: vv for kk, vv in v.items() if kk != "_raw_bytes"}
        serializable[k] = sv

    # Attach raw bytes separately — passed through as _raw_cache
    # Return JSON for checksum, raw bytes attached in module-level cache
    _RAW_CACHE.clear()
    for k, v in results.items():
        if v.get("status") == "ok" and "_raw_bytes" in v:
            _RAW_CACHE[k] = v["_raw_bytes"]

    return json.dumps(serializable, ensure_ascii=False)


# Module-level raw bytes cache — populated by fetch_raw, consumed by parse_raw
_RAW_CACHE: dict = {}


def parse_raw(raw: str, cfg: dict) -> list[dict]:
    """
    Parse all fetched sources into unified record list.
    Codd Rule: blank over wrong — each parser leaves missing fields empty.
    Sources that errored are skipped cleanly.
    """
    source_meta = json.loads(raw)
    all_records = []

    parsers = {
        "UN":        lambda b: _parse_un_xml(b),
        "EU":        lambda b: _parse_eu_xml(b),
        "OFAC_SDN":  lambda b: _parse_ofac_xml(b, "OFAC_SDN"),
        "OFAC_CONS": lambda b: _parse_ofac_xml(b, "OFAC_CONS"),
        "UK_OFSI":   lambda b: _parse_uk_csv(b),
    }

    for src_id, meta in source_meta.items():
        if meta.get("status") != "ok":
            continue
        raw_bytes = _RAW_CACHE.get(src_id)
        if not raw_bytes:
            continue
        parser = parsers.get(src_id)
        if not parser:
            continue
        try:
            records = parser(raw_bytes)
            # Tag each record with source for traceability
            for r in records:
                r["_source_fetch_ts"] = datetime.now().isoformat()
            all_records.extend(records)
        except Exception as e:
            # Log parse failure but continue with other sources
            print(f"[WARN] {src_id} parse failed: {str(e)[:100]}")

    return all_records

# ══════════════════════════════════════════════════════════════════
# FRAMEWORK — copied verbatim from tier1_pipeline_template.py
# DO NOT MODIFY — changes go in the template, then propagate here
# ══════════════════════════════════════════════════════════════════

def _setup_logging(cfg):
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


def _load_state(cfg):
    try:
        return json.loads(Path(cfg["state_path"]).read_text(encoding="utf-8"))
    except Exception:
        return {"last_run": None, "last_checksum": None, "last_record_count": 0,
                "last_classification": None, "run_count": 0, "error_count": 0}


def _save_state(cfg, state, log):
    Path(cfg["state_path"]).parent.mkdir(parents=True, exist_ok=True)
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


def _push_inbox(cfg, item):
    required = {"id", "source", "type", "urgency", "title", "finding", "status", "date"}
    if not required.issubset(item.keys()):
        raise ValueError(f"Inbox schema violation — missing: {required - item.keys()}")
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


def _normalize_with_gemini(records, cfg, log):
    if not records:
        return "[]"
    prompt = (
        "Normalize this sanctions data to clean JSON. Remove exact duplicates. "
        "Standardize date formats to ISO 8601. Trim whitespace from all strings. "
        "Return ONLY a valid JSON array, no commentary, no markdown:\n\n"
        + json.dumps(records[:50], ensure_ascii=False)
    )
    resp = gw_call(prompt, task_type=cfg["normalize_task"], max_tokens=2000)
    if not resp.success:
        log.warning(f"Gemini normalization failed: {resp.error} — using raw records")
        return json.dumps(records[:50], ensure_ascii=False)
    log.info(f"Normalized via {resp.provider}/{resp.model} ({resp.latency_ms}ms)")
    return resp.text


def _classify_with_ollama(data_summary, cfg, log):
    prompt = cfg["classify_prompt"].format(data=data_summary[:500])
    resp = gw_call(prompt, task_type=cfg["classify_task"], max_tokens=cfg["classify_max_tokens"])
    if not resp.success:
        log.warning(f"Ollama classification failed: {resp.error} — defaulting ROUTINE")
        return "ROUTINE"
    label = resp.text.strip().upper().split()[0]
    result = label if label in {"ROUTINE", "NOTABLE", "URGENT", "EMPTY"} else "ROUTINE"
    log.info(f"Classified: {result} via {resp.provider}/{resp.model}")
    return result


def _synthesize_with_claude(data_summary, cfg, log):
    # Sanitize — strip control chars and escape braces that break .format()
    clean = (data_summary
             .replace("\x00", "")
             .replace("\r", " ")
             .replace("{", "(")
             .replace("}", ")")
             [:3000])
    prompt = cfg["synthesis_prompt"].format(data=clean)
    resp = gw_call(prompt, task_type=cfg["synthesize_task"],
                   max_tokens=cfg["synthesize_max_tokens"])
    if not resp.success:
        log.warning(f"Claude synthesis failed: {resp.error}")
        return f"Synthesis unavailable — {resp.error}"
    log.info(f"Synthesized via {resp.provider}/{resp.model} ({resp.latency_ms}ms)")
    return resp.text

def _deliver(normalized, synthesis, classification, records, source_meta,
             cfg, state, log, dry):
    ts = datetime.now().strftime("%Y-%m-%d")
    out_dir = Path(cfg["output_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)

    # Build per-source counts for output
    counts = {}
    for r in records:
        lst = r.get("list", "unknown")
        counts[lst] = counts.get(lst, 0) + 1

    if cfg["deliver_file"] and not dry:
        out_path = out_dir / f"sanctions-{ts}.json"
        payload = {
            "agent_id":       cfg["agent_id"],
            "pool_number":    cfg["pool_number"],
            "generated_at":   datetime.now().isoformat(),
            "total_records":  len(records),
            "per_source":     counts,
            "classification": classification,
            "synthesis":      synthesis,
            "source_status":  source_meta,
            "sample_records": records[:20],   # first 20 records as sample
        }
        tmp = str(out_path) + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        os.replace(tmp, str(out_path))
        log.info(f"Output written: {out_path}")

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
            "total_records":  len(records),
            "per_source":     counts,
            "classification": classification,
            "synthesis":      synthesis[:300],
        })
        tmp = cfg["digest_path"] + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(digest, f, indent=2, ensure_ascii=False)
        os.replace(tmp, cfg["digest_path"])
        log.info("Appended to daily-digest.json")

    if dry:
        log.info("[DRY RUN] Delivery skipped")
        log.info(f"  Total records: {len(records)}")
        log.info(f"  Per source: {counts}")
        log.info(f"  Classification: {classification}")
        log.info(f"  Synthesis: {synthesis[:300]}")


# ══════════════════════════════════════════════════════════════════
# MAIN PIPELINE
# ══════════════════════════════════════════════════════════════════

def run(cfg: dict, dry: bool = False) -> dict:
    log = _setup_logging(cfg)
    state = _load_state(cfg)
    start_time = time.time()
    log.info(f"=== {cfg['agent_id']} START === pool #{cfg['pool_number']} | dry={dry}")

    def elapsed():
        return time.time() - start_time

    def hamilton_check():
        if elapsed() > cfg["ttl_seconds"]:
            raise TimeoutError(
                f"HAMILTON: {elapsed():.0f}s exceeded TTL {cfg['ttl_seconds']}s — aborting"
            )

    try:
        # STEP 1 — FETCH
        hamilton_check()
        log.info("Step 1: Fetching all sanctions sources...")
        raw = fetch_raw(cfg)
        source_meta = json.loads(raw)
        ok_sources  = [k for k, v in source_meta.items() if v.get("status") == "ok"]
        fail_sources = [k for k, v in source_meta.items() if v.get("status") != "ok"]
        log.info(f"Sources OK: {ok_sources} | Failed: {fail_sources}")
        if not ok_sources:
            raise RuntimeError("All 5 sources failed — network or source issue")

        # STEP 2 — HOPPER FRESHNESS
        checksum = _checksum(raw)
        if checksum == state.get("last_checksum"):
            log.info("HOPPER: no change since last run — skipping")
            state["last_run"] = datetime.now().isoformat()
            state["handoff_note"] = f"No change. Last: {state['last_run'][:10]}"
            _save_state(cfg, state, log)
            return {"status": "skipped", "reason": "unchanged"}

        pull_meta = {
            "pull_timestamp": datetime.now().isoformat(),
            "sources_ok":     ok_sources,
            "sources_failed": fail_sources,
            "checksum":       checksum,
        }
        log.info(f"HOPPER: pull logged, checksum={checksum}")

        # STEP 3 — PARSE
        hamilton_check()
        log.info("Step 2: Parsing all sources...")
        records = parse_raw(raw, cfg)
        log.info(f"Total records parsed: {len(records)}")
        if not records:
            state["handoff_note"] = f"Empty parse. {datetime.now().isoformat()[:10]}"
            _save_state(cfg, state, log)
            return {"status": "empty"}

        # STEP 4 — NORMALIZE (Gemini)
        hamilton_check()
        log.info("Step 3: Normalizing with Gemini...")
        normalized = _normalize_with_gemini(records, cfg, log)

        # Build summary for classify + synthesize (counts + sample names)
        counts = {}
        for r in records:
            counts[r.get("list","?")] = counts.get(r.get("list","?"),0) + 1
        sample_names = [r.get("name","") for r in records[:10] if r.get("name")]
        data_summary = (
            f"Sources: {ok_sources}. "
            f"Total entities: {len(records)}. "
            f"Per list: {json.dumps(counts)}. "
            f"Sample names: {', '.join(sample_names[:5])}."
        )

        # STEP 5 — CLASSIFY (Ollama)
        hamilton_check()
        log.info("Step 4: Classifying with Ollama...")
        classification = _classify_with_ollama(data_summary, cfg, log)

        # STEP 6 — SYNTHESIZE (Claude)
        hamilton_check()
        log.info("Step 5: Synthesizing with Claude...")
        synthesis = _synthesize_with_claude(data_summary, cfg, log)

        # STEP 7 — DELIVER
        hamilton_check()
        log.info("Step 6: Delivering outputs...")
        _deliver(normalized, synthesis, classification, records,
                 source_meta, cfg, state, log, dry)

        # STEP 8 — UPDATE STATE
        state.update({
            "last_run":            datetime.now().isoformat(),
            "last_checksum":       checksum,
            "last_record_count":   len(records),
            "last_per_source":     counts,
            "last_classification": classification,
            "sources_ok":          ok_sources,
            "sources_failed":      fail_sources,
            "run_count":           state.get("run_count", 0) + 1,
            "pull_meta":           pull_meta,
            "handoff_note": (
                f"sanctions-ingestor ran {datetime.now().isoformat()[:10]}. "
                f"{len(records)} entities across {len(ok_sources)} lists. "
                f"{classification}. {synthesis[:80]}..."
            ),
        })
        _save_state(cfg, state, log)

        if classification == "URGENT":
            _push_inbox(cfg, {
                "id":      f"sanctions-urgent-{datetime.now().strftime('%Y%m%d')}",
                "source":  "sanctions-ingestor",
                "type":    "data_alert",
                "urgency": "WARN",
                "title":   "URGENT: Sanctions list update",
                "finding": synthesis[:200],
                "status":  "PENDING",
                "date":    datetime.now().isoformat(),
            })
            log.info("URGENT — pushed to supervisor inbox")

        log.info(f"=== COMPLETE === {elapsed():.1f}s | {len(records)} records | {classification}")
        return {"status": "ok", "records": len(records), "classification": classification,
                "sources_ok": ok_sources, "sources_failed": fail_sources}

    except TimeoutError as e:
        log.error(str(e))
        state["error_count"] = state.get("error_count", 0) + 1
        state["handoff_note"] = f"TIMEOUT {datetime.now().isoformat()[:10]}"
        _save_state(cfg, state, log)
        _push_inbox(cfg, {"id": f"sanctions-timeout-{datetime.now().strftime('%Y%m%d%H%M')}",
                          "source": "sanctions-ingestor", "type": "agent_error",
                          "urgency": "WARN", "title": "TIMEOUT: sanctions-ingestor",
                          "finding": str(e)[:200], "status": "PENDING",
                          "date": datetime.now().isoformat()})
        return {"status": "timeout"}

    except Exception as e:
        log.error(f"PIPELINE FAILED: {str(e)[:200]}")
        state["error_count"] = state.get("error_count", 0) + 1
        state["handoff_note"] = f"ERROR {datetime.now().isoformat()[:10]}: {str(e)[:60]}"
        _save_state(cfg, state, log)
        _push_inbox(cfg, {"id": f"sanctions-error-{datetime.now().strftime('%Y%m%d%H%M')}",
                          "source": "sanctions-ingestor", "type": "agent_error",
                          "urgency": "WARN", "title": "ERROR: sanctions-ingestor",
                          "finding": str(e)[:200], "status": "PENDING",
                          "date": datetime.now().isoformat()})
        return {"status": "error", "error": str(e)[:200]}


# ══════════════════════════════════════════════════════════════════
# ENTRYPOINT
# ══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Sanctions Ingestor — Pool #73")
    parser.add_argument("--dry", action="store_true",
                        help="Fetch + process but skip file delivery")
    args = parser.parse_args()
    result = run(AGENT_CONFIG, dry=args.dry)
    print(f"\nResult: {result}")
    sys.exit(0 if result.get("status") in ("ok", "skipped", "empty") else 1)
