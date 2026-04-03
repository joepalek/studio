"""
wasde_full_product_run.py
=========================
Generates all three FCI subscription tier outputs from March 2026 WASDE.
Produces:
  data/wasde/fci-free-march-2026.html       — Free tier newsletter
  data/wasde/fci-pro-march-2026.html        — Pro tier full report
  data/wasde/fci-institutional-march-2026/  — Institutional package
    ├── fci-inst-march-2026.html            — Full HTML report
    ├── fci-inst-march-2026.json            — Data API payload
    ├── fci-inst-march-2026.csv             — CSV export
    └── fci-inst-march-2026-slack.txt       — Slack digest format
"""
import sys, json, csv, os
from datetime import datetime
from pathlib import Path

sys.path.insert(0, "G:/My Drive/Projects/_studio")
import wasde_parser

# ── CONFIG ────────────────────────────────────────────────────────
URL = "https://www.usda.gov/oce/commodity/wasde/wasde0326.pdf"
OUT = Path("G:/My Drive/Projects/_studio/data/wasde")
INST_DIR = OUT / "fci-institutional-march-2026"
INST_DIR.mkdir(parents=True, exist_ok=True)
wasde_parser.AGENT_CONFIG["source_url"] = URL

ISSUE_DATE    = "March 2026"
RELEASE_DATE  = "March 11, 2026"
NEXT_RELEASE  = "April 9, 2026"
METHODOLOGY   = (
    "Signals derived from USDA WASDE narrative text using keyword analysis. "
    "Each commodity is classified BULLISH (supply tighter), BEARISH (supply looser), "
    "or NEUTRAL (no change / ambiguous). A pre-computed signal layer corrects LLM "
    "synthesis errors. Confidence tags: [data] = numeric table extracted, "
    "[narrative] = prose-only month, [override] = keyword signal corrected LLM output."
)
ACCURACY_NOTE = "Backtest accuracy: pending (12-month validation scheduled pre-launch)."

# ── RUN PIPELINE ──────────────────────────────────────────────────
print("Fetching March 2026 WASDE PDF...")
log = wasde_parser._setup_logging(wasde_parser.AGENT_CONFIG)
raw = wasde_parser.fetch_raw(wasde_parser.AGENT_CONFIG)
records = wasde_parser.parse_raw(raw, wasde_parser.AGENT_CONFIG)
normalized = wasde_parser._normalize_with_gemini(records, wasde_parser.AGENT_CONFIG, log)
synthesis = wasde_parser._synthesize_with_mistral(normalized, wasde_parser.AGENT_CONFIG, log)
classification = wasde_parser._classify_with_ollama(normalized[:500], wasde_parser.AGENT_CONFIG, log)

print(f"Pipeline complete: {len(records)} commodities | {classification}")
print(f"\nSYNTHESIS:\n{synthesis}\n")

# ── SHARED HELPERS ────────────────────────────────────────────────
def badge_color(cls):
    return {"BULLISH":"#c62828","BEARISH":"#2e7d32","NEUTRAL":"#e65100",
            "MIXED":"#1565c0","EMPTY":"#616161"}.get(cls,"#616161")

def badge_label(cls):
    return {"BULLISH":"⚠ BULLISH — Supply Tighter","BEARISH":"✓ BEARISH — Supply Looser",
            "NEUTRAL":"→ NEUTRAL — No Significant Change","MIXED":"~ MIXED — Monitor Closely",
            "EMPTY":"— No Data"}.get(cls, cls)

def source_tag(r):
    """Return confidence source tag per expert panel request."""
    if r.get("confidence") == "high":  return "[data]"
    if r.get("signal") and r.get("signal") != "UNKNOWN" and r.get("confidence") == "low":
        sig = r.get("signal","")
        # Check if override was applied
        return "[override]" if sig in ("BULLISH","BEARISH") else "[narrative]"
    return "[narrative]"

def parse_synthesis_lines(synthesis):
    """Parse synthesis into commodity lines + overall."""
    lines = [l.strip() for l in synthesis.strip().split("\n") if l.strip()]
    commodity_lines = [l for l in lines if not l.upper().startswith("OVERALL")]
    overall = next((l for l in lines if l.upper().startswith("OVERALL")), "")
    return commodity_lines, overall

