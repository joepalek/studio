
# EXPECTED_RUNTIME_SECONDS: 3600
"""
synthesis_validator.py
======================
Load wasde_historical.db, run synthesis prompt on each month,
compare directional call (BULLISH/BEARISH/NEUTRAL) to actual
30-day price movement for Wheat, Corn, Soybeans.

Price data: yfinance (pip install yfinance)
  Wheat  → ZW=F (CBOT Wheat futures)
  Corn   → ZC=F (CBOT Corn futures)
  Soybeans → ZS=F (CBOT Soybean futures)

Output: accuracy report printed + written to
  G:/My Drive/Projects/_studio/data/wasde/synthesis_validation_report.json

Usage:
    python synthesis_validator.py              # full DB
    python synthesis_validator.py --months 24  # last 24 months
"""

MAX_CONSECUTIVE_FAILURES = 3  # Bezos Rule

import sys, os, json, time, sqlite3, argparse, logging
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, "G:/My Drive/Projects/_studio")
from ai_gateway import call as gw_call

# ─── Logging ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(
            "G:/My Drive/Projects/_studio/logs/wasde-validator.log",
            encoding="utf-8"
        ),
    ],
)
log = logging.getLogger("synthesis-validator")

# ─── Config ───────────────────────────────────────────────────────────────────

DB_PATH    = "G:/My Drive/Projects/_studio/data/wasde/wasde_historical.db"
OUT_PATH   = "G:/My Drive/Projects/_studio/data/wasde/synthesis_validation_report.json"
CACHE_PATH = "G:/My Drive/Projects/_studio/data/wasde/price_cache.json"

SYNTHESIS_PROMPT = (
    "You are a food procurement analyst. "
    "Your audience is food buyers who need to know if commodity prices will rise or fall.\n\n"
    "WASDE data this month:\n{data}\n\n"
    "Each record may have a 'narrative' field with USDA prose and a 'narrative_signal' "
    "pre-computed from keyword analysis (BULLISH/BEARISH/NEUTRAL/UNKNOWN).\n"
    "Use narrative when numeric fields are blank. Trust narrative_signal when BULLISH or BEARISH.\n\n"
    "For each commodity (Wheat, Corn, Soybeans, Cotton, Rice), write ONE sentence:\n"
    "  Format: 'CommodityName: [what changed] -- [BULLISH/BEARISH/NEUTRAL] for prices'\n\n"
    "CRITICAL RULES:\n"
    "1. Early harvest = MORE supply = BEARISH. Not bullish.\n"
    "2. La Nina/drought = supply CUT = BULLISH.\n"
    "3. Production cut = tighter supply = BULLISH.\n"
    "4. Ambiguous or missing data = NEUTRAL. Never force direction.\n"
    "5. 'No changes this month' = NEUTRAL.\n"
    "6. 'Lower supplies' OR 'reduced exports' = BULLISH even if ending stocks steady.\n"
    "7. narrative_signal=UNKNOWN means insufficient data — default NEUTRAL.\n\n"
    "After the 5 lines, add: "
    "'Overall: [BULLISH/BEARISH/NEUTRAL/MIXED] -- [one procurement sentence]'\n\n"
    "Return ONLY these 6 lines. No preamble."
)

# Futures tickers for price validation — 3 most liquid grains
PRICE_TICKERS = {
    "Wheat":    "ZW=F",
    "Corn":     "ZC=F",
    "Soybeans": "ZS=F",
}

# ─── Price Fetching ───────────────────────────────────────────────────────────

def load_price_cache():
    if Path(CACHE_PATH).exists():
        try:
            return json.loads(Path(CACHE_PATH).read_text(encoding="utf-8"))
        except:
            pass
    return {}

def save_price_cache(cache):
    tmp = CACHE_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2)
    os.replace(tmp, CACHE_PATH)

