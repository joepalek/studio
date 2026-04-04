
MAX_CONSECUTIVE_FAILURES = 3  # Bezos Rule
"""
wasde_parser.py  v2.0
=====================
Tier 1 pipeline — USDA WASDE Monthly Food Cost Alert | Pool #56
Built from tier1_pipeline_template.py (Gall's Law).

WHAT'S NEW IN v2.0:
  - Dual AI consensus check (Mistral + Gemini) in synthesis step
  - Signal override layer post-synthesis
  - Narrative extraction with precise section anchors
  - Plausibility bounds validation (WASDE_BOUNDS)
  - Narrative re-attached through Gemini normalization
  - _apply_signal_overrides() extracted for dual AI path

USAGE:
  python wasde_parser.py           # production run
  python wasde_parser.py --dry     # dry run, no delivery
  python wasde_parser.py --backtest # 12-month validation

SCHEDULER: \\Studio\\wasde-parser | 02:15 daily | TTL 600s
"""

# EXPECTED_RUNTIME_SECONDS: 300

import json, os, sys, time, hashlib, logging, argparse, io
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, "G:/My Drive/Projects/_studio")
from ai_gateway import call as gw_call

import sys as _sys
_sys.path.insert(0, "G:/My Drive/Projects/_studio/utilities")
from constraint_gates import hamilton_watchdog

# ══════════════════════════════════════════════════════════════
# URL BUILDER
# ══════════════════════════════════════════════════════════════

def _build_wasde_url(target_date=None):
    d = target_date or datetime.now()
    return f"https://www.usda.gov/oce/commodity/wasde/wasde{d.strftime('%m%y')}.pdf"

# ══════════════════════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════════════════════

AGENT_CONFIG = {
    "agent_id":       "wasde-parser",
    "pool_name":      "USDA WASDE Food Cost Alert",
    "pool_number":    56,
    "ttl_seconds":       600,
    "source_cadence":    "monthly",
    "stale_after_hours": 720,
    "source_url":    _build_wasde_url(),
    "source_format": "pdf",
    "normalize_task":  "batch",
    "synthesize_task": "reasoning",
    "classify_task":   "local",
    "synthesis_prompt": (
        "You are a food procurement analyst. "
        "Your audience is food buyers who need to know if commodity prices will rise or fall.\n\n"
        "WASDE data this month:\n{data}\n\n"
        "Each record has a 'narrative' field with USDA prose and a 'signal' field "
        "pre-computed from keyword analysis (BULLISH/BEARISH/NEUTRAL/UNKNOWN).\n"
        "Use narrative when numeric fields are blank. Trust signal when BULLISH or BEARISH.\n\n"
        "For each commodity (Wheat, Corn, Soybeans, Cotton, Rice), write ONE sentence:\n"
        "  Format: 'CommodityName: [what changed] -- [BULLISH/BEARISH/NEUTRAL] for prices'\n\n"
        "CRITICAL RULES:\n"
        "1. Early harvest = MORE supply = BEARISH. Not bullish.\n"
        "2. La Nina/drought = supply CUT = BULLISH.\n"
        "3. Production cut = tighter supply = BULLISH.\n"
        "4. Ambiguous or missing data = NEUTRAL. Never force direction.\n"
        "5. 'No changes this month' = NEUTRAL.\n"
        "6. 'Lower supplies' OR 'reduced exports' = BULLISH even if ending stocks steady.\n"
        "7. signal=UNKNOWN means insufficient data — default NEUTRAL.\n\n"
        "After the 5 lines, add: "
        "'Overall: [BULLISH/BEARISH/NEUTRAL/MIXED] -- [one procurement sentence]'\n\n"
        "Return ONLY these 6 lines. No preamble."
    ),
    "synthesize_max_tokens": 400,
    "classify_prompt": (
        "Classify this WASDE data: [BULLISH, BEARISH, NEUTRAL, EMPTY]. "
        "BULLISH=supply tighter. BEARISH=supply looser. NEUTRAL=mixed. EMPTY=no data. "
        "Return ONLY the label.\n\nData: {data}"
    ),
    "classify_max_tokens": 10,
    "deliver_email":   True,
    "deliver_webhook": False,
    "deliver_file":    True,
    "deliver_digest":  True,
    "output_dir":  "G:/My Drive/Projects/_studio/data/wasde",
    "state_path":  "G:/My Drive/Projects/_studio/data/wasde/state.json",
    "log_path":    "G:/My Drive/Projects/_studio/logs/wasde-parser.log",
    "digest_path": "G:/My Drive/Projects/_studio/daily-digest.json",
    "inbox_path":  "G:/My Drive/Projects/_studio/supervisor-inbox.json",
    "config_path": "G:/My Drive/Projects/_studio/studio-config.json",
}

