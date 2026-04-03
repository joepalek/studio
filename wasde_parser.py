"""
wasde_parser.py
===============
Tier 1 pipeline agent — USDA WASDE Monthly Food Cost Alert
Pool #56 | Cadence: monthly | Delivery: email-ready HTML digest

Built from tier1_pipeline_template.py following Gall's Law.
Only CONFIG, fetch_raw(), parse_raw(), and HTML delivery are pool-specific.
All framework rules (Bezos, Hamilton, Hopper, Codd, Shannon) inherited.

SOURCE: USDA World Agricultural Supply and Demand Estimates (WASDE)
URL pattern: https://www.usda.gov/oce/commodity/wasde/wasde{MM}{YY}.pdf
Parser: pdfplumber

SYNTHESIS: routes to Mistral Large via ai_gateway (reasoning task_type)
NOTE: Anthropic credits currently depleted — gateway falls back automatically.

CLASSIFY OPTIONS: BULLISH | BEARISH | NEUTRAL | EMPTY
  (non-standard — overrides base template valid set)

KNOWN FAILURE MODES FIXED IN SYNTHESIS PROMPT (from Sim 1):
  1. Seasonal reversal: early harvest = MORE supply = BEARISH (not bullish)
  2. La Nina causal chain: dry = drought = supply CUT = BULLISH for price
  3. Production vs demand: production cut = tighter = BULLISH
  4. Ambiguous signal: output NEUTRAL not a forced directional call

USAGE:
  python wasde_parser.py           # run once
  python wasde_parser.py --dry     # dry run, no delivery
  python wasde_parser.py --backtest # run synthesis validator (12 months)

TASK SCHEDULER: \\Studio\\wasde-parser | 02:15 daily | TTL 600s
"""

import json, os, sys, time, hashlib, logging, argparse, io
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, "G:/My Drive/Projects/_studio")
from ai_gateway import call as gw_call
import provider_health as ph

# ══════════════════════════════════════════════════════════════════
# CONFIG — pool-specific values only
# ══════════════════════════════════════════════════════════════════

def _build_wasde_url(target_date: datetime = None) -> str:
    """
    Build WASDE PDF URL for a given month.
    Format: wasde{MM}{YY}.pdf
    Default: current month.
    """
    d = target_date or datetime.now()
    month = d.strftime("%m")   # 04
    year  = d.strftime("%y")   # 26
    return f"https://www.usda.gov/oce/commodity/wasde/wasde{month}{year}.pdf"


AGENT_CONFIG = {
    # Identity
    "agent_id":       "wasde-parser",
    "pool_name":      "USDA WASDE Food Cost Alert",
    "pool_number":    56,

    # Timing
    "ttl_seconds":       600,       # Hamilton: PDF download can be slow
    "source_cadence":    "monthly",
    "stale_after_hours": 720,       # Hopper: 30 days

    # Data source
    "source_url":    _build_wasde_url(),   # resolved at import time
    "source_format": "pdf",

    # AI routing
    "normalize_task":  "batch",      # Gemini Free — bulk normalization
    "synthesize_task": "reasoning",  # Mistral Large fallback (Claude depleted)
    "classify_task":   "local",      # Ollama — local classification

    # Synthesis prompt — failure modes from Sim 1 explicitly addressed
    "synthesis_prompt": (
        "You are a food procurement analyst. "
        "Your audience is food buyers who need to know if commodity prices will rise or fall.\n\n"
        "WASDE data this month:\n{data}\n\n"
        "Each commodity record has numeric fields (production, ending_stocks, exports, domestic_use) "
        "AND a 'narrative' field with the USDA prose summary for that commodity.\n"
        "If numeric fields are blank or empty, use the narrative field to determine direction.\n"
        "If narrative says 'no changes this month' — that means NEUTRAL, supply unchanged.\n\n"
        "For each commodity (Wheat, Corn, Soybeans, Cotton, Rice), write ONE sentence:\n"
        "  Format: 'CommodityName: [what changed] -- [BULLISH/BEARISH/NEUTRAL] for prices'\n\n"
        "CRITICAL RULES -- you failed these in simulation:\n"
        "1. Early harvest = MORE supply = BEARISH (lower prices). Not bullish.\n"
        "2. La Nina = South American drought = supply CUT = BULLISH (higher prices).\n"
        "3. Production cut = tighter supply = BULLISH for prices.\n"
        "4. If signal is ambiguous or data is missing, write NEUTRAL -- never force a direction.\n"
        "5. Confidence < 70% on any commodity = write NEUTRAL for that commodity.\n"
        "6. 'No changes this month' = NEUTRAL -- do not invent a direction.\n"
        "7. 'Lower supplies' OR 'reduced exports' in the narrative = BULLISH even if ending stocks are steady.\n"
        "8. Use the 'narrative' field for each commodity -- it contains the actual USDA text. Read it carefully.\n"
        "9. Each record has a 'signal' field pre-computed from keyword analysis: BULLISH/BEARISH/NEUTRAL/UNKNOWN.\n"
        "   Trust 'signal' when it is BULLISH or BEARISH. Override only if narrative clearly contradicts it.\n"
        "   UNKNOWN means insufficient data — default to NEUTRAL for that commodity.\n\n"
        "After the 5 commodity lines, add one summary line:\n"
        "  'Overall: [BULLISH/BEARISH/NEUTRAL/MIXED] -- [one sentence procurement implication]'\n\n"
        "Return ONLY these 6 lines. No preamble, no explanation."
    ),
    "synthesize_max_tokens": 400,

    # Classification prompt — WASDE-specific labels (overrides template default)
    "classify_prompt": (
        "Classify this WASDE commodity data as one of: "
        "[BULLISH, BEARISH, NEUTRAL, EMPTY]. "
        "BULLISH = net supply tighter than last month across majority of commodities. "
        "BEARISH = net supply looser across majority of commodities. "
        "NEUTRAL = mixed or ambiguous signals. "
        "EMPTY = no usable data extracted. "
        "Return ONLY the single label, nothing else.\n\nData: {data}"
    ),
    "classify_max_tokens": 10,

    # Delivery
    "deliver_email":   True,    # HTML digest — stub until Beehiiv key in studio-config
    "deliver_webhook": False,
    "deliver_file":    True,
    "deliver_digest":  True,

    # Paths
    "output_dir":   "G:/My Drive/Projects/_studio/data/wasde",
    "state_path":   "G:/My Drive/Projects/_studio/data/wasde/state.json",
    "log_path":     "G:/My Drive/Projects/_studio/logs/wasde-parser.log",
    "digest_path":  "G:/My Drive/Projects/_studio/daily-digest.json",
    "inbox_path":   "G:/My Drive/Projects/_studio/supervisor-inbox.json",
    "config_path":  "G:/My Drive/Projects/_studio/studio-config.json",
}