def signal_color(line):
    lu = line.upper()
    if "BULLISH" in lu: return "#c62828"
    if "BEARISH" in lu: return "#2e7d32"
    return "#e65100"

commodity_lines, overall_line = parse_synthesis_lines(synthesis)

# Determine if this is a narrative-only month
narrative_only = all(r.get("confidence") == "low" for r in records)
narrative_notice = (
    "<p style='background:#fff8e1;border-left:3px solid #f9a825;padding:10px 14px;"
    "font-size:13px;margin-bottom:16px;border-radius:0 4px 4px 0'>"
    "<strong>Note:</strong> USDA made no numerical revisions to U.S. supply &amp; demand "
    "estimates this month. This analysis is based on USDA written commentary from the "
    "WASDE narrative sections.</p>"
) if narrative_only else ""

print("Helpers loaded. Building tier outputs...")

# ── FREE TIER HTML ────────────────────────────────────────────────
def build_free_html():
    comm_html = "".join(
        f"<p style='margin:6px 0;padding:8px 0;border-bottom:0.5px solid #f0f0f0;"
        f"font-size:14px;line-height:1.6'>{l}</p>"
        for l in commodity_lines
    )
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>FCI Food Cost Intelligence — {ISSUE_DATE}</title></head>
<body style="font-family:Georgia,serif;color:#222;max-width:600px;margin:0 auto;padding:24px 16px">
<div style="border-bottom:3px solid #1a1a1a;padding-bottom:12px;margin-bottom:20px">
  <p style="margin:0 0 2px;font-size:11px;color:#888;text-transform:uppercase;letter-spacing:.08em">FCI Food Cost Intelligence</p>
  <h1 style="margin:0;font-size:24px;letter-spacing:-.5px">WASDE Alert — {ISSUE_DATE}</h1>
  <p style="margin:4px 0 0;color:#666;font-size:13px">USDA World Agricultural Supply and Demand Estimates &nbsp;|&nbsp; {RELEASE_DATE}</p>
</div>
<div style="background:{badge_color(classification)};color:#fff;padding:10px 16px;
  border-radius:4px;font-size:15px;font-weight:bold;margin-bottom:20px">
  {badge_label(classification)}
</div>
{narrative_notice}
<h2 style="font-size:15px;font-weight:600;margin:0 0 10px;border-bottom:1px solid #eee;padding-bottom:6px">
  Procurement Analyst Summary</h2>
<div style="margin-bottom:24px">{comm_html}
  <p style="margin:12px 0 0;padding:10px 14px;background:#f8f8f8;border-radius:4px;
    font-size:13px;font-style:italic;color:#555">{overall_line}</p>
</div>
<div style="background:#f8f9ff;border:1px solid #e0e6ff;border-radius:6px;
  padding:14px 16px;margin-bottom:24px;font-size:13px">
  <strong>Next WASDE release:</strong> {NEXT_RELEASE}<br>
  <strong>Methodology:</strong> Directional signals derived from USDA narrative text analysis.
  <a href="https://www.usda.gov/oce/commodity/wasde/wasde0326.pdf"
    style="color:#1a5fb4">View source PDF</a>
</div>
<div style="border-top:1px solid #eee;padding-top:12px;font-size:11px;color:#aaa;line-height:1.8">
  <p style="margin:0">{ACCURACY_NOTE}</p>
  <p style="margin:4px 0 0">{METHODOLOGY}</p>
  <p style="margin:8px 0 0"><strong style="color:#888">Upgrade to FCI Pro</strong> for full numeric tables,
  U.S. vs global breakdowns, confidence tags, and 12-month trend data.</p>
  <p style="margin:4px 0 0">For procurement guidance only. Verify with USDA source before trading decisions.</p>