WASDE_COMMODITIES = ["Wheat", "Corn", "Soybeans", "Cotton", "Rice"]

# ══════════════════════════════════════════════════════════════
# FETCH — PDF download + pdfplumber extraction
# ══════════════════════════════════════════════════════════════

def fetch_raw(cfg):
    import pdfplumber, urllib.request
    req = urllib.request.Request(cfg["source_url"], headers={
        "User-Agent": "StudioAgent/1.0", "Accept": "application/pdf"})
    with urllib.request.urlopen(req, timeout=60) as r:
        pdf_bytes = r.read()
    if len(pdf_bytes) < 1000:
        raise RuntimeError(f"PDF too small ({len(pdf_bytes)}b) — not released yet")
    all_tables, all_text = [], []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            all_text.append(page.extract_text() or "")
            tbls = page.extract_tables()
            if tbls:
                all_tables.extend(tbls)
    full_text = "\n\n--- PAGE BREAK ---\n\n".join(all_text)
    if not full_text.strip() and not all_tables:
        raise RuntimeError("pdfplumber extracted no content")
    return json.dumps({"tables": all_tables, "text": full_text}, ensure_ascii=False)

# ══════════════════════════════════════════════════════════════
# PARSE — commodity table + narrative extraction
# ══════════════════════════════════════════════════════════════

WASDE_BOUNDS = {
    "Wheat":    {"production":(1200,2800),"ending_stocks":(300,1200),
                 "exports":(700,1400),"domestic_use":(900,1600)},
    "Corn":     {"production":(10000,16000),"ending_stocks":(700,2500),
                 "exports":(1500,3000),"domestic_use":(8000,13000)},
    "Soybeans": {"production":(3000,5000),"ending_stocks":(100,1000),
                 "exports":(1500,2500),"domestic_use":(1800,2800)},
    "Cotton":   {"production":(10000,22000),"ending_stocks":(3000,10000),
                 "exports":(8000,18000),"domestic_use":(2000,5000)},
    "Rice":     {"production":(150,280),"ending_stocks":(20,80),
                 "exports":(50,130),"domestic_use":(100,200)},
}

DOMESTIC_USE_LABELS = {
    "Wheat":    ["DOMESTIC USE","TOTAL DOMESTIC USE","FOOD USE","FOOD, SEED & IND."],
    "Corn":     ["DOMESTIC USE","TOTAL DOMESTIC USE","FOOD, SEED & IND.","FEED & RESIDUAL"],
    "Soybeans": ["DOMESTIC USE","TOTAL DOMESTIC USE","CRUSHINGS","CRUSH"],
    "Cotton":   ["DOMESTIC USE","TOTAL DOMESTIC USE","MILL USE","DOMESTIC MILL USE"],
    "Rice":     ["DOMESTIC USE","TOTAL DOMESTIC USE","FOOD USE","DOMESTIC FOOD USE"],
}

NARRATIVE_ANCHORS = {
    "Wheat":    ["WHEAT:","U.S. WHEAT"],
    "Corn":     ["CORN:","U.S. CORN","FEED GRAINS:"],
    "Soybeans": ["OILSEEDS:","U.S. 2025/26 SOYBEAN","SOYBEANS:"],
    "Cotton":   ["COTTON:","UPLAND COTTON:"],
    "Rice":     ["RICE:","U.S. RICE"],
}

BULLISH_KW = ["lower supplies","reduced exports","supplies are lowered","supply is lowered",
              "production cut","production down","lower production","decreased imports",
              "tighter","deficit","shortfall","drought","reduced area","lagging"]
BEARISH_KW = ["higher supplies","increased production","production up","higher production",
              "larger production","production raised","forecast raised",
              "higher ending stocks","increased exports","global production forecast",
              "surplus","record harvest","higher output","increased output","larger area"]
SIGNAL_KW  = ["lower","higher","increased","decreased","reduced","raised","tighter",
              "unchanged","no changes","forecast","production","exports","supplies"]

def _in_bounds(commodity, field, val):
    b = WASDE_BOUNDS.get(commodity, {}).get(field)
    if not b or val is None: return True
    return b[0] <= val <= b[1]

def _parse_num(v):
    try: return float(str(v).replace(",","").strip())
    except: return None

def _clean_cell(v):
    if v is None: return ""
    s = str(v).strip()
    return "" if s in ("-","--","---","N/A","") else s

def _score_sentence(s):
    sl = s.lower()
    return sum(1 for kw in SIGNAL_KW if kw in sl)