def get_price_change(ticker, release_date_str, cache):
    """
    Return 30-day % price change for ticker starting on release_date_str (YYYY-MM-DD).
    Uses cache to avoid repeated yfinance calls.
    """
    cache_key = f"{ticker}_{release_date_str}"
    if cache_key in cache:
        return cache[cache_key]

    try:
        import yfinance as yf
        start = datetime.strptime(release_date_str, "%Y-%m-%d")
        end   = start + timedelta(days=35)
        hist  = yf.download(ticker, start=start.strftime("%Y-%m-%d"),
                            end=end.strftime("%Y-%m-%d"), progress=False,
                            auto_adjust=True)
        if hist.empty or len(hist) < 5:
            cache[cache_key] = None
            return None
        # yfinance v1.x uses MultiIndex columns: (field, ticker)
        close_col = ("Close", ticker)
        if close_col in hist.columns:
            close = hist[close_col]
        else:
            close = hist["Close"]
        open_price  = float(close.iloc[0])
        close_price = float(close.iloc[min(21, len(close)-1)])
        pct = (close_price - open_price) / open_price * 100
        cache[cache_key] = round(pct, 2)
        return cache[cache_key]
    except Exception as e:
        log.warning(f"  Price fetch failed {ticker} {release_date_str}: {str(e)[:60]}")
        cache[cache_key] = None
        return None

def price_direction(pct_change, threshold=2.0):
    """Convert % change to directional label."""
    if pct_change is None:
        return "UNKNOWN"
    if pct_change > threshold:
        return "BULLISH"
    if pct_change < -threshold:
        return "BEARISH"
    return "NEUTRAL"

# ─── WASDE release dates ──────────────────────────────────────────────────────
# WASDE releases on the second Friday of each month, typically.
# Approximate by using the 10th of each month as release date.
def month_to_release_date(month_str):
    """YYYY-MM → approximate release date YYYY-MM-10."""
    return f"{month_str}-10"

# ─── Synthesis ────────────────────────────────────────────────────────────────

def extract_overall_direction(text):
    for line in text.upper().split("\n"):
        if "OVERALL" in line:
            for label in ["BULLISH", "BEARISH", "NEUTRAL", "MIXED"]:
                if label in line:
                    return label
    counts = {l: text.upper().count(l) for l in ["BULLISH", "BEARISH", "NEUTRAL", "MIXED"]}
    return max(counts, key=counts.get) if any(counts.values()) else "UNKNOWN"

def run_synthesis_for_month(month, records):
    """Run synthesis prompt via gateway, return (direction, synthesis_text)."""
    # Build compact data payload
    data_rows = []
    for r in records:
        row = {
            "commodity":       r["commodity"],
            "production":      r["production"],
            "ending_stocks":   r["ending_stocks"],
            "exports":         r["exports"],
            "domestic_use":    r["domestic_use"],
            "mom_change":      r["mom_change"],
            "narrative_signal": r["narrative_signal"],
            "narrative":        (r["narrative"] or "")[:200],
        }
        data_rows.append(row)

    prompt = SYNTHESIS_PROMPT.replace("{data}", json.dumps(data_rows, ensure_ascii=False)[:3000])
    resp = gw_call(prompt, task_type="reasoning", max_tokens=400)
    if not resp.success:
        log.warning(f"  Synthesis failed for {month}: {resp.error}")
        return "UNKNOWN", ""
    direction = extract_overall_direction(resp.text)
    return direction, resp.text

# ─── Accuracy Scoring ─────────────────────────────────────────────────────────

def score_call(synthesized_dir, actual_dir):
    """
    correct      = exact match, or MIXED/NEUTRAL both non-directional
    wrong        = BULLISH vs BEARISH (dangerous wrong call)
    neutral_miss = synthesis said NEUTRAL/MIXED but market moved directionally
    """
    if synthesized_dir == "UNKNOWN" or actual_dir == "UNKNOWN":
        return "undetermined"
    # Normalize: MIXED is treated as non-directional (same risk class as NEUTRAL)
    synth_norm  = "NEUTRAL" if synthesized_dir in ("NEUTRAL", "MIXED") else synthesized_dir
    actual_norm = "NEUTRAL" if actual_dir      in ("NEUTRAL", "MIXED") else actual_dir
    if synth_norm == actual_norm:
        return "correct"
    if {synth_norm, actual_norm} == {"BULLISH", "BEARISH"}:
        return "wrong"  # dangerous wrong call
    # One is NEUTRAL, other is directional
    return "neutral_miss"

# ─── Main ─────────────────────────────────────────────────────────────────────