# Commodities to extract — in order of appearance in WASDE
WASDE_COMMODITIES = ["Wheat", "Corn", "Soybeans", "Cotton", "Rice"]

# Fields to extract per commodity — Codd: blank over wrong
WASDE_FIELDS = [
    "production",
    "domestic_use",
    "exports",
    "ending_stocks",
]

# ══════════════════════════════════════════════════════════════════
# POOL-SPECIFIC: fetch_raw() and parse_raw()
# ══════════════════════════════════════════════════════════════════

def fetch_raw(cfg: dict) -> str:
    """
    Download WASDE PDF and extract full text via pdfplumber.
    Returns raw text string (all pages concatenated).
    Raises on failure — framework handles retries (Bezos Rule).
    """
    try:
        import pdfplumber
    except ImportError:
        raise RuntimeError(
            "pdfplumber not installed. Run: pip install pdfplumber"
        )
    import urllib.request

    url = cfg["source_url"]
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "StudioAgent/1.0 (research; usda-wasde-monitor)",
            "Accept": "application/pdf",
        }
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        pdf_bytes = r.read()

    if len(pdf_bytes) < 1000:
        raise RuntimeError(f"PDF too small ({len(pdf_bytes)} bytes) — likely not released yet")

    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        # Extract both tables and text per page — tables preserve column alignment
        all_tables = []
        all_text_pages = []
        for page in pdf.pages:
            text = page.extract_text() or ""
            all_text_pages.append(text)
            tbls = page.extract_tables()
            if tbls:
                all_tables.extend(tbls)

    full_text = "\n\n--- PAGE BREAK ---\n\n".join(all_text_pages)

    if not full_text.strip() and not all_tables:
        raise RuntimeError("pdfplumber extracted no content — PDF may be scanned/image-based")

    # Return as JSON bundle: both tables and raw text available to parse_raw()
    import json as _json
    return _json.dumps({
        "tables": all_tables,
        "text":   full_text
    }, ensure_ascii=False)