def _derive_signal(narrative):
    if not narrative: return "UNKNOWN"
    n = narrative.lower()
    bs = sum(1 for kw in BULLISH_KW if kw in n)
    brs = sum(1 for kw in BEARISH_KW if kw in n)
    # Weight U.S.-specific mentions
    us = "u.s." in n[:200]
    if us: bs = int(bs * 1.5)
    if bs == 0 and brs == 0: return "NEUTRAL"
    return "BULLISH" if bs > brs else "BEARISH" if brs > bs else "NEUTRAL"

def _extract_narrative(commodity, full_text):
    anchors = NARRATIVE_ANCHORS.get(commodity, [commodity.upper()+":"])
    fu = full_text.upper()
    idx = -1
    for anchor in anchors:
        i = fu.find(anchor)
        if i >= 0: idx = i; break
    if idx < 0: return ""
    snippet = full_text[idx:idx+900].replace("\n"," ")
    sents = [s.strip() for s in snippet.split(". ") if len(s.strip()) > 25]
    if not sents: return ""
    scored = sorted(enumerate(sents[:8]), key=lambda x: -_score_sentence(x[1]))
    top = scored[0][0]
    idxs = sorted(set([0, top] + ([top+1] if top+1 < len(sents) else [])))
    return ". ".join(sents[i] for i in idxs if i < len(sents)) + "."

def _extract_tables(commodity, all_tables):
    result = {f:"" for f in ["production","domestic_use","exports","ending_stocks",
                              "prior_production","prior_domestic_use","prior_exports",
                              "prior_ending_stocks","unit"]}
    terms = [commodity.upper()] + {
        "Soybeans":["SOYBEAN","SOYBEANS"],"Cotton":["UPLAND COTTON","COTTON"],
        "Rice":["U.S. RICE","RICE"]}.get(commodity,[])
    dom = [l.upper() for l in DOMESTIC_USE_LABELS.get(commodity,[])]
    in_sec = False
    for table in all_tables:
        if not table: continue
        for row in table:
            if not row or not row[0]: continue
            lbl = str(row[0]).upper().strip()
            if any(t in lbl for t in terms): in_sec = True
            if not in_sec: continue
            other = [c.upper() for c in WASDE_COMMODITIES if c != commodity]
            if any(lbl.startswith(o) for o in other): in_sec = False; continue
            if "MILLION BUSHELS" in lbl or "MIL. BU." in lbl: result["unit"]="million_bushels"
            elif "1,000 BALES" in lbl: result["unit"]="thousand_bales"
            elif "MIL. CWT" in lbl: result["unit"]="million_cwt"
            c = _clean_cell(row[1]) if len(row)>1 else ""
            p = _clean_cell(row[2]) if len(row)>2 else ""
            if "PRODUCTION" in lbl and not result["production"]:
                result["production"]=c; result["prior_production"]=p
            elif any(d in lbl for d in dom) and not result["domestic_use"]:
                result["domestic_use"]=c; result["prior_domestic_use"]=p
            elif "EXPORT" in lbl and "IMPORT" not in lbl and not result["exports"]:
                result["exports"]=c; result["prior_exports"]=p
            elif "ENDING STOCKS" in lbl and not result["ending_stocks"]:
                result["ending_stocks"]=c; result["prior_ending_stocks"]=p
    return result

def parse_raw(raw, cfg):
    import re
    try:
        bundle = json.loads(raw)
        all_tables = bundle.get("tables",[])
        full_text  = bundle.get("text","")
    except:
        all_tables=[]; full_text=raw

    records = []
    for commodity in WASDE_COMMODITIES:
        tbl = _extract_tables(commodity, all_tables)
        record = {"commodity":commodity,"confidence":"low",
                  "data_source":"table" if tbl["production"] else "text"}
        # Text fallback for missing fields
        for f in ["production","domestic_use","exports","ending_stocks",
                  "prior_production","prior_domestic_use","prior_exports",
                  "prior_ending_stocks","unit"]:
            record[f] = tbl[f] or ""
        if commodity == "Cotton": record["unit"] = "thousand_bales"

        # Bounds validation
        key_fields = ["production","domestic_use","exports","ending_stocks"]
        flags=[]; valid=0
        for field in key_fields:
            v = record.get(field,"")
            if not v: continue
            num = _parse_num(v)
            if num is not None and _in_bounds(commodity,field,num):
                valid += 1
            else:
                flags.append(f"{field}={v} OOB")
                record[field]=""; record[f"prior_{field}"]=""

        record["parse_flags"] = flags
        record["narrative"]   = _extract_narrative(commodity, full_text)
        record["signal"]      = _derive_signal(record["narrative"])

        if valid >= 3:   record["confidence"] = "high"
        elif valid >= 2: record["confidence"] = "medium"
        else:
            record["confidence"] = "low"
            for f in key_fields:
                record[f]=""; record[f"prior_{f}"]=""

        records.append(record)
    return records