def run(months_limit=None):
    if not Path(DB_PATH).exists():
        log.error(f"DB not found: {DB_PATH} — run wasde_historical_backfill.py first")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    query = "SELECT DISTINCT month FROM wasde_historical ORDER BY month DESC"
    if months_limit:
        query += f" LIMIT {months_limit}"
    months = [row["month"] for row in conn.execute(query).fetchall()]

    log.info(f"Validator: {len(months)} months to evaluate")

    price_cache = load_price_cache()
    results = []
    consecutive_failures = 0

    for month in months:
        log.info(f"  Processing {month}...")

        # Load commodity records for this month
        rows = conn.execute(
            "SELECT * FROM wasde_historical WHERE month=?", (month,)
        ).fetchall()
        if not rows:
            log.warning(f"  No data for {month} — skip")
            continue

        records = [dict(r) for r in rows]

        # Run synthesis
        try:
            synth_dir, synth_text = run_synthesis_for_month(month, records)
            consecutive_failures = 0
        except Exception as e:
            log.error(f"  Synthesis exception {month}: {str(e)[:80]}")
            consecutive_failures += 1
            if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                log.error("CIRCUIT BREAKER: 3 consecutive synthesis failures — aborting")
                break
            time.sleep(2)
            continue

        # Get actual price movements (Wheat, Corn, Soybeans — most liquid)
        release_date = month_to_release_date(month)
        commodity_results = []
        for commodity, ticker in PRICE_TICKERS.items():
            pct = get_price_change(ticker, release_date, price_cache)
            actual_dir = price_direction(pct)
            log.info(f"    {commodity}: synth={synth_dir} actual={actual_dir} ({pct}%)")
            outcome = score_call(synth_dir, actual_dir)
            commodity_results.append({
                "commodity":   commodity,
                "ticker":      ticker,
                "synth_dir":   synth_dir,
                "actual_dir":  actual_dir,
                "pct_change":  pct,
                "outcome":     outcome,
            })

        results.append({
            "month":       month,
            "release_date": release_date,
            "synth_dir":   synth_dir,
            "synthesis":   synth_text[:400],
            "commodities": commodity_results,
        })

        save_price_cache(price_cache)
        time.sleep(1)  # polite delay between gateway calls

    conn.close()

    if not results:
        log.warning("No results to report")
        return {}

    # ─── Accuracy Report ──────────────────────────────────────────────────────
    all_calls = [c for r in results for c in r["commodities"]]
    determined = [c for c in all_calls if c["outcome"] != "undetermined"]
    correct      = sum(1 for c in determined if c["outcome"] == "correct")
    wrong        = sum(1 for c in determined if c["outcome"] == "wrong")
    neutral_miss = sum(1 for c in determined if c["outcome"] == "neutral_miss")

    accuracy_pct = round(correct / len(determined) * 100, 1) if determined else 0
    wrong_pct    = round(wrong   / len(determined) * 100, 1) if determined else 0

    report = {
        "generated_at":     datetime.now().isoformat(),
        "months_evaluated": len(results),
        "total_calls":      len(determined),
        "correct":          correct,
        "wrong_dangerous":  wrong,
        "neutral_miss":     neutral_miss,
        "accuracy_pct":     accuracy_pct,
        "wrong_pct":        wrong_pct,
        "target_accuracy":  88.0,
        "target_wrong_max": 8.0,
        "pass":             accuracy_pct >= 88.0 and wrong_pct <= 8.0,
        "monthly_detail":   results,
    }

    # Write report
    out = Path(OUT_PATH)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = str(out) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    os.replace(tmp, str(out))

    # Print summary
    print("\n" + "="*60)
    print("SYNTHESIS VALIDATOR REPORT")
    print("="*60)
    print(f"Months evaluated:  {len(results)}")
    print(f"Total calls:       {len(determined)}")
    print(f"Correct:           {correct}  ({accuracy_pct}%)")
    print(f"Wrong (dangerous): {wrong}   ({wrong_pct}%)")
    print(f"Neutral miss:      {neutral_miss}")
    print(f"Target:            ≥88% accuracy, ≤8% dangerous wrong")
    verdict = "PASS" if report["pass"] else "FAIL"
    print(f"VERDICT:           {verdict}")
    print(f"Report written to: {OUT_PATH}")
    print("="*60)

    return report

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    p = argparse.ArgumentParser(description="WASDE synthesis accuracy validator")
    p.add_argument("--months", type=int, default=None, help="limit to N most recent months")
    args = p.parse_args()
    run(args.months)