def parse_raw(raw: str, cfg: dict) -> list[dict]:
    """
    Extract commodity supply/demand values from WASDE PDF content.

    FIX 1: Uses extract_table() column data (preserves alignment) with text fallback.
    FIX 2: Plausibility bounds validation — values outside WASDE_BOUNDS blanked (Codd).
    FIX 3: Commodity-specific domestic use label variants.
    FIX 4: Confidence requires bounds pass, not just field count.

    WASDE column structure: [Row label | Current estimate | Prior month | Prior year]
    Cotton unit: thousand bales. All grains: million bushels. Rice: million cwt.
    """
    import re, json as _json

    # Parse the JSON bundle from fetch_raw()
    try:
        bundle = _json.loads(raw)
        all_tables = bundle.get("tables", [])
        full_text  = bundle.get("text", "")
    except Exception:
        all_tables = []
        full_text  = raw

    # ── PLAUSIBILITY BOUNDS (Fix 2) ──────────────────────────────
    # U.S. supply figures — reject values outside these ranges
    # Sources: USDA historical 2015-2025. Units match commodity unit field.
    WASDE_BOUNDS = {
        "Wheat":    {"production": (1200, 2800),  "ending_stocks": (300, 1200),
                     "exports":    (700, 1400),    "domestic_use":  (900, 1600)},
        "Corn":     {"production": (10000, 16000), "ending_stocks": (700, 2500),
                     "exports":    (1500, 3000),   "domestic_use":  (8000, 13000)},
        "Soybeans": {"production": (3000, 5000),   "ending_stocks": (100, 1000),
                     "exports":    (1500, 2500),   "domestic_use":  (1800, 2800)},
        "Cotton":   {"production": (10000, 22000), "ending_stocks": (3000, 10000),
                     "exports":    (8000, 18000),  "domestic_use":  (2000, 5000)},
        "Rice":     {"production": (150, 280),     "ending_stocks": (20, 80),
                     "exports":    (50, 130),      "domestic_use":  (100, 200)},
    }

    def parse_num(val) -> float:
        """Convert string number with commas to float. Returns None if unparseable."""
        if val is None:
            return None
        try:
            return float(str(val).replace(",", "").strip())
        except Exception:
            return None

    def in_bounds(commodity: str, field: str, val: float) -> bool:
        """Codd: return False if value outside known USDA range."""
        bounds = WASDE_BOUNDS.get(commodity, {}).get(field)
        if bounds is None or val is None:
            return True  # no bounds defined — pass through
        lo, hi = bounds
        return lo <= val <= hi

    def clean_cell(val) -> str:
        """Strip whitespace and dashes from table cells."""
        if val is None:
            return ""
        s = str(val).strip()
        return "" if s in ("-", "--", "---", "N/A", "") else s

    # ── DOMESTIC USE LABEL VARIANTS (Fix 3) ─────────────────────
    DOMESTIC_USE_LABELS = {
        "Wheat":    ["DOMESTIC USE", "TOTAL DOMESTIC USE", "FOOD USE",
                     "FOOD, SEED & IND.", "FOOD, SEED & INDUSTRIAL"],
        "Corn":     ["DOMESTIC USE", "TOTAL DOMESTIC USE", "FOOD, SEED & IND.",
                     "FOOD/SEED/INDUSTRIAL", "FEED & RESIDUAL"],
        "Soybeans": ["DOMESTIC USE", "TOTAL DOMESTIC USE", "CRUSHINGS",
                     "CRUSH", "FOOD, SEED & IND."],
        "Cotton":   ["DOMESTIC USE", "TOTAL DOMESTIC USE", "MILL USE",
                     "DOMESTIC MILL USE"],
        "Rice":     ["DOMESTIC USE", "TOTAL DOMESTIC USE", "FOOD USE",
                     "DOMESTIC FOOD USE"],
    }

    # ── TABLE-BASED EXTRACTION (Fix 1) ──────────────────────────
    def extract_from_tables(commodity: str) -> dict:
        """
        Search all extracted tables for a commodity section.
        WASDE tables: col 0 = row label, col 1 = current, col 2 = prior month.
        Returns partial record dict (empty strings if not found).
        """
        result = {f: "" for f in ["production","domestic_use","exports",
                                   "ending_stocks","prior_production",
                                   "prior_domestic_use","prior_exports",
                                   "prior_ending_stocks","unit"]}

        search_name = commodity.upper()
        alt_map = {
            "Soybeans": ["SOYBEAN","SOYBEANS"],
            "Cotton":   ["UPLAND COTTON","ALL COTTON","COTTON"],
            "Rice":     ["U.S. RICE","RICE","MILLED RICE"],
        }
        search_terms = [search_name] + [a.upper() for a in alt_map.get(commodity, [])]

        dom_labels = [l.upper() for l in DOMESTIC_USE_LABELS.get(commodity, [])]

        in_section = False
        for table in all_tables:
            if not table:
                continue
            for row in table:
                if not row or not row[0]:
                    continue
                label = str(row[0]).upper().strip()

                # Detect section header
                if any(t in label for t in search_terms):
                    in_section = True

                if not in_section:
                    continue

                # Stop if we've hit the next major commodity section
                if in_section and label and label != search_name:
                    other = [c.upper() for c in WASDE_COMMODITIES if c != commodity]
                    if any(label.startswith(o) for o in other):
                        in_section = False
                        continue

                # Unit detection
                if "MILLION BUSHELS" in label or "MIL. BU." in label:
                    result["unit"] = "million_bushels"
                elif "1,000 BALES" in label or "THOUSAND BALES" in label:
                    result["unit"] = "thousand_bales"
                elif "1,000 MT" in label or "METRIC TONS" in label:
                    result["unit"] = "thousand_mt"
                elif "MIL. CWT" in label or "MILLION CWT" in label:
                    result["unit"] = "million_cwt"

                curr  = clean_cell(row[1]) if len(row) > 1 else ""
                prior = clean_cell(row[2]) if len(row) > 2 else ""

                if "PRODUCTION" in label and not result["production"]:
                    result["production"] = curr
                    result["prior_production"] = prior

                elif any(dl in label for dl in dom_labels) and not result["domestic_use"]:
                    result["domestic_use"] = curr
                    result["prior_domestic_use"] = prior

                elif "EXPORT" in label and "IMPORT" not in label and not result["exports"]:
                    result["exports"] = curr
                    result["prior_exports"] = prior

                elif "ENDING STOCKS" in label and not result["ending_stocks"]:
                    result["ending_stocks"] = curr
                    result["prior_ending_stocks"] = prior

        return result

    # ── TEXT FALLBACK (for PDFs where tables don't extract cleanly) ──
    def extract_from_text(commodity: str) -> dict:
        """Fallback: scan linearized text. Less reliable but better than nothing."""
        result = {f: "" for f in ["production","domestic_use","exports",
                                   "ending_stocks","prior_production",
                                   "prior_domestic_use","prior_exports",
                                   "prior_ending_stocks","unit"]}
        raw_upper = full_text.upper()
        search_name = commodity.upper()
        alt_map = {
            "Soybeans": ["SOYBEAN", "SOY BEANS"],
            "Cotton":   ["UPLAND COTTON", "ALL COTTON"],
            "Rice":     ["U.S. RICE", "RICE, MILLED"],
        }
        section_start = raw_upper.find(search_name)
        if section_start == -1:
            for alt in alt_map.get(commodity, []):
                section_start = raw_upper.find(alt)
                if section_start != -1:
                    break
        if section_start == -1:
            return result

        section_text = full_text[section_start:section_start + 6000]
        section_upper = section_text.upper()

        if "MILLION BUSHELS" in section_upper or "MIL. BU." in section_upper:
            result["unit"] = "million_bushels"
        elif "1,000 BALES" in section_upper:
            result["unit"] = "thousand_bales"
        elif "MIL. CWT" in section_upper:
            result["unit"] = "million_cwt"

        dom_labels = DOMESTIC_USE_LABELS.get(commodity, ["DOMESTIC USE"])

        def two_nums(line):
            matches = re.findall(r"\b\d{1,5}(?:,\d{3})*(?:\.\d+)?\b", line)
            filtered = [m for m in matches
                        if not re.match(r"^(?:19|20)\d{2}$", m.replace(",",""))]
            return (filtered[0], filtered[1]) if len(filtered) >= 2 else \
                   (filtered[0], "") if len(filtered) == 1 else ("", "")

        for line in section_text.split("\n"):
            lu = line.upper().strip()
            if "PRODUCTION" in lu and not result["production"]:
                c, p = two_nums(line)
                result["production"] = c; result["prior_production"] = p
            elif any(dl in lu for dl in [d.upper() for d in dom_labels]) \
                    and not result["domestic_use"]:
                c, p = two_nums(line)
                result["domestic_use"] = c; result["prior_domestic_use"] = p
            elif "EXPORT" in lu and "IMPORT" not in lu and not result["exports"]:
                c, p = two_nums(line)
                result["exports"] = c; result["prior_exports"] = p
            elif "ENDING STOCKS" in lu and not result["ending_stocks"]:
                c, p = two_nums(line)
                result["ending_stocks"] = c; result["prior_ending_stocks"] = p

        return result

    # ── NARRATIVE EXTRACTION (no-change months) ─────────────────
    # Some WASDE releases have no updated tables — only prose summaries.
    # Extract the narrative paragraph per commodity for synthesis input.
    # Keywords that indicate a supply-direction signal — used to score sentences
    SIGNAL_KEYWORDS = [
        "lower", "higher", "increased", "decreased", "reduced", "raised",
        "tighter", "looser", "cut", "up", "down", "decline", "surge",
        "shortage", "surplus", "unchanged", "no changes", "forecast",
        "production", "ending stocks", "exports", "supplies", "imports",
    ]

    def score_sentence(sentence: str) -> int:
        """Score a sentence by number of supply-direction signal keywords."""
        s = sentence.lower()
        return sum(1 for kw in SIGNAL_KEYWORDS if kw in s)

    def extract_narrative(commodity: str) -> str:
        search_terms = [commodity.upper()]
        alt_map = {
            "Soybeans": ["SOYBEANS", "SOYBEAN OIL", "SOYBEAN MEAL", "SOYBEAN"],
            "Cotton":   ["UPLAND COTTON", "ALL COTTON", "COTTON"],
            "Rice":     ["U.S. RICE", "RICE"],
        }
        for alt in alt_map.get(commodity, []):
            search_terms.append(alt.upper())

        full_upper = full_text.upper()

        # Fix 1 — Soybeans: skip first 5,000 chars to avoid table of contents matches
        toc_skip = 5000 if commodity == "Soybeans" else 0

    def extract_narrative(commodity: str) -> str:
        """
        Extract commodity narrative using precise WASDE section headers.
        WASDE uses specific section labels — match these exactly to avoid
        TOC hits, cross-commodity bleed, and word-fragment matches (RICE in PRICE).
        """
        # Precise section header anchors per commodity (from wasde0326 position analysis)
        # Format: list of (search_string, is_exact_header) tuples — try in order
        anchor_map = {
            "Wheat":    ["WHEAT:", "U.S. WHEAT"],
            "Corn":     ["CORN:", "U.S. CORN", "FEED GRAINS:"],
            "Soybeans": ["OILSEEDS:", "U.S. 2025/26 SOYBEAN", "SOYBEANS:"],
            "Cotton":   ["COTTON:", "UPLAND COTTON:"],
            "Rice":     ["RICE:", "U.S. RICE"],
        }
        anchors = anchor_map.get(commodity, [commodity.upper() + ":"])
        full_upper = full_text.upper()

        best_idx = -1
        for anchor in anchors:
            idx = full_upper.find(anchor)
            if idx >= 0:
                best_idx = idx
                break

        if best_idx == -1:
            return ""

        # Extract window and split into sentences
        snippet = full_text[best_idx:best_idx + 900].replace("\n", " ")
        raw_sentences = snippet.split(". ")
        sentences = [s.strip() for s in raw_sentences if len(s.strip()) > 25]

        if not sentences:
            return ""

        # Score sentences — pick top signal sentence + include lede (sentence 0)
        scored = [(score_sentence(s), i, s) for i, s in enumerate(sentences[:8])]
        scored_sorted = sorted(scored, key=lambda x: (-x[0], x[1]))

        top_idx = scored_sorted[0][1]
        # Always return sentences 0 (lede) and top-scored, plus next for context
        selected_indices = sorted(set([0, top_idx]))
        # Add one more sentence after the top for context
        if top_idx + 1 < len(sentences):
            selected_indices.append(top_idx + 1)
        selected_indices = sorted(set(selected_indices))

        selected = [sentences[i] for i in selected_indices if i < len(sentences)]
        return ". ".join(selected) + "."

    def _derive_signal(narrative: str) -> str:
        """
        Pre-compute directional signal from narrative keywords.
        Returns BULLISH, BEARISH, NEUTRAL, or UNKNOWN.
        Removes ambiguity from LLM synthesis on narrative-only months.
        Codd: UNKNOWN rather than a guess when signals conflict or are absent.
        """
        if not narrative:
            return "UNKNOWN"

        n = narrative.lower()

        # No-change months — explicit USDA language
        no_change_phrases = [
            "no changes this month", "no changes to the", "unchanged relative to last month",
            "outlook is unchanged", "no change", "balance sheet is unchanged"
        ]
        if any(p in n for p in no_change_phrases):
            # Check if there's also a global signal in the same narrative
            pass  # fall through to signal scoring below

        # Bullish signals — supply tighter, prices should rise
        bullish_keywords = [
            "lower supplies", "reduced exports", "supply is lowered", "supplies are lowered",
            "production cut", "production is down", "production down", "lower production",
            "decreased imports", "tighter", "deficit", "shortfall", "drought",
            "reduced area", "lower area", "lagging", "below last year"
        ]
        # Bearish signals — supply looser, prices should fall
        bearish_keywords = [
            "higher supplies", "increased production", "production is up", "production up",
            "higher production", "larger production", "production raised", "forecast raised",
            "higher ending stocks", "larger ending stocks", "increased exports",
            "global production forecast", "surplus", "record pace", "record harvest",
            "higher output", "increased output", "larger area"
        ]

        bullish_score = sum(1 for kw in bullish_keywords if kw in n)
        bearish_score = sum(1 for kw in bearish_keywords if kw in n)

        # U.S.-specific signals outweigh global signals — weight them
        us_bullish = sum(2 for kw in bullish_keywords
                         if kw in n and any(
                             f"u.s. {kw}" in n or f"u.s. rice" in n or "u.s." in n[:200]
                             for _ in [1]
                         ))
        us_bearish = sum(2 for kw in bearish_keywords
                         if kw in n and "u.s." in n[:200])

        total_bullish = bullish_score + us_bullish
        total_bearish = bearish_score + us_bearish

        if total_bullish == 0 and total_bearish == 0:
            return "NEUTRAL"
        if total_bullish > total_bearish:
            return "BULLISH"
        if total_bearish > total_bullish:
            return "BEARISH"
        return "NEUTRAL"  # tied = neutral

    # ── ASSEMBLE RECORDS ─────────────────────────────────────────
    records = []
    for commodity in WASDE_COMMODITIES:

        # Try table extraction first; fill gaps from text
        tbl = extract_from_tables(commodity)
        txt = extract_from_text(commodity)

        record = {"commodity": commodity, "confidence": "low",
                  "data_source": "table" if tbl["production"] else "text"}
        for f in ["production","domestic_use","exports","ending_stocks",
                  "prior_production","prior_domestic_use","prior_exports",
                  "prior_ending_stocks","unit"]:
            record[f] = tbl[f] if tbl[f] else txt[f]

        # Cotton unit override — always thousand_bales
        if commodity == "Cotton":
            record["unit"] = "thousand_bales"

        # ── FIX 2 + FIX 4: Plausibility bounds + confidence ─────
        key_fields = ["production", "domestic_use", "exports", "ending_stocks"]
        fields_present = 0
        fields_valid   = 0
        flags = []

        for field in key_fields:
            raw_val = record.get(field, "")
            if not raw_val:
                continue
            fields_present += 1
            num = parse_num(raw_val)
            if num is not None and in_bounds(commodity, field, num):
                fields_valid += 1
            else:
                flags.append(f"{field}={raw_val} OOB")
                record[field] = ""  # Codd: blank over wrong
                record[f"prior_{field}"] = ""

        record["parse_flags"] = flags  # surfaced in log
        record["narrative"] = extract_narrative(commodity)  # prose fallback for synthesis

        # Pre-compute directional signal from narrative keywords
        # Removes ambiguity for Mistral on narrative-only months
        record["signal"] = _derive_signal(record["narrative"])

        # Fix 4: confidence requires BOTH field count AND plausibility
        if fields_valid >= 3:
            record["confidence"] = "high"
        elif fields_valid >= 2:
            record["confidence"] = "medium"
        else:
            record["confidence"] = "low"
            # Codd: low confidence = blank everything
            for f in key_fields:
                record[f] = ""
                record[f"prior_{f}"] = ""

        records.append(record)

    return records