</div>
</body></html>"""

free_path = OUT / "fci-free-march-2026.html"
free_path.write_text(build_free_html(), encoding="utf-8")
print(f"FREE tier written: {free_path}")

# ── PRO TIER HTML ─────────────────────────────────────────────────
def build_pro_html():
    # Data table rows — show narrative source when no numeric data
    table_rows = ""
    for r in records:
        conf = r.get("confidence","low")
        tag  = source_tag(r)
        sig  = r.get("signal","UNKNOWN")
        sig_color = {"BULLISH":"#c62828","BEARISH":"#2e7d32","NEUTRAL":"#888","UNKNOWN":"#aaa"}.get(sig,"#888")
        prod = r.get("production","") or "—"
        prior_p = r.get("prior_production","") or "—"
        stocks  = r.get("ending_stocks","") or "—"
        prior_s = r.get("prior_ending_stocks","") or "—"
        dom_use = r.get("domestic_use","") or "—"
        exports = r.get("exports","") or "—"
        unit    = r.get("unit","").replace("_"," ") or "—"
        table_rows += f"""<tr>
          <td style="padding:8px 10px;font-weight:600;border-bottom:0.5px solid #f0f0f0">{r['commodity']}</td>
          <td style="padding:8px 10px;text-align:right;border-bottom:0.5px solid #f0f0f0">{prod}</td>
          <td style="padding:8px 10px;text-align:right;border-bottom:0.5px solid #f0f0f0;color:#888">{prior_p}</td>
          <td style="padding:8px 10px;text-align:right;border-bottom:0.5px solid #f0f0f0">{stocks}</td>
          <td style="padding:8px 10px;text-align:right;border-bottom:0.5px solid #f0f0f0;color:#888">{prior_s}</td>
          <td style="padding:8px 10px;text-align:right;border-bottom:0.5px solid #f0f0f0">{dom_use}</td>
          <td style="padding:8px 10px;text-align:right;border-bottom:0.5px solid #f0f0f0">{exports}</td>
          <td style="padding:8px 10px;text-align:center;border-bottom:0.5px solid #f0f0f0;font-size:11px;color:{sig_color};font-weight:600">{sig}</td>
          <td style="padding:8px 10px;text-align:center;border-bottom:0.5px solid #f0f0f0;font-size:10px;color:#999">{tag}</td>
        </tr>"""

    # Narrative section per commodity
    narrative_rows = ""
    for r in records:
        narr = r.get("narrative","")
        if narr:
            narrative_rows += f"""<div style="margin-bottom:12px">
              <strong style="font-size:13px">{r['commodity']}:</strong>
              <span style="font-size:13px;color:#555"> {narr}</span>
            </div>"""

    comm_html = "".join(
        f"<p style='margin:6px 0;padding:8px 0;border-bottom:0.5px solid #f0f0f0;font-size:14px;line-height:1.6'>"
        f"<span style='color:{signal_color(l)};font-size:11px;font-weight:600;margin-right:6px'>"
        f"{'BULL' if 'BULLISH' in l.upper() else 'BEAR' if 'BEARISH' in l.upper() else 'NEUT'}</span>{l}</p>"
        for l in commodity_lines
    )

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>FCI Pro — WASDE Alert {ISSUE_DATE}</title></head>
<body style="font-family:Georgia,serif;color:#222;max-width:700px;margin:0 auto;padding:24px 16px">
<div style="border-bottom:3px solid #1a1a1a;padding-bottom:12px;margin-bottom:20px;display:flex;justify-content:space-between;align-items:flex-end">
  <div>
    <p style="margin:0 0 2px;font-size:11px;color:#888;text-transform:uppercase;letter-spacing:.08em">FCI Pro — Food Cost Intelligence</p>
    <h1 style="margin:0;font-size:24px;letter-spacing:-.5px">WASDE Alert — {ISSUE_DATE}</h1>
    <p style="margin:4px 0 0;color:#666;font-size:13px">{RELEASE_DATE}</p>
  </div>
  <div style="text-align:right;font-size:11px;color:#888">
    <div>Next release: <strong style="color:#222">{NEXT_RELEASE}</strong></div>
  </div>
</div>
<div style="background:{badge_color(classification)};color:#fff;padding:10px 16px;
  border-radius:4px;font-size:15px;font-weight:bold;margin-bottom:20px">
  {badge_label(classification)}
</div>
{narrative_notice}
<h2 style="font-size:15px;font-weight:600;margin:0 0 10px;border-bottom:1px solid #eee;padding-bottom:6px">Analyst Summary</h2>
<div style="margin-bottom:24px">{comm_html}
  <p style="margin:12px 0 0;padding:10px 14px;background:#f8f8f8;border-radius:4px;font-size:13px;font-style:italic;color:#555">{overall_line}</p>
</div>
<h2 style="font-size:15px;font-weight:600;margin:0 0 10px;border-bottom:1px solid #eee;padding-bottom:6px">Supply &amp; Demand Data</h2>
<div style="overflow-x:auto;margin-bottom:24px">
<table style="width:100%;border-collapse:collapse;font-size:12px">
  <thead><tr style="background:#f5f5f5">
    <th style="padding:8px 10px;text-align:left;border-bottom:2px solid #ddd">Commodity</th>
    <th style="padding:8px 10px;text-align:right;border-bottom:2px solid #ddd">Production</th>
    <th style="padding:8px 10px;text-align:right;border-bottom:2px solid #ddd;color:#888">Prior</th>
    <th style="padding:8px 10px;text-align:right;border-bottom:2px solid #ddd">End Stocks</th>
    <th style="padding:8px 10px;text-align:right;border-bottom:2px solid #ddd;color:#888">Prior</th>
    <th style="padding:8px 10px;text-align:right;border-bottom:2px solid #ddd">Dom. Use</th>
    <th style="padding:8px 10px;text-align:right;border-bottom:2px solid #ddd">Exports</th>
    <th style="padding:8px 10px;text-align:center;border-bottom:2px solid #ddd">Signal</th>
    <th style="padding:8px 10px;text-align:center;border-bottom:2px solid #ddd">Source</th>
  </tr></thead>
  <tbody>{table_rows}</tbody>
</table>
{'<p style="font-size:11px;color:#aaa;margin-top:6px">— No numeric data: USDA made no numerical revisions this month. Signals derived from narrative analysis.</p>' if narrative_only else ''}
</div>
<h2 style="font-size:15px;font-weight:600;margin:0 0 10px;border-bottom:1px solid #eee;padding-bottom:6px">USDA Source Narrative</h2>
<div style="margin-bottom:24px;font-size:13px;line-height:1.7;color:#444">{narrative_rows}</div>
<div style="background:#f8f9ff;border:1px solid #e0e6ff;border-radius:6px;padding:14px 16px;margin-bottom:24px;font-size:13px">
  <strong>Signal source tags:</strong> [data] = numeric table extracted &nbsp;|&nbsp;
  [narrative] = USDA prose analysis &nbsp;|&nbsp; [override] = keyword signal corrected LLM output
</div>
<div style="border-top:1px solid #eee;padding-top:12px;font-size:11px;color:#aaa;line-height:1.8">
  <p style="margin:0">{ACCURACY_NOTE}</p>
  <p style="margin:4px 0 0">{METHODOLOGY}</p>
  <p style="margin:4px 0 0">Source: <a href="https://www.usda.gov/oce/commodity/wasde/wasde0326.pdf" style="color:#1a5fb4">USDA WASDE PDF</a></p>
</div>
</body></html>"""

