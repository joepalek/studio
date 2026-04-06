
# EXPECTED_RUNTIME_SECONDS: 1800
"""
wasde_historical_backfill.py
============================
Download last 60 WASDE PDFs (5 years, monthly), parse each, store in
wasde_historical.db (SQLite).

Schema: month, commodity, production, domestic_use, exports,
        ending_stocks, mom_change, unit, confidence, narrative_signal

Usage:
    python wasde_historical_backfill.py              # full 60-month run
    python wasde_historical_backfill.py --months 12  # last 12 months only
    python wasde_historical_backfill.py --resume     # skip already-stored months
"""

MAX_CONSECUTIVE_FAILURES = 3  # Bezos Rule

import sys, os, json, time, sqlite3, argparse, io, logging
from datetime import datetime
from pathlib import Path

sys.path.insert(0, "G:/My Drive/Projects/_studio")

# ─── Logging ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(
            "G:/My Drive/Projects/_studio/logs/wasde-backfill.log",
            encoding="utf-8"
        ),
    ],
)
log = logging.getLogger("wasde-backfill")

# ─── DB Setup ─────────────────────────────────────────────────────────────────

DB_PATH = "G:/My Drive/Projects/_studio/data/wasde/wasde_historical.db"

def init_db(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS wasde_historical (
            month           TEXT NOT NULL,
            commodity       TEXT NOT NULL,
            production      REAL,
            domestic_use    REAL,
            exports         REAL,
            ending_stocks   REAL,
            prior_production REAL,
            prior_domestic_use REAL,
            prior_exports   REAL,
            prior_ending_stocks REAL,
            mom_change      TEXT,
            unit            TEXT,
            confidence      TEXT,
            narrative_signal TEXT,
            narrative       TEXT,
            fetched_at      TEXT,
            PRIMARY KEY (month, commodity)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS backfill_log (
            month       TEXT PRIMARY KEY,
            status      TEXT,
            error       TEXT,
            fetched_at  TEXT
        )
    """)
    conn.commit()

def already_stored(conn, month):
    row = conn.execute(
        "SELECT COUNT(*) FROM wasde_historical WHERE month=?", (month,)
    ).fetchone()
    return row[0] >= 3  # at least 3 commodities = partial success is stored

def log_month(conn, month, status, error=""):
    conn.execute(
        "INSERT OR REPLACE INTO backfill_log VALUES (?,?,?,?)",
        (month, status, error[:200], datetime.now().isoformat())
    )
    conn.commit()

# ─── Month List ───────────────────────────────────────────────────────────────

def build_month_list(n=60):
    """Return list of (YYYY-MM, URL) from most recent back n months."""
    d = datetime(2026, 4, 1)
    months = []
    for _ in range(n):
        url = f"https://www.usda.gov/oce/commodity/wasde/wasde{d.strftime('%m%y')}.pdf"
        months.append((d.strftime("%Y-%m"), url))
        if d.month == 1:
            d = d.replace(year=d.year - 1, month=12)
        else:
            d = d.replace(month=d.month - 1)
    return months

# ─── Fetch + Parse (reuse wasde_parser logic) ─────────────────────────────────

def _wayback_url(original_url):
    """
    Find the best Wayback Machine snapshot for a URL.
    Returns snapshot URL or None.
    """
    import urllib.request, json
    avail_api = f"https://archive.org/wayback/available?url={original_url}"
    try:
        r = urllib.request.urlopen(avail_api, timeout=10)
        d = json.loads(r.read())
        snap = d.get("archived_snapshots", {}).get("closest", {})
        if snap.get("available") and snap.get("url"):
            return snap["url"]
    except Exception:
        pass
    return None

def fetch_pdf(url):
    import pdfplumber, urllib.request, urllib.error

    def _download(target_url):
        req = urllib.request.Request(
            target_url,
            headers={"User-Agent": "Mozilla/5.0 StudioAgent/1.0", "Accept": "application/pdf"},
        )
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.read()

    # Try direct USDA URL first
    try:
        pdf_bytes = _download(url)
        source = "usda"
    except urllib.error.HTTPError as e:
        if e.code != 404:
            raise
        # 404 → try Wayback Machine
        log.info(f"    USDA 404 — trying Wayback Machine...")
        wb_url = _wayback_url(url)
        if not wb_url:
            raise RuntimeError(f"Not on USDA or Wayback Machine: {url}")
        log.info(f"    Wayback: {wb_url}")
        pdf_bytes = _download(wb_url)
        source = "wayback"

    if len(pdf_bytes) < 5000:
        raise RuntimeError(f"PDF too small ({len(pdf_bytes)}b) — not released or wrong URL")

    all_tables, all_text = [], []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            all_text.append(page.extract_text() or "")
            tbls = page.extract_tables()
            if tbls:
                all_tables.extend(tbls)
    full_text = "\n\n".join(all_text)
    log.info(f"    Source: {source} | {len(pdf_bytes):,} bytes")
    return all_tables, full_text

def _parse_num(v):
    try:
        return float(str(v).replace(",", "").strip())
    except:
        return None

def _clean_cell(v):
    if v is None:
        return ""
    s = str(v).strip()
    return "" if s in ("-", "--", "---", "N/A", "") else s

WASDE_COMMODITIES = ["Wheat", "Corn", "Soybeans", "Cotton", "Rice"]

DOMESTIC_USE_LABELS = {
    "Wheat":    ["DOMESTIC USE", "TOTAL DOMESTIC USE", "FOOD USE", "FOOD, SEED & IND."],
    "Corn":     ["DOMESTIC USE", "TOTAL DOMESTIC USE", "FOOD, SEED & IND.", "FEED & RESIDUAL"],
    "Soybeans": ["DOMESTIC USE", "TOTAL DOMESTIC USE", "CRUSHINGS", "CRUSH"],
    "Cotton":   ["DOMESTIC USE", "TOTAL DOMESTIC USE", "MILL USE", "DOMESTIC MILL USE"],
    "Rice":     ["DOMESTIC USE", "TOTAL DOMESTIC USE", "FOOD USE", "DOMESTIC FOOD USE"],
}

WASDE_BOUNDS = {
    "Wheat":    {"production": (1200, 2800),  "ending_stocks": (300, 1200),
                 "exports": (700, 1400),       "domestic_use": (900, 1600)},
    "Corn":     {"production": (10000, 16000), "ending_stocks": (700, 2500),
                 "exports": (1500, 3000),      "domestic_use": (8000, 13000)},
    "Soybeans": {"production": (3000, 5000),   "ending_stocks": (100, 1000),
                 "exports": (1500, 2500),       "domestic_use": (1800, 2800)},
    "Cotton":   {"production": (10000, 22000), "ending_stocks": (3000, 10000),
                 "exports": (8000, 18000),     "domestic_use": (2000, 5000)},
    "Rice":     {"production": (150, 280),     "ending_stocks": (20, 80),
                 "exports": (50, 130),          "domestic_use": (100, 200)},
}

BULLISH_KW = ["lower supplies", "reduced exports", "supplies are lowered", "supply is lowered",
              "production cut", "production down", "lower production", "tighter", "deficit",
              "drought", "reduced area", "lagging"]
BEARISH_KW = ["higher supplies", "increased production", "production up", "higher production",
              "larger production", "production raised", "forecast raised",
              "higher ending stocks", "increased exports", "surplus", "record harvest",
              "higher output", "increased output", "larger area"]

def _in_bounds(commodity, field, val):
    b = WASDE_BOUNDS.get(commodity, {}).get(field)
    if not b or val is None:
        return True
    return b[0] <= val <= b[1]

def _derive_signal(narrative):
    if not narrative:
        return "UNKNOWN"
    n = narrative.lower()
    bs  = sum(1 for kw in BULLISH_KW if kw in n)
    brs = sum(1 for kw in BEARISH_KW if kw in n)
    if "u.s." in n[:200]:
        bs = int(bs * 1.5)
    if bs == 0 and brs == 0:
        return "NEUTRAL"
    return "BULLISH" if bs > brs else "BEARISH" if brs > bs else "NEUTRAL"

def parse_commodity(commodity, all_tables, full_text):
    terms = [commodity.upper()] + {
        "Soybeans": ["SOYBEAN", "SOYBEANS"],
        "Cotton":   ["UPLAND COTTON", "COTTON"],
        "Rice":     ["U.S. RICE", "RICE"],
    }.get(commodity, [])
    dom = [l.upper() for l in DOMESTIC_USE_LABELS.get(commodity, [])]

    result = {f: None for f in ["production", "domestic_use", "exports", "ending_stocks",
                                 "prior_production", "prior_domestic_use", "prior_exports",
                                 "prior_ending_stocks", "unit"]}
    in_sec = False
    for table in all_tables:
        if not table:
            continue
        for row in table:
            if not row or not row[0]:
                continue
            lbl = str(row[0]).upper().strip()
            if any(t in lbl for t in terms):
                in_sec = True
            if not in_sec:
                continue
            other = [c.upper() for c in WASDE_COMMODITIES if c != commodity]
            if any(lbl.startswith(o) for o in other):
                in_sec = False
                continue
            if "MILLION BUSHELS" in lbl or "MIL. BU." in lbl:
                result["unit"] = "million_bushels"
            elif "1,000 BALES" in lbl:
                result["unit"] = "thousand_bales"
            elif "MIL. CWT" in lbl:
                result["unit"] = "million_cwt"
            c = _clean_cell(row[1]) if len(row) > 1 else ""
            p = _clean_cell(row[2]) if len(row) > 2 else ""
            if "PRODUCTION" in lbl and result["production"] is None:
                result["production"] = c or None
                result["prior_production"] = p or None
            elif any(d in lbl for d in dom) and result["domestic_use"] is None:
                result["domestic_use"] = c or None
                result["prior_domestic_use"] = p or None
            elif "EXPORT" in lbl and "IMPORT" not in lbl and result["exports"] is None:
                result["exports"] = c or None
                result["prior_exports"] = p or None
            elif "ENDING STOCKS" in lbl and result["ending_stocks"] is None:
                result["ending_stocks"] = c or None
                result["prior_ending_stocks"] = p or None

    if commodity == "Cotton":
        result["unit"] = "thousand_bales"

    # Bounds check + convert to float
    for field in ["production", "domestic_use", "exports", "ending_stocks",
                   "prior_production", "prior_domestic_use", "prior_exports", "prior_ending_stocks"]:
        v = result[field]
        if v is None:
            continue
        num = _parse_num(v)
        base = field.replace("prior_", "")
        if num is not None and _in_bounds(commodity, base, num):
            result[field] = num
        else:
            result[field] = None  # Codd: blank over wrong

    # Narrative
    anchors = {
        "Wheat":    ["WHEAT:", "U.S. WHEAT"],
        "Corn":     ["CORN:", "U.S. CORN", "FEED GRAINS:"],
        "Soybeans": ["OILSEEDS:", "U.S. 2025/26 SOYBEAN", "SOYBEANS:"],
        "Cotton":   ["COTTON:", "UPLAND COTTON:"],
        "Rice":     ["RICE:", "U.S. RICE"],
    }.get(commodity, [commodity.upper() + ":"])
    fu = full_text.upper()
    idx = -1
    for anchor in anchors:
        i = fu.find(anchor)
        if i >= 0:
            idx = i
            break
    narrative = ""
    if idx >= 0:
        snippet = full_text[idx:idx + 600].replace("\n", " ")
        sents = [s.strip() for s in snippet.split(". ") if len(s.strip()) > 20]
        if sents:
            narrative = ". ".join(sents[:3]) + "."

    valid = sum(1 for f in ["production", "domestic_use", "exports", "ending_stocks"]
                if result[f] is not None)
    confidence = "high" if valid >= 3 else "medium" if valid >= 2 else "low"
    signal = _derive_signal(narrative)

    return {
        "commodity":          commodity,
        "production":         result["production"],
        "domestic_use":       result["domestic_use"],
        "exports":            result["exports"],
        "ending_stocks":      result["ending_stocks"],
        "prior_production":   result["prior_production"],
        "prior_domestic_use": result["prior_domestic_use"],
        "prior_exports":      result["prior_exports"],
        "prior_ending_stocks": result["prior_ending_stocks"],
        "unit":               result["unit"],
        "confidence":         confidence,
        "narrative_signal":   signal,
        "narrative":          narrative,
    }

def compute_mom_change(curr, prior):
    """Return percentage change string, or '' if not computable."""
    if curr is None or prior is None:
        return ""
    try:
        c, p = float(curr), float(prior)
        if p == 0:
            return ""
        pct = (c - p) / p * 100
        sign = "+" if pct > 0 else ""
        return f"{sign}{pct:.1f}%"
    except:
        return ""

# ─── Main ─────────────────────────────────────────────────────────────────────

def run(months_n=60, resume=False):
    Path("G:/My Drive/Projects/_studio/data/wasde").mkdir(parents=True, exist_ok=True)
    Path("G:/My Drive/Projects/_studio/logs").mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    init_db(conn)

    month_list = build_month_list(months_n)
    log.info(f"Backfill: {len(month_list)} months | resume={resume} | DB: {DB_PATH}")

    stats = {"ok": 0, "skipped": 0, "failed": 0, "empty": 0}
    consecutive_failures = 0

    for month, url in month_list:
        if resume and already_stored(conn, month):
            log.info(f"  SKIP {month} (already in DB)")
            stats["skipped"] += 1
            continue

        log.info(f"  Fetching {month}: {url}")
        try:
            all_tables, full_text = fetch_pdf(url)
            consecutive_failures = 0  # Bezos: reset on success
        except RuntimeError as e:
            # "Not on USDA or Wayback" = expected gap — soft-fail, don't circuit-break
            err = str(e)[:120]
            log.info(f"  UNAVAILABLE {month}: {err}")
            log_month(conn, month, "unavailable", err)
            stats["failed"] += 1
            # Don't increment consecutive_failures for expected unavailability
            time.sleep(1)
            continue
        except Exception as e:
            err = str(e)[:120]
            log.warning(f"  FAIL {month}: {err}")
            log_month(conn, month, "failed", err)
            stats["failed"] += 1
            consecutive_failures += 1
            if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                log.error(f"CIRCUIT BREAKER: {MAX_CONSECUTIVE_FAILURES} consecutive fetch failures — aborting")
                break
            time.sleep(2)
            continue

        records_inserted = 0
        for commodity in WASDE_COMMODITIES:
            rec = parse_commodity(commodity, all_tables, full_text)
            mom = compute_mom_change(rec["production"], rec["prior_production"])
            conn.execute(
                """INSERT OR REPLACE INTO wasde_historical VALUES
                   (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    month, commodity,
                    rec["production"], rec["domestic_use"],
                    rec["exports"],    rec["ending_stocks"],
                    rec["prior_production"], rec["prior_domestic_use"],
                    rec["prior_exports"],    rec["prior_ending_stocks"],
                    mom, rec["unit"],
                    rec["confidence"], rec["narrative_signal"],
                    rec["narrative"][:400] if rec["narrative"] else "",
                    datetime.now().isoformat(),
                )
            )
            records_inserted += 1

        conn.commit()
        log_month(conn, month, "ok")
        stats["ok"] += 1
        log.info(f"  OK {month}: {records_inserted} commodities stored")
        time.sleep(1.5)  # polite delay between USDA fetches

    # Summary
    row_count = conn.execute("SELECT COUNT(*) FROM wasde_historical").fetchone()[0]
    log.info(f"=== BACKFILL COMPLETE === ok={stats['ok']} skip={stats['skipped']} fail={stats['failed']}")
    log.info(f"DB rows: {row_count} | path: {DB_PATH}")
    conn.close()
    return stats

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    p = argparse.ArgumentParser(description="WASDE 60-month historical backfill")
    p.add_argument("--months", type=int, default=60)
    p.add_argument("--resume", action="store_true", help="skip already-stored months")
    args = p.parse_args()
    result = run(args.months, args.resume)
    print(f"\nDone: {result}")