# ══════════════════════════════════════════════════════════════════
# WASDE-SPECIFIC: HTML digest builder
# ══════════════════════════════════════════════════════════════════

def _beehiiv_delivery(html: str, subject: str, api_key: str, pub_id: str, log) -> dict:
    """
    POST html digest to Beehiiv as a draft post.
    Beehiiv API v2: POST /v2/publications/{pub_id}/posts
    Returns {"ok": True, "post_id": "..."} or {"ok": False, "error": "..."}
    """
    import urllib.request, urllib.error
    url = f"https://api.beehiiv.com/v2/publications/{pub_id}/posts"
    payload = json.dumps({
        "subject":    subject,
        "content":    {"free": {"web": html, "email": html}},
        "status":     "draft",
        "send_at":    None,
        "audience":   "free",
    }).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type":  "application/json",
            "Accept":        "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            post_id = body.get("data", {}).get("id", "unknown")
            log.info(f"EMAIL: Beehiiv draft created — post_id={post_id}")
            return {"ok": True, "post_id": post_id}
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="replace")[:200]
        log.warning(f"EMAIL: Beehiiv HTTP {e.code} — {err}")
        return {"ok": False, "error": f"HTTP {e.code}: {err}"}
    except Exception as e:
        log.warning(f"EMAIL: Beehiiv delivery failed — {e}")
        return {"ok": False, "error": str(e)}