pro_path = OUT / "fci-pro-march-2026.html"
pro_path.write_text(build_pro_html(), encoding="utf-8")
print(f"PRO tier written: {pro_path}")

# ── INSTITUTIONAL TIER ────────────────────────────────────────────

# 1. Full HTML (Pro + extras)
inst_html_path = INST_DIR / "fci-inst-march-2026.html"
inst_html = build_pro_html().replace(
    "FCI Pro — Food Cost Intelligence",
    "FCI Institutional — Food Cost Intelligence"
).replace(
    "Upgrade to FCI Pro",
    "FCI Institutional client"
)
# Add institutional extras header
inst_extras = f"""
<div style="background:#fffde7;border:1px solid #f9a825;border-radius:6px;
  padding:12px 16px;margin-bottom:20px;font-size:13px">
  <strong>Institutional Package</strong> — {ISSUE_DATE} &nbsp;|&nbsp;
  JSON API, CSV export, and Slack digest included below.
  <br>Climate/country risk overlay and ethanol sub-section: available on request.
</div>"""
inst_html = inst_html.replace(narrative_notice if narrative_notice else "<!-- -->",
                               inst_extras + (narrative_notice or ""))
inst_html_path.write_text(inst_html, encoding="utf-8")
print(f"INSTITUTIONAL HTML written: {inst_html_path}")

