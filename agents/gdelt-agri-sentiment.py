"""
gdelt-agri-sentiment.py — GDELT News Sentiment: Agriculture & Food
Pool #40 | Tier 1 Pipeline Agent | Daily cadence

Fetches the GDELT Doc 2.0 API for agriculture/food supply news,
extracts tone, themes, and country tags as sentiment signals.
Negative tone spike is a leading indicator of supply disruption.

TASK SCHEDULER: \\Studio\\gdelt-agri-sentiment | 04:00 daily | TTL 180s
"""

import json, os, sys, time, hashlib
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, "G:/My Drive/Projects/_studio")

AGENT_CONFIG = {
    "agent_id":      "gdelt-agri-sentiment",
    "pool_number":   40,
    "pool_name":     "GDELT News Sentiment — Agriculture & Food",
    "source_url":    "https://api.gdeltproject.org/api/v2/doc/doc?query=agriculture%20food%20supply%20prices&mode=artlist&maxrecords=25&format=json",
    "source_format": "api",
    "cadence":       "daily",
    "ttl_seconds":   180,
    "synthesis_prompt": (
        "You are a food supply chain analyst. Audience: food buyers tracking media sentiment.\n\n"
        "GDELT news sentiment data (agriculture/food):\n{data}\n\n"
        "Analyze the tone and themes. Negative tone = supply concern (BULLISH for prices).\n"
        "Positive tone = supply comfort (BEARISH for prices).\n\n"
        "Write ONE summary sentence per theme area if present, then:\n"
        "'Overall: [BULLISH/BEARISH/NEUTRAL/MIXED] -- [one sentence on what the news signals]'\n"
        "Return only the summary lines. No preamble."
    ),
    "synthesize_max_tokens": 300,
    "state_path":    "G:/My Drive/Projects/_studio/data/gdelt-agri-sentiment/state.json",
    "digest_path":   "G:/My Drive/Projects/_studio/daily-digest.json",
    "log_path":      "G:/My Drive/Projects/_studio/logs/gdelt-agri-sentiment.log",
}


def fetch_raw(cfg: dict) -> str:
    """Fetch GDELT artlist JSON. Returns raw response text."""
    import urllib.request, urllib.error
    url = cfg["source_url"]
    max_failures = 3
    for attempt in range(1, max_failures + 1):
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Studio/1.0", "Accept": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=20) as resp:
                text = resp.read().decode("utf-8", errors="replace")
            if len(text) < 100:
                raise ValueError(f"Response too small ({len(text)} bytes)")
            return text
        except Exception as e:
            if attempt >= max_failures:
                raise
            time.sleep(3)
    raise RuntimeError("fetch_raw: unreachable")


def parse_raw(raw: str, cfg: dict) -> list:
    """
    Parse GDELT artlist JSON into sentiment records.
    Returns list of: {date, title, url, tone, themes, country}
    """
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # GDELT sometimes returns HTML error pages
        raise ValueError(f"GDELT response is not valid JSON (first 200: {raw[:200]})")

    articles = data.get("articles", [])
    if not articles:
        return []

    records = []
    for art in articles:
        # GDELT tone field: positive = positive coverage, negative = negative/crisis coverage
        tone_raw = art.get("tone", "")
        try:
            # Tone is a CSV: tone,pos,neg,polarity,actref,selfref
            tone_parts = [float(x) for x in str(tone_raw).split(",") if x.strip()]
            tone_val = tone_parts[0] if tone_parts else 0.0
        except (ValueError, TypeError):
            tone_val = 0.0

        # Classify sentiment direction
        if tone_val <= -3.0:
            sentiment = "BEARISH"   # negative news = supply concern
        elif tone_val >= 3.0:
            sentiment = "BULLISH"   # positive news = supply comfort
        else:
            sentiment = "NEUTRAL"

        date_raw = art.get("seendate", art.get("date", ""))
        # GDELT date format: YYYYMMDDTHHMMSSZ
        try:
            if "T" in date_raw:
                date_clean = date_raw[:8]
                date_clean = f"{date_clean[:4]}-{date_clean[4:6]}-{date_clean[6:8]}"
            else:
                date_clean = str(date_raw)[:10]
        except Exception:
            date_clean = ""

        records.append({
            "date":      date_clean,
            "title":     (art.get("title") or "")[:120],
            "url":       art.get("url", ""),
            "tone":      round(tone_val, 2),
            "sentiment": sentiment,
            "themes":    art.get("themes", ""),
            "country":   art.get("socialimage", art.get("domain", "")),
            "source":    "GDELT v2",
        })

    return records