def _build_html_digest(records: list, synthesis: str, classification: str,
                        cfg: dict) -> str:
    """
    Build email-ready HTML digest for Beehiiv delivery.
    Newsletter tier (free subscribers) — plain, mobile-friendly.
    """
    ts = datetime.now().strftime("%B %Y")
    release_date = datetime.now().strftime("%B %d, %Y")

    # Classification badge color
    badge_colors = {
        "BULLISH":  ("#d32f2f", "⚠️ BULLISH — Supply Tighter"),
        "BEARISH":  ("#2e7d32", "✅ BEARISH — Supply Looser"),
        "NEUTRAL":  ("#f57c00", "➡️ NEUTRAL — Mixed Signals"),
        "EMPTY":    ("#757575", "⬜ NO DATA"),
    }
    badge_color, badge_label = badge_colors.get(classification, ("#757575", classification))

    # Build commodity rows
    rows_html = ""
    for r in records:
        if r.get("confidence") == "low":
            continue
        commodity = r["commodity"]
        prod      = r.get("production", "—") or "—"
        prior_p   = r.get("prior_production", "—") or "—"
        stocks    = r.get("ending_stocks", "—") or "—"
        prior_s   = r.get("prior_ending_stocks", "—") or "—"
        unit      = r.get("unit", "").replace("_", " ")
        conf      = r.get("confidence", "low")
        conf_star = {"high": "★★★", "medium": "★★☆", "low": "★☆☆"}.get(conf, "")

        rows_html += f"""
        <tr>
          <td style="padding:8px 12px;font-weight:bold;border-bottom:1px solid #eee">{commodity}</td>
          <td style="padding:8px 12px;text-align:right;border-bottom:1px solid #eee">{prod}</td>
          <td style="padding:8px 12px;text-align:right;border-bottom:1px solid #eee">{prior_p}</td>
          <td style="padding:8px 12px;text-align:right;border-bottom:1px solid #eee">{stocks}</td>
          <td style="padding:8px 12px;text-align:right;border-bottom:1px solid #eee">{prior_s}</td>
          <td style="padding:8px 12px;text-align:center;border-bottom:1px solid #eee;color:#888;font-size:11px">{conf_star}</td>
        </tr>"""

    # Format synthesis lines as paragraphs
    synthesis_lines = [l.strip() for l in synthesis.strip().split("\n") if l.strip()]
    synthesis_html = "".join(f"<p style='margin:6px 0;line-height:1.5'>{l}</p>"
                             for l in synthesis_lines)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>WASDE Food Cost Alert — {ts}</title>