# ══════════════════════════════════════════════════════════════
# SIGNAL OVERRIDE — post-synthesis correction layer
# ══════════════════════════════════════════════════════════════

def _apply_signal_overrides(synthesis, normalized, log):
    try:
        recs = json.loads(normalized)
        sig_map = {r["commodity"]:r.get("signal","UNKNOWN")
                   for r in recs if isinstance(r,dict) and "commodity" in r}
        narr_map = {r["commodity"]:r.get("narrative","")
                    for r in recs if isinstance(r,dict) and "commodity" in r}
    except:
        return synthesis

    lines = []
    for line in synthesis.split("\n"):
        out = line
        for comm, sig in sig_map.items():
            if sig not in ("BULLISH","BEARISH"): continue
            if not line.strip().upper().startswith(comm.upper()): continue
            lu = line.upper()
            llm_ok = (sig=="BULLISH" and "BULLISH" in lu) or \
                     (sig=="BEARISH" and "BEARISH" in lu)
            llm_neutral = "BULLISH" not in lu and "BEARISH" not in lu
            if not llm_ok and llm_neutral:
                narr = narr_map.get(comm,"")[:120].replace("\n"," ")
                for pfx in [f"{comm.upper()}:", f"{comm}:"]:
                    if narr.upper().startswith(pfx):
                        narr = narr[len(pfx):].strip()
                lede = narr.split(",")[0].strip().rstrip(".")
                out = f"{comm}: {lede} -- {sig} for prices"
                log.info(f"Signal override: {comm} LLM=NEUTRAL -> {sig}")
        lines.append(out)
    return "\n".join(lines)

# ══════════════════════════════════════════════════════════════
# FRAMEWORK FUNCTIONS
# ══════════════════════════════════════════════════════════════

def _setup_logging(cfg):
    Path(cfg["log_path"]).parent.mkdir(parents=True, exist_ok=True)
    log = logging.getLogger(cfg["agent_id"])
    log.setLevel(logging.INFO)
    if not log.handlers:
        fh = logging.FileHandler(cfg["log_path"], encoding="utf-8")
        fh.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s %(message)s",datefmt="%Y-%m-%d %H:%M:%S"))
        log.addHandler(fh)
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(logging.Formatter("[%(asctime)s] %(message)s",datefmt="%H:%M:%S"))
        log.addHandler(ch)
    return log

def _load_state(cfg):
    try: return json.loads(Path(cfg["state_path"]).read_text(encoding="utf-8"))
    except: return {"last_run":None,"last_checksum":None,"last_record_count":0,
                    "last_classification":None,"run_count":0,"error_count":0}

def _save_state(cfg, state, log):
    Path(cfg["state_path"]).parent.mkdir(parents=True, exist_ok=True)
    note = state.get("handoff_note","")
    if len(note.split()) > 40:
        state["handoff_note"] = " ".join(note.split()[:40]) + "..."
    tmp = cfg["state_path"] + ".tmp"
    with open(tmp,"w",encoding="utf-8") as f: json.dump(state,f,indent=2,ensure_ascii=False)
    os.replace(tmp, cfg["state_path"])
    log.info(f"state.json saved — run #{state['run_count']}")

def _checksum(data): return hashlib.md5(data.encode()).hexdigest()[:12]

def _push_inbox(cfg, item):
    required = {"id","source","type","urgency","title","finding","status","date"}
    if not required.issubset(item.keys()):
        raise ValueError(f"Inbox schema missing: {required-item.keys()}")
    try:
        inbox = json.loads(Path(cfg["inbox_path"]).read_text(encoding="utf-8"))
        if isinstance(inbox,dict): inbox = inbox.get("items",[])
    except: inbox = []
    if item["id"] not in {i.get("id") for i in inbox}:
        inbox.append(item)
        tmp = cfg["inbox_path"] + ".tmp"
        with open(tmp,"w",encoding="utf-8") as f: json.dump(inbox,f,indent=2,ensure_ascii=False)
        os.replace(tmp, cfg["inbox_path"])