def _load_state(cfg):
    try:
        return json.loads(Path(cfg["state_path"]).read_text(encoding="utf-8"))
    except Exception:
        return {"last_run": None, "last_checksum": None, "run_count": 0,
                "handoff_note": ""}


def _save_state(state, cfg):
    Path(cfg["state_path"]).parent.mkdir(parents=True, exist_ok=True)
    tmp = cfg["state_path"] + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
    os.replace(tmp, cfg["state_path"])


def run(cfg: dict, dry: bool = False) -> dict:
    import logging
    log = logging.getLogger(cfg["agent_id"])
    if not log.handlers:
        Path(cfg["log_path"]).parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(cfg["log_path"], encoding="utf-8")
        fh.setFormatter(logging.Formatter("[%(asctime)s] %(message)s", datefmt="%H:%M:%S"))
        log.addHandler(fh)
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(logging.Formatter("[%(asctime)s] %(message)s", datefmt="%H:%M:%S"))
        log.addHandler(ch)
        log.setLevel(logging.INFO)

    log.info(f"=== {cfg['agent_id']} START === pool #{cfg['pool_number']} | dry={dry}")
    state = _load_state(cfg)
    t0 = time.time()

    try:
        raw = fetch_raw(cfg)
        checksum = hashlib.md5(raw.encode()).hexdigest()[:12]

        if not dry and checksum == state.get("last_checksum"):
            log.info("HOPPER: no change since last run — skipping")
            state["last_run"] = datetime.now().isoformat()
            state["handoff_note"] = f"No change. checksum={checksum}"
            _save_state(state, cfg)
            return {"status": "skipped", "reason": "unchanged"}

        records = parse_raw(raw, cfg)
        sentiments = [r["sentiment"] for r in records]
        dominant = max(set(sentiments), key=sentiments.count) if sentiments else "UNKNOWN"
        avg_tone = round(sum(r["tone"] for r in records) / len(records), 2) if records else 0

        log.info(f"Parsed {len(records)} articles | avg_tone={avg_tone} | dominant={dominant}")

        if not dry:
            state.update({
                "last_run":       datetime.now().isoformat(),
                "last_checksum":  checksum,
                "run_count":      state.get("run_count", 0) + 1,
                "record_count":   len(records),
                "classification": dominant,
                "avg_tone":       avg_tone,
                "handoff_note":   f"{len(records)} articles | tone={avg_tone} | {dominant} | checksum={checksum}",
            })
            _save_state(state, cfg)
            log.info(f"state.json saved — run #{state['run_count']}")

        elapsed = round(time.time() - t0, 1)
        log.info(f"=== COMPLETE === {elapsed}s | {len(records)} articles | {dominant}")
        return {"status": "ok", "records": len(records), "classification": dominant,
                "avg_tone": avg_tone, "checksum": checksum}

    except Exception as e:
        log.error(f"PIPELINE FAILED: {e}")
        state["handoff_note"] = f"ERROR {datetime.now().isoformat()[:10]}: {str(e)[:60]}"
        _save_state(state, cfg)
        return {"status": "error", "error": str(e)}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry", action="store_true")
    args = parser.parse_args()
    result = run(AGENT_CONFIG, dry=args.dry)
    print("Result:", result)
