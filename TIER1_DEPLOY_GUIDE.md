# Tier 1 Pipeline — How to Deploy a New Pool Agent
*Read this once. Takes ~30 minutes per pool.*

---

## What you're building

A fully autonomous overnight agent that:
1. Pulls raw data from a source API/feed/URL
2. Normalizes it with Gemini Free (no cost)
3. Classifies it with Ollama (local, no cost)
4. Synthesizes a plain-English summary with Claude
5. Writes output files + updates daily-digest.json + updates state.json
6. Pushes URGENT alerts to supervisor inbox

Zero human touch after setup. All rules enforced automatically.

---

## Step 1 — Copy the template

```
copy "G:\My Drive\Projects\_studio\tier1_pipeline_template.py" ^
     "G:\My Drive\Projects\_studio\agents\YOUR_AGENT_NAME.py"
```

---

## Step 2 — Fill in AGENT_CONFIG (top of file)

Only touch the CONFIG block. Everything else is framework.

| Field | What to put |
|-------|-------------|
| agent_id | short slug, no spaces: `sanctions-ingestor` |
| pool_name | human label from the pool catalog |
| pool_number | pool # (1–101) |
| ttl_seconds | how long before Hamilton kills it (300 = 5 min) |
| source_cadence | `daily` / `weekly` / `monthly` |
| stale_after_hours | Hopper threshold — 25 for daily, 170 for weekly |
| source_url | the actual data URL |
| source_format | `json` / `xml` / `csv` / `pdf` / `rss` / `api` |
| synthesis_prompt | what you want Claude to say about the data |
| synthesize_max_tokens | 200–500 for summaries |
| classify_prompt | instructions for ROUTINE/NOTABLE/URGENT/EMPTY label |
| deliver_* | set True/False per channel |
| output_dir | where to write files |
| state_path | where to track run state |
| log_path | where to write logs |

---

## Step 3 — Implement fetch_raw()

Replace the stub with real fetch logic. Examples:

**REST JSON API:**
```python
def fetch_raw(cfg):
    import urllib.request
    req = urllib.request.Request(cfg["source_url"],
          headers={"Authorization": f"Bearer {_load_cfg()['your_api_key']}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8")
```

**RSS feed:**
```python
def fetch_raw(cfg):
    import feedparser, json
    feed = feedparser.parse(cfg["source_url"])
    return json.dumps([{"title": e.title, "summary": e.summary,
                        "published": e.published, "link": e.link}
                       for e in feed.entries])
```

**WASDE PDF:**
```python
def fetch_raw(cfg):
    import urllib.request, pdfplumber, io
    with urllib.request.urlopen(cfg["source_url"], timeout=60) as r:
        pdf_bytes = r.read()
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages)
```

---

## Step 4 — Implement parse_raw()

Convert raw string to a list of dicts. Codd Rule: blank over wrong.

```python
def parse_raw(raw, cfg):
    import json
    data = json.loads(raw)
    records = []
    for item in data.get("items", []):
        records.append({
            "id":       item.get("id", ""),       # blank if missing
            "name":     item.get("name", ""),
            "date":     item.get("date", ""),
            "country":  item.get("country", ""),
            # Codd: leave fields blank, never guess
        })
    return records
```

---

## Step 5 — Test with dry run

```
cd "G:\My Drive\Projects\_studio"
python agents\YOUR_AGENT_NAME.py --dry
```

Check:
- Fetch succeeded (see log output)
- Records parsed > 0
- Gemini normalization returned valid JSON
- Ollama classification returned ROUTINE/NOTABLE/URGENT/EMPTY
- Claude synthesis returned readable text
- "[DRY RUN] Delivery skipped" appears at end

---

## Step 6 — Register with Task Scheduler

1. Copy the XML template:
```
copy "G:\My Drive\Projects\_studio\scheduler\tier1-template.xml" ^
     "G:\My Drive\Projects\_studio\scheduler\YOUR_AGENT_NAME.xml"
```

2. Edit YOUR_AGENT_NAME.xml — replace:
   - `AGENT_ID` → your agent_id slug
   - `POOL_NUMBER` → pool number
   - `AGENT_SCRIPT` → your script filename
   - `TRIGGER_HOUR` → hour to run (2 = 2 AM, stagger by 15 min per agent)
   - `TRIGGER_MINUTE` → minute to run
   - `EXPECTED_RUNTIME_SECONDS` → your ttl_seconds value

3. Register:
```
schtasks /Create /XML "G:\My Drive\Projects\_studio\scheduler\YOUR_AGENT_NAME.xml" ^
         /TN "\Studio\YOUR_AGENT_NAME" /F
```

4. Test immediately:
```
schtasks /Run /TN "\Studio\YOUR_AGENT_NAME"
```

5. Check output:
```
type "G:\My Drive\Projects\_studio\logs\YOUR_AGENT_NAME.log"
```

---

## Trigger time stagger (avoid API rate limit collisions)

Use this schedule for the first 10 Tier 1 agents:

| Agent | Trigger time |
|-------|-------------|
| sanctions-ingestor | 02:00 |
| wasde-parser | 02:15 |
| gfw-deforestation | 02:30 |
| acled-conflict | 02:45 |
| rasff-food-alerts | 03:00 |
| opencorporates-sync | 03:15 |
| acled-sovereign | 03:30 |
| ocds-tender-alerts | 03:45 |
| gdelt-sentiment | 04:00 |
| bis-debt-monitor | 04:15 |

---

## What state.json looks like after a successful run

```json
{
  "last_run": "2026-04-03T02:00:45.123456",
  "last_checksum": "a3f7c9d2b1e4",
  "last_record_count": 847,
  "last_classification": "ROUTINE",
  "run_count": 1,
  "error_count": 0,
  "pull_meta": {
    "pull_timestamp": "2026-04-03T02:00:41.000000",
    "source_url": "https://scsanctions.un.org/...",
    "byte_count": 142830,
    "checksum": "a3f7c9d2b1e4"
  },
  "handoff_note": "sanctions-ingestor ran 2026-04-03. 847 records. ROUTINE. Synthesis: No new major designations today. EU updated 3 entity entries..."
}
```

---

## Rules enforced automatically (do not bypass)

| Rule | What it does |
|------|-------------|
| Bezos | Circuit breaker: 3 consecutive fetch failures → abort, log, inbox |
| Hamilton | TTL watchdog: exceeds ttl_seconds → abort, log, inbox |
| Hopper | Freshness: checksum + pull_timestamp logged every run; staleness flagged |
| Codd | 95% confidence gate: parse_raw() must leave blanks not guesses |
| Shannon | state.json handoff_note capped at 40 words |
| Gall | Template = working base; only CONFIG + fetch/parse changes per pool |

---

## Checklist before marking an agent as production

- [ ] --dry run succeeds with real data
- [ ] state.json written correctly
- [ ] daily-digest.json entry appears
- [ ] log file written with no ERROR lines
- [ ] Task Scheduler registered and tested (schtasks /Run)
- [ ] First overnight run verified next morning
- [ ] Agent added to STUDIO_BRIEFING.md agent registry
