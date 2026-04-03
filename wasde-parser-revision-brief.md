# WASDE Parser — Expert Panel Revision Brief
# Generated: 2026-04-02 | Source: 16-expert think tank review of March 2026 dry run

## STATUS
Parser ran successfully end-to-end against wasde0326.pdf.
Pipeline mechanics work. Data extraction is wrong. Four critical fixes required before April 9.

---

## CRITICAL FIX 1 — Switch to extract_table() (root cause of all number errors)

Current: parse_raw() uses pdfplumber extract_text() which linearizes table content.
This destroys WASDE's columnar alignment and causes field bleed between commodities.

Fix: Replace extract_text() with pdfplumber's extract_table() API per commodity section.
WASDE PDFs have proper table objects. extract_table() preserves column positions.

Expert source: Dr. Amir Hassan (Ag Data Scientist), Alex Morgan (Sr. Engineer) — independent agreement.

Example approach:
  for page in pdf.pages:
      tables = page.extract_tables()
      for table in tables:
          # table is a list of rows, each row is a list of cell strings
          # Row 0 = header, col 0 = label, col 1 = current estimate, col 2 = prior month

WASDE column structure: [Row label | Current estimate | Prior month estimate | Prior year]

---

## CRITICAL FIX 2 — Add plausibility bounds validation after parse_raw()

Current: Parser accepts any number that matches regex. No magnitude check.
Result: Wheat production 0.5 MB accepted (real value: ~1,700 MB). 
        Corn ending stocks 0.2 MB accepted (real value: ~1,400 MB).

Fix: Add a WASDE_BOUNDS dict and reject/blank values outside range before normalization.

Known U.S. ranges (million bushels unless noted):
  Wheat production:    1,500 — 2,500 MB
  Corn production:    13,000 — 15,500 MB
  Corn ending stocks:    900 — 2,200 MB
  Soybeans production: 4,000 — 4,800 MB
  Rice production:       180 —   250 MB (million cwt)
  Cotton production:   14,000 — 20,000 (thousand bales)

Codd Rule: if value outside bounds → blank the field, log warning, downgrade confidence.

---

## CRITICAL FIX 3 — Domestic use field extraction (blank for all 5 commodities)

Current: domestic_use blank for every commodity — systematic parse failure.
Likely cause: WASDE labels this row differently per commodity.
  Wheat: "Food Use" + "Feed & Residual" + "Exports" summed as "Total Domestic Use"
  Corn: "Feed & Residual" + "Food/Seed/Industrial" 
  Soybeans: "Crushings" is primary domestic use proxy

Fix: Add commodity-specific row label variants to the domestic_use search:
  domestic_use_labels = [
      "DOMESTIC USE", "TOTAL DOMESTIC USE", "TOTAL USE",
      "FOOD, SEED & INDUSTRIAL", "FEED & RESIDUAL", "CRUSHINGS"
  ]
Match the first label found in each commodity section.

---

## CRITICAL FIX 4 — Confidence rating calibration

Current: Confidence ★★★ assigned if ≥3 fields found — regardless of plausibility.
Result: Cotton and Rice show ★★★ but values are wrong.

Fix: Confidence must require BOTH field count AND plausibility bounds pass:
  high   = ≥3 fields found AND all values within WASDE_BOUNDS
  medium = ≥2 fields found OR values within bounds but incomplete
  low    = <2 fields OR any value outside bounds → blank all fields (Codd)

---

## SECONDARY ISSUE — Synthesis prompt classification flag

Expert: Dr. Priya Nair (Agricultural Economist, Rabobank)
Issue: Report classified NEUTRAL because prior data was missing — not because signals were mixed.
"No data to compare" is a different situation than "mixed signals."

Fix: Add a data quality flag to synthesis output:
  If prior_month values missing for majority of commodities:
    append line: "Note: Prior month comparison unavailable — directional confidence is low."
  Synthesis should distinguish: NEUTRAL (mixed signals) vs NEUTRAL (insufficient data)

---

## SECONDARY ISSUE — Cotton unit detection

Cotton uses 1,000 bales not million bushels.
Current unit detection finds "million_bushels" for cotton incorrectly.
Fix: detect "1,000 BALES" or "UPLAND COTTON" section → set unit = "thousand_bales"

---

## WHAT IS WORKING — DO NOT CHANGE

- Pipeline architecture (fetch → normalize → classify → synthesize → deliver) is correct
- Synthesis prompt failure mode guards (seasonal reversal, La Nina, production vs demand) are well-designed
- HTML digest format and tone validated by food manufacturer and supply chain experts
- Overall NEUTRAL classification for March 2026 is approximately correct directionally
- Beehiiv delivery stub wiring is correct
- Bezos/Hamilton/Hopper rule enforcement is solid

---

## RECOMMENDED TEST AFTER FIXES

Run: python wasde_march_test.py --dry
Verify:
  - Wheat production: 1,500-2,500 MB range
  - Corn production: 13,000-15,500 MB range
  - Domestic use populated for at least 3 of 5 commodities
  - Cotton unit shows "thousand_bales" not "million_bushels"
  - Prior month values populated for at least 3 of 5 commodities
  - Confidence ★★★ only on plausibility-validated records

Target: 4 of 5 commodities with high-confidence, plausibility-validated extraction
before April 9 production run.

---

## EXPERT PANEL SOURCE
16 domain experts reviewed March 2026 dry run output in expert panel chat.
Personas: Grain producer, commodity trader, agribusiness, livestock/dairy, input supplier,
financial economist, USDA analyst, food manufacturer, meatpacker, biofuel analyst,
data analyst, engineer, supply chain analyst, ag data scientist, data engineer, climate analyst.
Critical issues: 4 | Concerns: 5 | Acceptable: 4 | Avg rating: 3.4/5