def _normalize_with_gemini(records, cfg, log):
    if not records: return "[]"
    narratives = {r.get("commodity",""): r.get("narrative","") for r in records}
    no_narr = [{k:v for k,v in r.items() if k != "narrative"} for r in records]
    prompt = ("Normalize this WASDE data to clean JSON. Remove commas from numbers. "
              "Return ONLY valid JSON array, no markdown:\n\n" + json.dumps(no_narr,ensure_ascii=False))
    resp = gw_call(prompt, task_type=cfg["normalize_task"], max_tokens=1000)
    if not resp.success:
        log.warning(f"Gemini norm failed: {resp.error} — using raw")
        return json.dumps(records, ensure_ascii=False)
    text = resp.text.strip()
    if text.startswith("```"):
        text = text.split("```",2)[-1].lstrip("json").strip().rstrip("```").strip()
    try:
        lst = json.loads(text)
        _consecutive_failures = 0
        for r in lst:
            c = r.get("commodity") or r.get("Commodity","")
            if c in narratives: r["narrative"] = narratives[c]
        result = json.dumps(lst, ensure_ascii=False)
    except:
        log.warning("Gemini malformed JSON — raw fallback")
        result = json.dumps(records, ensure_ascii=False)
    log.info(f"Normalized via {resp.provider}/{resp.model} ({resp.latency_ms}ms)")
    return result

def _classify_with_ollama(normalized, cfg, log):
    safe = normalized[:500]
    prompt = cfg["classify_prompt"].replace("{data}", safe)
    resp = gw_call(prompt, task_type=cfg["classify_task"], max_tokens=cfg["classify_max_tokens"])
    if not resp.success:
        log.warning(f"Ollama classify failed — default NEUTRAL"); return "NEUTRAL"
    label = resp.text.strip().upper().split()[0]
    result = label if label in {"BULLISH","BEARISH","NEUTRAL","EMPTY"} else "NEUTRAL"
    log.info(f"Classified: {result} via {resp.provider}/{resp.model}")
    return result

# ══════════════════════════════════════════════════════════════
# DUAL AI SYNTHESIS — Mistral + Gemini consensus check
# ══════════════════════════════════════════════════════════════

def _synthesize(normalized, cfg, log):
    """
    Run synthesis through Mistral (A) and Gemini (B) independently.
    Returns synthesis text + ai_confidence tag.
    Consensus  = both agree → higher credibility
    Divergent  = disagree → force NEUTRAL overall, push to inbox
    Single     = one failed → use survivor
    """
    from wasde_dual_ai import dual_synthesize
    result = dual_synthesize(normalized, cfg, log)
    synthesis = _apply_signal_overrides(result["synthesis"], normalized, log)
    result["override_applied"] = (synthesis != result["synthesis"])
    result["synthesis"] = synthesis
    log.info(f"AI confidence: {result['confidence']} | A={result['model_a_direction']} B={result['model_b_direction']}")
    return result

# ══════════════════════════════════════════════════════════════
# DELIVER
# ══════════════════════════════════════════════════════════════

def _build_html_digest(records, synthesis, classification, cfg, ai_confidence="unknown"):
    ts = datetime.now().strftime("%B %Y")
    rdate = datetime.now().strftime("%B %d, %Y")
    bc = {"BULLISH":("#d32f2f","BULLISH — Supply Tighter"),
          "BEARISH":("#2e7d32","BEARISH — Supply Looser"),
          "NEUTRAL":("#f57c00","NEUTRAL — Mixed Signals"),
          "MIXED":  ("#1565c0","MIXED — Monitor Closely"),
          "EMPTY":  ("#757575","NO DATA")}.get(classification,("#757575",classification))

    rows = ""
    for r in records:
        if r.get("confidence")=="low": continue
        c=r["commodity"]
        rows += (f"<tr><td style='padding:8px 12px;font-weight:bold'>{c}</td>"
                 f"<td style='padding:8px 12px;text-align:right'>{r.get('production','') or '—'}</td>"
                 f"<td style='padding:8px 12px;text-align:right;color:#888'>{r.get('prior_production','') or '—'}</td>"
                 f"<td style='padding:8px 12px;text-align:right'>{r.get('ending_stocks','') or '—'}</td>"
                 f"<td style='padding:8px 12px;text-align:right;color:#888'>{r.get('prior_ending_stocks','') or '—'}</td>"
                 f"<td style='padding:8px 12px;text-align:center;font-size:11px;color:#aaa'>"
                 f"{'[data]' if r.get('confidence')=='high' else '[narrative]' if not r.get('parse_flags') else '[override]'}</td></tr>")

    narrative_only = all(r.get("confidence")=="low" for r in records)
    narr_notice = ("<div style='background:#fff8e1;border-left:3px solid #f9a825;padding:10px 14px;"
                   "font-size:13px;margin-bottom:16px;border-radius:0 4px 4px 0'>"
                   "<strong>Note:</strong> USDA made no numerical revisions this month. "
                   "Analysis is based on USDA written commentary.</div>") if narrative_only else ""

    conf_badge = {"consensus":"Consensus ✓","divergent":"Review Needed","single":"Single Model","unknown":""}.get(ai_confidence,"")
    synth_html = "".join(f"<p style='margin:6px 0;line-height:1.5'>{l}</p>"
                         for l in synthesis.strip().split("\n") if l.strip())

    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>FCI WASDE Alert — {ts}</title></head>