# 2. JSON API payload
inst_json = {
    "meta": {
        "product":        "FCI Food Cost Intelligence",
        "tier":           "institutional",
        "issue_date":     ISSUE_DATE,
        "release_date":   RELEASE_DATE,
        "next_release":   NEXT_RELEASE,
        "classification": classification,
        "overall":        overall_line,
        "generated_at":   datetime.now().isoformat(),
        "source_url":     URL,
        "narrative_only": narrative_only,
        "methodology":    METHODOLOGY,
        "accuracy_note":  ACCURACY_NOTE,
    },
    "commodities": [
        {
            "commodity":         r["commodity"],
            "signal":            r.get("signal","UNKNOWN"),
            "confidence":        r.get("confidence","low"),
            "source_tag":        source_tag(r),
            "production":        r.get("production",""),
            "prior_production":  r.get("prior_production",""),
            "domestic_use":      r.get("domestic_use",""),
            "exports":           r.get("exports",""),
            "ending_stocks":     r.get("ending_stocks",""),
            "prior_ending_stocks": r.get("prior_ending_stocks",""),
            "unit":              r.get("unit",""),
            "narrative":         r.get("narrative",""),
            "parse_flags":       r.get("parse_flags",[]),
        }
        for r in records
    ],
    "synthesis_lines": commodity_lines,
}
inst_json_path = INST_DIR / "fci-inst-march-2026.json"
inst_json_path.write_text(json.dumps(inst_json, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"INSTITUTIONAL JSON written: {inst_json_path}")

# 3. CSV export
inst_csv_path = INST_DIR / "fci-inst-march-2026.csv"
fieldnames = ["commodity","signal","confidence","source_tag","production","prior_production",
              "domestic_use","exports","ending_stocks","prior_ending_stocks","unit"]
with open(inst_csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for r in inst_json["commodities"]:
        writer.writerow({k: r.get(k,"") for k in fieldnames})
print(f"INSTITUTIONAL CSV written: {inst_csv_path}")

# 4. Slack digest
slack_lines = [
    f"*FCI WASDE Alert — {ISSUE_DATE}* | {badge_label(classification)}",
    "",
]
for l in commodity_lines:
    emoji = ":red_circle:" if "BULLISH" in l.upper() else \
            ":large_green_circle:" if "BEARISH" in l.upper() else ":white_circle:"
    slack_lines.append(f"{emoji} {l}")
slack_lines += [
    "",
    f"_{overall_line}_",
    "",
    f"Next release: *{NEXT_RELEASE}*  |  Source: {URL}",
]
inst_slack_path = INST_DIR / "fci-inst-march-2026-slack.txt"
inst_slack_path.write_text("\n".join(slack_lines), encoding="utf-8")
print(f"INSTITUTIONAL SLACK written: {inst_slack_path}")

# ── SUMMARY ───────────────────────────────────────────────────────
print("\n" + "="*60)
print("FCI FULL PRODUCT RUN COMPLETE")
print("="*60)
print(f"  FREE:          {OUT}/fci-free-march-2026.html")
print(f"  PRO:           {OUT}/fci-pro-march-2026.html")
print(f"  INSTITUTIONAL: {INST_DIR}/")
print(f"    - fci-inst-march-2026.html")
print(f"    - fci-inst-march-2026.json")
print(f"    - fci-inst-march-2026.csv")
print(f"    - fci-inst-march-2026-slack.txt")
print(f"\nClassification: {classification}")
print(f"Narrative-only month: {narrative_only}")
print(f"Commodities: {len(records)}")
