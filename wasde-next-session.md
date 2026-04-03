# WASDE Pipeline — Next Session Handoff
# Generated: 2026-04-02 | From: Global Data Products mega-session

## STATUS: READY TO BUILD

Sanctions ingestor is production and proven. WASDE is next.

## WHAT TO TELL THE NEW CLAUDE

"Read G:\My Drive\Projects\_studio\STUDIO_BRIEFING.md — that is your full context.
Today's directive: Build the WASDE Food Cost Alert pipeline agent using the
Tier 1 pipeline template at G:\My Drive\Projects\_studio\tier1_pipeline_template.py.
Read the template fully before writing any code.
Also read G:\My Drive\Projects\_studio\sanctions_ingestor.py as a working example.
The deploy guide is at G:\My Drive\Projects\_studio\TIER1_DEPLOY_GUIDE.md."

## WASDE SPECIFICS

Source: USDA WASDE PDF — released monthly on fixed dates
Next release: April 9, 2026
URL pattern: https://www.usda.gov/oce/commodity/wasde/wasde0426.pdf
  (format: wasde + month 2-digit + year 2-digit + .pdf)
  Calendar: https://usda.gov/oce/commodity/wasde

Parser: pdfplumber (pip install pdfplumber)
  - Extract text from all pages
  - Find commodity tables: Wheat, Corn, Soybeans, Cotton, Rice
  - Key fields per commodity: Production, Domestic Use, Exports, Ending Stocks
  - Changes from prior month = the signal (not absolute values)

Synthesis prompt goal:
  - Plain English cost impact for food procurement buyers
  - Per commodity: is supply tighter or looser vs last month?
  - One sentence per commodity: "Wheat: USDA cut production 50M bushels — bearish for prices"
  - Add neutral/mixed output for ambiguous months (Data Strategist warning)

## KNOWN FAILURE MODES TO FIX IN SYNTHESIS PROMPT
(from Sim 1 — 4 dangerous wrong calls in 24 months)
1. Seasonal reversal: early harvest = MORE supply = BEARISH (not bullish)
2. La Nina causal chain: La Nina dry = South American drought = supply CUT = BULLISH
3. Production vs demand: production cut = tighter supply = BULLISH for price
4. Ambiguous signal: output "mixed/neutral" not a forced directional call

## SYNTHESIS VALIDATOR (mandatory before launch)
Build a backtesting harness that:
- Downloads last 12 months of WASDE PDFs
- Runs synthesis prompt on each
- Compares directional call (bullish/bearish) to actual 30-day price movement
- Target: >88% accuracy, <8% dangerous wrong calls
- Add 2 weeks to timeline if validator catches failures

## AGENT CONFIG VALUES TO USE
agent_id: wasde-parser
pool_number: 56
ttl_seconds: 600 (PDF download can be slow)
source_cadence: monthly
stale_after_hours: 720 (30 days)
synthesize_task: reasoning (Mistral fallback — Claude credits currently depleted)
classify options: BULLISH | BEARISH | NEUTRAL | EMPTY (not URGENT/ROUTINE)

## STUDIO STATE
- ai_gateway.py: billing gate added, _call_anthropic reads error body properly
- Anthropic credits: DEPLETED — synthesis routes to Mistral Large (free) automatically
- Sanctions ingestor: PRODUCTION, running nightly at 02:00
- tier1_pipeline_template.py: proven end-to-end, use as base
- CLAUDE.md rules in force: Bezos, Hamilton, Hopper, Codd, Shannon, Gall

## DELIVERY TARGET
Newsletter tier first (free subscribers), not API.
Output: formatted email-ready HTML digest, not just JSON.
Beehiiv API key needed in studio-config.json before email delivery works.