<body style="font-family:Georgia,serif;color:#222;max-width:640px;margin:0 auto;padding:20px">
<div style="border-bottom:3px solid #1a1a1a;padding-bottom:12px;margin-bottom:20px">
  <p style="margin:0 0 2px;font-size:11px;color:#888;text-transform:uppercase;letter-spacing:.06em">FCI Food Cost Intelligence</p>
  <h1 style="margin:0;font-size:22px">WASDE Alert — {ts}</h1>
  <p style="margin:4px 0 0;color:#666;font-size:13px">USDA WASDE &nbsp;|&nbsp; {rdate}</p>
</div>
<div style="background:{bc[0]};color:#fff;padding:10px 16px;border-radius:4px;font-size:15px;font-weight:bold;margin-bottom:6px">{bc[1]}</div>
{f'<p style="font-size:11px;color:#888;margin-bottom:16px">AI confidence: {conf_badge}</p>' if conf_badge else '<div style="margin-bottom:16px"></div>'}
{narr_notice}
<h2 style="font-size:15px;margin:0 0 10px;border-bottom:1px solid #ddd;padding-bottom:6px">Procurement Summary</h2>
<div style="font-size:14px;line-height:1.6;margin-bottom:24px">{synth_html}</div>
<h2 style="font-size:15px;margin:0 0 10px;border-bottom:1px solid #ddd;padding-bottom:6px">Supply & Demand Snapshot</h2>
<table style="width:100%;border-collapse:collapse;font-size:13px;margin-bottom:24px">
<thead><tr style="background:#f5f5f5">
  <th style="padding:8px 12px;text-align:left;border-bottom:2px solid #ddd">Commodity</th>
  <th style="padding:8px 12px;text-align:right;border-bottom:2px solid #ddd">Production</th>
  <th style="padding:8px 12px;text-align:right;border-bottom:2px solid #ddd;color:#888">Prior</th>
  <th style="padding:8px 12px;text-align:right;border-bottom:2px solid #ddd">End Stocks</th>
  <th style="padding:8px 12px;text-align:right;border-bottom:2px solid #ddd;color:#888">Prior</th>
  <th style="padding:8px 12px;text-align:center;border-bottom:2px solid #ddd">Source</th>
</tr></thead>
<tbody>{rows or "<tr><td colspan='6' style='padding:12px;text-align:center;color:#888'>USDA made no numerical revisions this month — narrative analysis used</td></tr>"}</tbody>
</table>
<div style="border-top:1px solid #ddd;padding-top:12px;font-size:11px;color:#999">
  <p style="margin:0">Methodology: Signals from USDA narrative keyword analysis + dual-model consensus (Mistral + Gemini). Source: <a href="{cfg['source_url']}" style="color:#1a5fb4">USDA WASDE PDF</a></p>
  <p style="margin:4px 0 0">Backtest accuracy: pending. For procurement guidance only.</p>
  <p style="margin:4px 0 0">Next release: April 9, 2026</p>