</head>
<body style="font-family:Georgia,serif;color:#222;max-width:640px;margin:0 auto;padding:20px">

  <!-- Header -->
  <div style="border-bottom:3px solid #1a1a1a;padding-bottom:12px;margin-bottom:20px">
    <h1 style="margin:0;font-size:22px;letter-spacing:-0.5px">
      WASDE Food Cost Alert
    </h1>
    <p style="margin:4px 0 0;color:#666;font-size:13px">
      USDA World Agricultural Supply and Demand Estimates &nbsp;|&nbsp; {release_date}
    </p>
  </div>

  <!-- Classification badge -->
  <div style="background:{badge_color};color:#fff;padding:10px 16px;
              border-radius:4px;font-size:15px;font-weight:bold;margin-bottom:24px">
    {badge_label}
  </div>

  <!-- Analyst synthesis -->
  <h2 style="font-size:16px;margin:0 0 10px;border-bottom:1px solid #ddd;padding-bottom:6px">
    Procurement Analyst Summary
  </h2>
  <div style="font-size:14px;line-height:1.6;margin-bottom:24px">
    {synthesis_html}
  </div>

  <!-- Data table -->
  <h2 style="font-size:16px;margin:0 0 10px;border-bottom:1px solid #ddd;padding-bottom:6px">
    Supply &amp; Demand Snapshot
  </h2>
  <table style="width:100%;border-collapse:collapse;font-size:13px;margin-bottom:24px">
    <thead>
      <tr style="background:#f5f5f5">
        <th style="padding:8px 12px;text-align:left;border-bottom:2px solid #ddd">Commodity</th>
        <th style="padding:8px 12px;text-align:right;border-bottom:2px solid #ddd">Production</th>
        <th style="padding:8px 12px;text-align:right;border-bottom:2px solid #ddd">Prior</th>
        <th style="padding:8px 12px;text-align:right;border-bottom:2px solid #ddd">End Stocks</th>
        <th style="padding:8px 12px;text-align:right;border-bottom:2px solid #ddd">Prior</th>
        <th style="padding:8px 12px;text-align:center;border-bottom:2px solid #ddd">Conf</th>
      </tr>
    </thead>
    <tbody>
      {rows_html if rows_html else '<tr><td colspan="6" style="padding:12px;text-align:center;color:#888">No high-confidence data extracted</td></tr>'}
    </tbody>
  </table>

  <!-- Footer -->
  <div style="border-top:1px solid #ddd;padding-top:12px;font-size:11px;color:#999">
    <p style="margin:0">Generated by Studio wasde-parser agent (Pool #56) &nbsp;|&nbsp;
    Data source: USDA WASDE PDF &nbsp;|&nbsp; {cfg['source_url']}</p>
    <p style="margin:4px 0 0">Confidence ratings: ★★★ high ≥3 fields | ★★☆ medium ≥2 fields |
    Not shown: low confidence extractions</p>
    <p style="margin:4px 0 0">⚠️ For procurement guidance only. Verify with USDA source before trading decisions.</p>
  </div>

</body>
</html>"""

    return html


# ══════════════════════════════════════════════════════════════════
# SYNTHESIS VALIDATOR — backtesting harness
# ══════════════════════════════════════════════════════════════════

def _load_studio_config(cfg: dict) -> dict:
    try:
        return json.loads(Path(cfg["config_path"]).read_text(encoding="utf-8"))
    except Exception:
        return {}


def run_backtest(cfg: dict) -> dict:
    """
    Synthesis validator: download last 12 months of WASDE PDFs,
    run synthesis, compare directional call to actual 30-day price movement.

    Target: >88% accuracy, <8% dangerous wrong calls.
    Writes backtest report to data/wasde/backtest-report.json.

    NOTE: Price comparison requires commodity price data source.
    Stub implementation — wire to price feed when available.
    """
    log = _setup_logging(cfg)
    log.info("=== WASDE BACKTEST START ===")

    results = []
    today = datetime.now()

    for months_back in range(1, 13):
        target = today - timedelta(days=30 * months_back)
        url = _build_wasde_url(target)
        label = target.strftime("%Y-%m")
        log.info(f"Backtest: {label} — {url}")

        try:
            cfg_copy = dict(cfg)
            cfg_copy["source_url"] = url
            raw = fetch_raw(cfg_copy)
            records = parse_raw(raw, cfg_copy)

            if not records:
                results.append({"month": label, "status": "empty"})
                continue

            # Run synthesis
            normalized = json.dumps(records, ensure_ascii=False)
            prompt = cfg["synthesis_prompt"].format(data=normalized[:3000])
            resp = gw_call(prompt, task_type=cfg["synthesize_task"],
                           max_tokens=cfg["synthesize_max_tokens"])

            synthesis = resp.text if resp.success else "SYNTHESIS_FAILED"

            # Extract overall direction from synthesis
            # Look for the "Overall: BULLISH/BEARISH/NEUTRAL/MIXED" line
            direction = "UNKNOWN"
            for line in synthesis.upper().split("\n"):
                if "OVERALL" in line:
                    for label_check in ["BULLISH", "BEARISH", "NEUTRAL", "MIXED"]:
                        if label_check in line:
                            direction = label_check
                            break
                    break

            result = {
                "month":      label,
                "url":        url,
                "records":    len(records),
                "direction":  direction,
                "synthesis":  synthesis[:200],
                "status":     "ok",
                # price_movement: wire to commodity price API
                # actual_direction: computed from price_movement
                # correct: actual_direction == direction
                "price_movement":   None,  # stub
                "actual_direction": None,  # stub
                "correct":          None,  # stub
            }
            results.append(result)
            log.info(f"  {label}: {direction} ({len(records)} records)")
            time.sleep(2)  # rate limit courtesy

        except Exception as e:
            results.append({"month": label, "status": "error", "error": str(e)[:80]})
            log.warning(f"  {label}: FAILED — {str(e)[:60]}")

    # Summary stats (when price feed is wired)
    graded = [r for r in results if r.get("correct") is not None]
    accuracy = sum(1 for r in graded if r["correct"]) / len(graded) if graded else None

    report = {
        "generated_at": datetime.now().isoformat(),
        "months_tested": len(results),
        "accuracy":      accuracy,
        "target_accuracy": 0.88,
        "target_wrong_calls": 0.08,
        "results":       results,
        "notes": (
            "Price movement validation not yet wired. "
            "Connect commodity price feed to complete accuracy calculation. "
            "Directional calls extracted from synthesis — review manually."
        ),
    }

    out_path = Path(cfg["output_dir"]) / "backtest-report.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    log.info(f"Backtest complete. Report: {out_path}")
    log.info(f"  Months tested: {len(results)} | Graded: {len(graded)}")
    if accuracy is not None:
        log.info(f"  Accuracy: {accuracy:.1%} (target: 88%)")

    return report


# ══════════════════════════════════════════════════════════════════
# FRAMEWORK — inherited from tier1_pipeline_template.py
# Only modification: classify valid set extended for WASDE labels
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
    """Shannon Rule: keep handoff note under 40 words."""
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


def _push_inbox(cfg: dict, item: dict) -> None:
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


def _normalize_with_gemini(records: list, cfg: dict, log) -> str:
    if not records:
        return "[]"
    # Preserve narrative fields — strip before sending to Gemini, re-attach after
    narratives = {r.get("commodity", ""): r.get("narrative", "") for r in records}
    records_no_narrative = [{k: v for k, v in r.items() if k != "narrative"}
                             for r in records]
    prompt = (
        "Normalize this WASDE commodity data to clean JSON. "
        "Standardize number formats (remove commas from numbers). "
        "Return ONLY valid JSON array, no markdown, no backticks, no commentary:\n\n"
        f"{json.dumps(records_no_narrative, ensure_ascii=False)}"
    )
    resp = gw_call(prompt, task_type=cfg["normalize_task"], max_tokens=1000)
    if not resp.success:
        log.warning(f"Gemini normalization failed: {resp.error} — using raw records")
        return json.dumps(records, ensure_ascii=False)
    # Strip markdown fences
    text = resp.text.strip()
    if text.startswith("```"):
        text = text.split("```", 2)[-1] if text.count("```") >= 2 else text
        text = text.lstrip("json").strip().rstrip("```").strip()
    # Validate and re-attach narratives
    try:
        normalized_list = json.loads(text)
        for r in normalized_list:
            commodity = r.get("commodity") or r.get("Commodity", "")
            if commodity in narratives:
                r["narrative"] = narratives[commodity]
        result = json.dumps(normalized_list, ensure_ascii=False)
    except Exception:
        log.warning("Gemini returned malformed JSON — falling back to raw records")
        result = json.dumps(records, ensure_ascii=False)
    log.info(f"Normalized via {resp.provider}/{resp.model} ({resp.latency_ms}ms)")
    return result


def _synthesize_with_mistral(normalized: str, cfg: dict, log) -> str:
    """Routes to Mistral Large via gateway reasoning task_type (Claude depleted)."""
    import json as _j

    # Parse records to extract pre-computed signals and prior data flag
    try:
        recs = _j.loads(normalized)
        missing_prior = sum(1 for r in recs
                            if isinstance(r, dict) and not r.get("prior_production"))
        # Build signal map: commodity -> pre-computed signal
        signal_map = {r["commodity"]: r.get("signal", "UNKNOWN")
                      for r in recs if isinstance(r, dict) and "commodity" in r}
        prior_note = (
            "\nNOTE: Prior month data unavailable for most commodities. "
            "If you cannot establish direction from change data, use the 'signal' field.\n"
        ) if missing_prior >= 3 else ""
    except Exception:
        signal_map = {}
        prior_note = ""

    safe_data = normalized[:3000].replace("{", "{{").replace("}", "}}")
    prompt = cfg["synthesis_prompt"].format(data=safe_data) + prior_note
    resp = gw_call(prompt, task_type=cfg["synthesize_task"],
                   max_tokens=cfg["synthesize_max_tokens"])
    if not resp.success:
        log.warning(f"Synthesis failed: {resp.error}")
        return f"Synthesis unavailable — {resp.error}"

    synthesis = resp.text
    log.info(f"Synthesized via {resp.provider}/{resp.model} ({resp.latency_ms}ms)")

    # Post-process: override any commodity line where LLM contradicts pre-computed signal
    # Only override BULLISH/BEARISH signals — leave NEUTRAL/UNKNOWN to LLM judgment
    corrected_lines = []
    for line in synthesis.split("\n"):
        corrected = line
        for commodity, signal in signal_map.items():
            if signal not in ("BULLISH", "BEARISH"):
                continue
            # Check if this line is about this commodity
            if not line.strip().upper().startswith(commodity.upper()):
                continue
            # Check if LLM got it wrong
            line_upper = line.upper()
            llm_bullish = "BULLISH" in line_upper
            llm_bearish = "BEARISH" in line_upper
            llm_neutral  = "NEUTRAL" in line_upper or (not llm_bullish and not llm_bearish)
            signal_correct = (signal == "BULLISH" and llm_bullish) or \
                             (signal == "BEARISH" and llm_bearish)

            if not signal_correct and llm_neutral:
                # LLM said NEUTRAL but signal says BULLISH or BEARISH — override
                # Extract commodity name and narrative snippet for the correction
                try:
                    rec = next(r for r in _j.loads(normalized)
                               if isinstance(r, dict) and r.get("commodity") == commodity)
                    narrative_short = rec.get("narrative", "")[:120].replace("\n", " ")
                except Exception:
                    narrative_short = ""
                # Strip commodity header prefix from narrative (e.g. "RICE: The outlook...")
                clean_narrative = narrative_short
                for prefix in [f"{commodity.upper()}:", f"{commodity}:"]:
                    if clean_narrative.upper().startswith(prefix):
                        clean_narrative = clean_narrative[len(prefix):].strip()
                lede = clean_narrative.split(",")[0].strip().rstrip(".")
                corrected = (
                    f"{commodity}: {lede} -- {signal} for prices"
                )
                log.info(f"Signal override: {commodity} LLM=NEUTRAL -> {signal}")
        corrected_lines.append(corrected)

    return "\n".join(corrected_lines)
    resp = gw_call(prompt, task_type=cfg["synthesize_task"],
                   max_tokens=cfg["synthesize_max_tokens"])
    if not resp.success:
        log.warning(f"Synthesis failed: {resp.error}")
        return f"Synthesis unavailable — {resp.error}"
    log.info(f"Synthesized via {resp.provider}/{resp.model} ({resp.latency_ms}ms)")
    return resp.text


def _classify_with_ollama(normalized: str, cfg: dict, log) -> str:
    """WASDE-specific valid labels: BULLISH | BEARISH | NEUTRAL | EMPTY."""
    # Escape braces in data — prevents KeyError on JSON keys like {Commodity}
    safe_data = normalized[:500].replace("{", "{{").replace("}", "}}")
    prompt = cfg["classify_prompt"].format(data=safe_data)
    resp = gw_call(prompt, task_type=cfg["classify_task"],
                   max_tokens=cfg["classify_max_tokens"])
    if not resp.success:
        log.warning(f"Ollama classification failed: {resp.error} — defaulting to NEUTRAL")
        return "NEUTRAL"
    label = resp.text.strip().upper().split()[0]
    valid = {"BULLISH", "BEARISH", "NEUTRAL", "EMPTY"}
    result = label if label in valid else "NEUTRAL"
    log.info(f"Classified: {result} via {resp.provider}/{resp.model}")
    return result


def _deliver(normalized: str, synthesis: str, classification: str,
             records: list, cfg: dict, state: dict, log, dry: bool) -> None:
    ts = datetime.now().strftime("%Y-%m-%d")
    out_dir = Path(cfg["output_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)

    # Safe parse of normalized JSON — fallback to original records if malformed
    try:
        clean_normalized = normalized.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        normalized_records = json.loads(clean_normalized)
        # Normalize all keys to lowercase (Groq/Gemini may capitalize them)
        normalized_records = [{k.lower(): v for k, v in r.items()}
                               if isinstance(r, dict) else r
                               for r in normalized_records]
    except Exception:
        normalized_records = records  # Codd: blank over wrong — use original

    # File output (JSON)
    if cfg["deliver_file"] and not dry:
        out_path = out_dir / f"{cfg['agent_id']}-{ts}.json"
        payload = {
            "agent_id":       cfg["agent_id"],
            "pool_number":    cfg["pool_number"],
            "generated_at":   datetime.now().isoformat(),
            "source_url":     cfg["source_url"],
            "record_count":   len(records),
            "classification": classification,
            "synthesis":      synthesis,
            "records":        normalized_records,
        }
        tmp = str(out_path) + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        os.replace(tmp, str(out_path))
        log.info(f"JSON output written: {out_path}")

    # HTML digest output
    if not dry:
        html = _build_html_digest(records, synthesis, classification, cfg)
        html_path = out_dir / f"{cfg['agent_id']}-{ts}.html"
        tmp = str(html_path) + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(html)
        os.replace(tmp, str(html_path))
        log.info(f"HTML digest written: {html_path}")

    # Daily digest entry
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

    # Email delivery — stub until Beehiiv key is in studio-config
    if cfg["deliver_email"] and not dry:
        studio_cfg = _load_studio_config(cfg)
        beehiiv_key = studio_cfg.get("Beehiiv API Key", "")
        beehiiv_pub = studio_cfg.get("Beehiiv Publication ID", "")
        if beehiiv_key and beehiiv_pub:
            html = _build_html_digest(records, synthesis, classification, cfg)
            subject = f"FCI — WASDE Food Cost Alert {datetime.now().strftime('%B %Y')}"
            result = _beehiiv_delivery(html, subject, beehiiv_key, beehiiv_pub, log)
            if not result["ok"]:
                log.warning(f"EMAIL: Delivery failed — {result['error']}")
        else:
            log.info("EMAIL: Beehiiv key not in studio-config — skipping email delivery")

    if dry:
        log.info("[DRY RUN] Delivery skipped — synthesis preview:")
        log.info(synthesis[:300])
        # Still build HTML in dry run for inspection
        html = _build_html_digest(records, synthesis, classification, cfg)
        html_path = out_dir / f"{cfg['agent_id']}-dryrun.html"
        html_path.parent.mkdir(parents=True, exist_ok=True)
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)
        log.info(f"[DRY RUN] HTML preview written: {html_path}")


# ══════════════════════════════════════════════════════════════════
# MAIN PIPELINE — Bezos + Hamilton + Hopper enforced
# ══════════════════════════════════════════════════════════════════

def run(cfg: dict, dry: bool = False) -> dict:
    log = _setup_logging(cfg)
    state = _load_state(cfg)
    start_time = time.time()

    log.info(f"=== {cfg['agent_id']} START === pool #{cfg['pool_number']} | dry={dry}")
    log.info(f"Source URL: {cfg['source_url']}")

    def elapsed():
        return time.time() - start_time

    def hamilton_check():
        if elapsed() > cfg["ttl_seconds"]:
            raise TimeoutError(
                f"HAMILTON: runtime {elapsed():.0f}s exceeded TTL {cfg['ttl_seconds']}s — aborting"
            )

    try:
        # ── STEP 1: FETCH ─────────────────────────────────────────
        hamilton_check()
        log.info("Step 1: Fetching WASDE PDF...")

        MAX_CONSECUTIVE_FAILURES = 3   # Bezos Rule
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
                log.warning(f"Fetch attempt {attempt+1} failed: {str(e)[:100]}")
                if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                    log.error(f"CIRCUIT BREAKER: {MAX_CONSECUTIVE_FAILURES} consecutive failures")
                    raise
                time.sleep(10)  # longer delay for PDF sources

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

        pull_meta = {
            "pull_timestamp": datetime.now().isoformat(),
            "source_url":     cfg["source_url"],
            "byte_count":     len(raw),
            "checksum":       checksum,
        }
        log.info(f"HOPPER: {pull_meta['byte_count']:,} bytes, checksum={checksum}")

        # ── STEP 3: PARSE ─────────────────────────────────────────
        hamilton_check()
        log.info("Step 2: Parsing commodity tables...")
        records = parse_raw(raw, cfg)
        high_conf = [r for r in records if r.get("confidence") == "high"]
        narrative_only = [r for r in records if r.get("narrative") and r.get("confidence") == "low"]
        log.info(f"Parsed {len(records)} commodities | {len(high_conf)} high-confidence | {len(narrative_only)} narrative-only")

        # Allow narrative-only months through — some WASDE releases have no table changes
        if not records or (not high_conf and not narrative_only):
            log.warning("No usable records — possible parser failure or pre-release PDF")
            state["handoff_note"] = f"Low confidence parse. Check PDF structure. {datetime.now().isoformat()[:10]}"
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

        # ── STEP 6: SYNTHESIZE (Mistral via gateway) ──────────────
        hamilton_check()
        log.info("Step 5: Synthesizing with Mistral (reasoning task_type)...")
        synthesis = _synthesize_with_mistral(normalized, cfg, log)

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
            "handoff_note": (
                f"wasde-parser ran {datetime.now().isoformat()[:10]}. "
                f"{len(records)} commodities ({len(high_conf)} high-conf). "
                f"{classification}. Synthesis: {synthesis[:60]}..."
            ),
        })
        _save_state(cfg, state, log)

        # BULLISH = supply tighter = price risk for buyers = push inbox
        if classification == "BULLISH":
            _push_inbox(cfg, {
                "id":      f"wasde-parser-bullish-{datetime.now().strftime('%Y%m%d')}",
                "source":  cfg["agent_id"],
                "type":    "data_alert",
                "urgency": "WARN",
                "title":   f"WASDE BULLISH — commodity supply tighter this month",
                "finding": synthesis[:200],
                "status":  "PENDING",
                "date":    datetime.now().isoformat(),
            })
            log.info("BULLISH classification — pushed to supervisor inbox")

        elapsed_s = elapsed()
        log.info(f"=== {cfg['agent_id']} COMPLETE === {elapsed_s:.1f}s | {len(records)} commodities | {classification}")
        return {"status": "ok", "records": len(records), "classification": classification}

    except TimeoutError as e:
        log.error(str(e))
        state["error_count"] = state.get("error_count", 0) + 1
        state["handoff_note"] = f"TIMEOUT abort {datetime.now().isoformat()[:10]}. Check TTL."
        _save_state(cfg, state, log)
        _push_inbox(cfg, {
            "id":      f"wasde-parser-timeout-{datetime.now().strftime('%Y%m%d%H%M')}",
            "source":  cfg["agent_id"],
            "type":    "agent_error",
            "urgency": "WARN",
            "title":   "TIMEOUT: wasde-parser",
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
            "id":      f"wasde-parser-error-{datetime.now().strftime('%Y%m%d%H%M')}",
            "source":  cfg["agent_id"],
            "type":    "agent_error",
            "urgency": "WARN",
            "title":   "ERROR: wasde-parser",
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
    parser = argparse.ArgumentParser(description="wasde-parser — USDA WASDE Food Cost Alert")
    parser.add_argument("--dry",      action="store_true", help="Dry run — fetch/parse/synthesize but no delivery")
    parser.add_argument("--backtest", action="store_true", help="Run synthesis validator on last 12 months")
    args = parser.parse_args()

    if args.backtest:
        report = run_backtest(AGENT_CONFIG)
        print(f"\nBacktest complete: {report['months_tested']} months tested")
        print(f"Accuracy: {report['accuracy']} (target: 88%)")
        sys.exit(0)

    result = run(AGENT_CONFIG, dry=args.dry)
    print(f"\nResult: {result}")
    sys.exit(0 if result.get("status") in ("ok", "skipped", "empty") else 1)


# ══════════════════════════════════════════════════════════════════
# TASK SCHEDULER XML
# ══════════════════════════════════════════════════════════════════
# Copy scheduler\tier1-template.xml → scheduler\wasde-parser.xml
# Replace:
#   AGENT_ID              → wasde-parser
#   POOL_NUMBER           → 56
#   AGENT_SCRIPT          → wasde_parser.py
#   TRIGGER_HOUR          → 2
#   TRIGGER_MINUTE        → 15
#   EXPECTED_RUNTIME_SECONDS → 600
#
# Register:
#   schtasks /Create /XML "G:\My Drive\Projects\_studio\scheduler\wasde-parser.xml" ^
#            /TN "\Studio\wasde-parser" /F
#
# Test:
#   schtasks /Run /TN "\Studio\wasde-parser"
#
# Dry run first:
#   cd "G:\My Drive\Projects\_studio"
#   python agents\wasde_parser.py --dry
# ══════════════════════════════════════════════════════════════════