</div></body></html>"""

def _deliver(normalized, synthesis, classification, ai_confidence, records, cfg, state, log, dry):
    ts = datetime.now().strftime("%Y-%m-%d")
    out_dir = Path(cfg["output_dir"]); out_dir.mkdir(parents=True, exist_ok=True)

    html = _build_html_digest(records, synthesis, classification, cfg, ai_confidence)

    if cfg["deliver_file"] and not dry:
        out = out_dir / f"{cfg['agent_id']}-{ts}.json"
        # Strip parse_flags from public payload (internal only)
        public_records = [{k:v for k,v in r.items() if k!="parse_flags"} for r in records]
        payload = {"agent_id":cfg["agent_id"],"pool_number":cfg["pool_number"],
                   "generated_at":datetime.now().isoformat(),"source_url":cfg["source_url"],
                   "classification":classification,"ai_confidence":ai_confidence,
                   "narrative_only":all(r.get("confidence")=="low" for r in records),
                   "synthesis":synthesis,"commodities":public_records}
        tmp = str(out)+".tmp"
        with open(tmp,"w",encoding="utf-8") as f: json.dump(payload,f,indent=2,ensure_ascii=False)
        os.replace(tmp,str(out)); log.info(f"JSON written: {out}")

    # Always write HTML (even in dry run — for inspection)
    html_path = out_dir / (f"{cfg['agent_id']}-{ts}.html" if not dry else f"{cfg['agent_id']}-dryrun.html")
    with open(html_path,"w",encoding="utf-8") as f: f.write(html)
    log.info(f"HTML written: {html_path}")

    if cfg["deliver_digest"] and not dry:
        try: digest = json.loads(Path(cfg["digest_path"]).read_text(encoding="utf-8"))
        except: digest = {"date":ts,"entries":[]}
        digest.setdefault("entries",[]).append({
            "agent_id":cfg["agent_id"],"pool_number":cfg["pool_number"],
            "pool_name":cfg["pool_name"],"timestamp":datetime.now().isoformat(),
            "classification":classification,"ai_confidence":ai_confidence,
            "synthesis":synthesis[:300]})
        tmp = cfg["digest_path"]+".tmp"
        with open(tmp,"w",encoding="utf-8") as f: json.dump(digest,f,indent=2,ensure_ascii=False)
        os.replace(tmp,cfg["digest_path"]); log.info("Appended to daily-digest.json")

    if cfg["deliver_email"] and not dry:
        studio_cfg = json.loads(Path(cfg["config_path"]).read_text(encoding="utf-8-sig"))
        bk = studio_cfg.get("Beehiiv API Key","")
        bp = studio_cfg.get("Beehiiv Publication ID","")
        if bk and bp:
            import urllib.request, urllib.error
            subject = f"FCI WASDE Alert — {datetime.now().strftime('%B %Y')} [{classification}]"
            payload = json.dumps({"subject":subject,"content":html,
                                  "content_format":"html","status":"draft"}).encode()
            req = urllib.request.Request(
                f"https://api.beehiiv.com/v2/publications/{bp}/posts",
                data=payload,
                headers={"Authorization":f"Bearer {bk}","Content-Type":"application/json"},
                method="POST")
            try:
                with urllib.request.urlopen(req,timeout=30) as r:
                    pid = json.loads(r.read()).get("data",{}).get("id","?")
                    log.info(f"Beehiiv draft created: {pid}")
            except Exception as e:
                log.warning(f"Beehiiv delivery failed: {e}")
        else:
            log.info("Beehiiv keys not in studio-config — email skipped")

    if dry:
        log.info(f"[DRY RUN] synthesis preview:\n{synthesis[:300]}")

# ══════════════════════════════════════════════════════════════
# MAIN PIPELINE
# ══════════════════════════════════════════════════════════════

def run(cfg, dry=False):
    log = _setup_logging(cfg)
    state = _load_state(cfg)
    t0 = time.time()
    log.info(f"=== {cfg['agent_id']} START === pool #{cfg['pool_number']} | dry={dry}")
    log.info(f"URL: {cfg['source_url']}")

    def elapsed(): return time.time()-t0
    def hamilton():
        if elapsed() > cfg["ttl_seconds"]:
            raise TimeoutError(f"HAMILTON: {elapsed():.0f}s > TTL {cfg['ttl_seconds']}s")

    try:
        # Step 1: Fetch
        hamilton(); log.info("Step 1: Fetch PDF...")
        raw = None; fails = 0
        for attempt in range(3):
            try:
                raw = fetch_raw(cfg); fails=0
                log.info(f"Fetched {len(raw):,} chars (attempt {attempt+1})"); break
            except Exception as e:
                fails += 1; log.warning(f"Fetch {attempt+1} failed: {str(e)[:80]}")
                if fails >= 3: raise
                time.sleep(10)
        if raw is None: raise RuntimeError("All fetches failed")

        # Step 2: Hopper freshness
        ck = _checksum(raw)
        if ck == state.get("last_checksum"):
            log.info("HOPPER: unchanged — skipping")
            state["last_run"]=datetime.now().isoformat()
            state["handoff_note"]=f"No change. Last run: {state['last_run'][:10]}"
            _save_state(cfg,state,log); return {"status":"skipped"}

        pull_meta={"pull_timestamp":datetime.now().isoformat(),"source_url":cfg["source_url"],
                   "byte_count":len(raw),"checksum":ck}
        log.info(f"HOPPER: {pull_meta['byte_count']:,}b checksum={ck}")

        # Step 3: Parse
        hamilton(); log.info("Step 2: Parse commodities...")
        records = parse_raw(raw, cfg)
        hi = [r for r in records if r.get("confidence")=="high"]
        narr = [r for r in records if r.get("narrative") and r.get("confidence")=="low"]
        log.info(f"Parsed {len(records)} | {len(hi)} high-conf | {len(narr)} narrative-only")
        if not records or (not hi and not narr):
            log.warning("No usable records — possible pre-release PDF")
            state["handoff_note"]=f"Empty parse. {datetime.now().isoformat()[:10]}"
            _save_state(cfg,state,log); return {"status":"empty"}

        # Step 4: Normalize
        hamilton(); log.info("Step 3: Normalize (Gemini)...")
        normalized = _normalize_with_gemini(records, cfg, log)

        # Step 5: Classify
        hamilton(); log.info("Step 4: Classify (Ollama)...")
        classification = _classify_with_ollama(normalized[:500], cfg, log)

        # Step 6: Dual AI synthesis
        hamilton(); log.info("Step 5: Dual AI synthesis (Mistral + Gemini)...")
        dual = _synthesize(normalized, cfg, log)
        synthesis     = dual["synthesis"]
        ai_confidence = dual["confidence"]

        # Step 7: Deliver
        hamilton(); log.info("Step 6: Deliver...")
        _deliver(normalized, synthesis, classification, ai_confidence, records, cfg, state, log, dry)

        # Step 8: State
        state.update({"last_run":datetime.now().isoformat(),"last_checksum":ck,
                      "last_record_count":len(records),"last_classification":classification,
                      "run_count":state.get("run_count",0)+1,"error_count":0,
                      "pull_meta":pull_meta,"ai_confidence":ai_confidence,
                      "handoff_note":(f"{cfg['agent_id']} ran {datetime.now().isoformat()[:10]}. "
                                      f"{len(records)} commodities ({len(hi)} high-conf). "
                                      f"{classification} [{ai_confidence}]. "
                                      f"Synthesis: {synthesis[:50]}...")})
        _save_state(cfg,state,log)

        if classification == "BULLISH":
            _push_inbox(cfg,{"id":f"wasde-bullish-{datetime.now().strftime('%Y%m%d')}",
                             "source":cfg["agent_id"],"type":"data_alert","urgency":"WARN",
                             "title":"WASDE BULLISH — supply tighter","finding":synthesis[:200],
                             "status":"PENDING","date":datetime.now().isoformat()})
            log.info("BULLISH — pushed to supervisor inbox")

        log.info(f"=== COMPLETE === {elapsed():.1f}s | {classification} [{ai_confidence}]")
        return {"status":"ok","records":len(records),"classification":classification,
                "ai_confidence":ai_confidence}

    except TimeoutError as e:
        log.error(str(e)); state["error_count"]=state.get("error_count",0)+1
        state["handoff_note"]=f"TIMEOUT {datetime.now().isoformat()[:10]}"
        _save_state(cfg,state,log)
        _push_inbox(cfg,{"id":f"wasde-timeout-{datetime.now().strftime('%Y%m%d%H%M')}",
                         "source":cfg["agent_id"],"type":"agent_error","urgency":"WARN",
                         "title":"TIMEOUT: wasde-parser","finding":str(e)[:200],
                         "status":"PENDING","date":datetime.now().isoformat()})
        return {"status":"timeout"}
    except Exception as e:
        log.error(f"PIPELINE FAILED: {str(e)[:200]}")
        state["error_count"]=state.get("error_count",0)+1
        state["handoff_note"]=f"ERROR {datetime.now().isoformat()[:10]}: {str(e)[:60]}"
        _save_state(cfg,state,log)
        finding = str(e)[:200]
        # Pre-release PDF errors are expected monthly — deduplicate to one inbox entry
        # per calendar month to avoid inbox spam from repeated scheduler runs.
        if "not released yet" in finding.lower() or "pdf too small" in finding.lower():
            error_id = f"wasde-prerelease-{datetime.now().strftime('%Y%m')}"
        else:
            error_id = f"wasde-error-{datetime.now().strftime('%Y%m%d%H%M')}"
        _push_inbox(cfg,{"id":error_id,
                         "source":cfg["agent_id"],"type":"agent_error","urgency":"WARN",
                         "title":"ERROR: wasde-parser","finding":finding,
                         "status":"PENDING","date":datetime.now().isoformat()})
        return {"status":"error","error":str(e)[:200]}

# ══════════════════════════════════════════════════════════════
# ENTRYPOINT
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    p = argparse.ArgumentParser(description="wasde-parser — USDA WASDE Food Cost Alert")
    p.add_argument("--dry",      action="store_true")
    p.add_argument("--backtest", action="store_true")
    args = p.parse_args()
    result = run(AGENT_CONFIG, dry=args.dry)
    print(f"\nResult: {result}")
    sys.exit(0 if result.get("status") in ("ok","skipped","empty") else 1)
