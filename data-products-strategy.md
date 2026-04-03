# Global Data Products — Strategy Reference
*Generated: 2026-04-02 | Session: 8-pass discovery, rating, combination, hit list, GTM, expert panel, simulation, agentic/Capybara analysis*

---

## THE SITUATION

Joe Palek — independent developer, eBay reseller, executive director of autonomous AI studio.
Employment ends May 2026. Studio revenue projects are the priority.
Studio: `G:\My Drive\Projects\_studio\` | 16+ agents | Windows Task Scheduler overnight | Claude/Gemini/Ollama stack | Opera sidebar on port 8765.

---

## PRIMARY HIT LIST (7 projects)

### P0 — Build immediately

| # | Project | Build | Ceiling | Entry Price | Mandate |
|---|---------|-------|---------|-------------|---------|
| P0-1 | Global Entity Screening API | 5wk | $3–15M/yr | $99/mo | EU 6AMLD, FATF |
| P0-2 | EUDR Deforestation Compliance Engine | 8wk | $5–20M/yr | $499/mo | EU Deforestation Reg |
| P0-3 | WASDE Food Cost Alert | 4wk (+2 validation) | $1–5M/yr | $0/$49/$249 | None — economic value |

### P1 — Build after P0 generates cash

| # | Project | Build | Ceiling |
|---|---------|-------|---------|
| P1-4 | Food Safety Alert Digest | 5wk | $1–4M/yr |
| P1-5 | Global Procurement Alert API | 6wk | $2–8M/yr |
| P1-6 | Sentinel Compliance (full entity risk) | 10wk | $10–50M/yr |
| P1-7 | PhysicalRisk.io (Climate API) | 12wk | $5–20M/yr |

### Backup projects
B1 ACLED Conflict Dashboard (4wk) | B2 Critical Minerals Scorecard (6wk) | B3 GDELT EM Sentiment Feed (5wk) | B4 BIS Housing Monitor (6wk) | B5 Carbon Credit Screener (6wk)

---

## GTM SEQUENCE (90 days)

| Week | WASDE | Entity Screening | EUDR |
|------|-------|-----------------|------|
| 1–2 | Build parser + synthesis_validator. Fix 4 prompt failure modes. | Join 3 fintech Slacks. Post beta recruitment. Apply WDPA license. | Apply WDPA license TODAY. Join EUDR LinkedIn groups. |
| 3–4 | Launch newsletter. Email delivery live. First digest published. | Beta users onboarded (sim: done wk 2–3). Begin sanctions_ingestor. | Publish free EUDR guide (gated). Book 5 discovery calls. |
| 5–6 | Pro tier launch. Stripe billing. | Disambiguation engine + entity graph (SQLite+NetworkX). | 5 discovery calls completed. |
| 7–8 | WASDE API endpoint. HackerNews Show HN. | Confidence scorer + audit log + ToS layer. | Build begins (after WDPA confirmed). |
| 9–10 | Content flywheel. SEO posts. | Webhook + API keys + test suite. ProductHunt launch. | Week 2 of 8-week build. |
| 11–12 | Annual plans. Creator partnerships. | Public launch. LinkedIn push. First paying customers. | Closed beta — 3 pilot customers. |

### Revenue targets (MRR)
| Month | WASDE | Entity | EUDR | Total |
|-------|-------|--------|------|-------|
| M2 | $245 | — | — | $245 |
| M3 | $1,200 | $990 | $1,497 | $3,687 |
| M4 | $3,000 | $5,000 | $3,000 | $11,000 |
| M6 (May 26) | $8,000 | $20,000 | $12,000 | **$40,000** |

---

## PRICING

**Entity Screening:** $99/mo Starter | $499/mo Growth | $1,990/mo Enterprise
**EUDR:** $499/mo Starter | $1,990/mo Growth | Custom Enterprise *(Finance Lead dissent: start at $1,500)*
**WASDE:** Free (3 commodities) | $49/mo Pro | $249/mo API

---

## SIMULATION FINDINGS (3 sims run)

### Sim 1 — WASDE synthesis quality: CONDITIONAL PASS
- Claude directional accuracy: 80% on clear signals
- 4 dangerous wrong calls in 24 months (17%) — all fixable prompt issues
- Fix: add explicit causal chain reasoning, neutral output option for ambiguous months
- WASDE timeline: 6 weeks (not 4) — synthesis_validator is mandatory pre-launch

**The 4 failure modes to fix in the synthesis prompt:**
1. Seasonal reversal: early harvest = MORE supply = BEARISH (not bullish)
2. La Niña causal chain: La Niña = South American drought = supply cut = BULLISH
3. Production vs demand: production cut = tighter supply = BULLISH for price
4. Ambiguous signal: output "mixed/neutral" not a forced call

### Sim 2 — AML trust deficit: ADVOCATES RIGHT
- Monte Carlo 5,000 runs: median 2.0 weeks to 5 beta users
- 90th percentile: 3 weeks. Skeptics' 8-week threshold: 0% probability
- Best channel: warm intro via creator network (2.16 qualified/week, trust=1.0)
- Second best: Fintech Slack communities (1.85/week)
- Trust deficit is real for enterprise Month 12+ — not for free-trial beta recruitment

### Sim 3 — Studio upgrade scope
- WASDE: 9 new agents, 4 reused
- Entity Screening: 10 new agents, 5 reused
- One tech risk: entity_graph_db → MITIGATED: use SQLite+NetworkX for MVP
- Biggest quick win: sanctions_ingestor (2 days)

---

## STUDIO PRE-BUILD CHECKLIST

### Blockers (must exist before Week 1)
- [ ] Create state.json for WASDE project
- [ ] Create state.json for Entity Screening project
- [ ] Create Stripe account + add key to studio-config.json (account review takes days)

### Session Zero (one focused session, ~2.5hrs total)
- [ ] Add 3 new CLAUDE.md rules: Hopper (data freshness), Delta Fallback (model routing), Codd Synthesis extension (confidence gating)
- [ ] Add Beehiiv API key to studio-config.json (free up to 2,500 subscribers)
- [ ] Add Capybara routing stub to ai_gateway.py (harness now, key when it arrives)

### Do today (not studio infra — business task)
- [ ] Email WDPA commercial license request to protectedplanet.net (2–4 week processing)

---

## EXPERT PANEL VOTES (11 experts)

| Project | 1st choice votes | 2nd choice votes | Total pts |
|---------|-----------------|-----------------|-----------|
| EUDR Compliance Engine | 4 | 6 | **14pts** |
| Entity Screening API | 5 | 2 | **12pts** |
| WASDE Food Cost Alert | 2 | 3 | **7pts** |

**Hidden unanimous view:** Every expert agreed WASDE should be built first regardless of primary vote.
**Key dissents:** GR Analyst (WASDE has no moat), SC Expert (Entity Screening too competitive for unknown vendor), Behavioral Econ (EUDR demand backloaded to enforcement events), Finance Lead (EUDR pricing too cheap — start at $1,500).
**The empirical question:** Beta recruitment speed resolves the trust deficit debate. Sim 2 says: advocates right.

---

## AGENTIC WORKFLOW TIERS (101 pools)

| Tier | Count | Description | Studio pattern |
|------|-------|-------------|----------------|
| 1 — Full agentic | 31 | Zero human touch | Overnight Task Scheduler → Gemini normalize → Claude synthesize → deliver |
| 2 — Hybrid | 38 | Auto-ingest, human reviews synthesis | Agent generates draft → Opera sidebar review queue → Joe approves → agent sends |
| 3 — Human-in-loop | 22 | Agent preps brief, human decides | EUDR borderline cases, entity disambiguation 60–90% confidence |
| 4 — Not agentic | 10 | Relationship-sold or legally constrained | Agent feeds human analyst |

**P0 project tiers:** WASDE = Tier 2 | Entity Screening = Tier 2 (Tier 3 at disambiguation edge) | EUDR = Tier 3 (borderline cases)

---

## CAPYBARA / MYTHOS STATUS

Confirmed via Fortune leak + Anthropic acknowledgment (March 26–31, 2026).
New fourth tier above Opus. "By far the most powerful AI model we've ever developed."
Currently: early access testing, expensive to serve, not general release.
Capybara v8 in iteration. Known issue: 29–30% false claims rate (regression from v4's 16.7%).
Two leaked draft names: "Mythos" (v1) and "Capybara" (v2) — same model, name undecided.
Estimated general availability: 2–6 months.

### Impact on portfolio
| Project | Opus 4.6 | With Capybara | Delta |
|---------|----------|---------------|-------|
| WASDE | 80% accuracy, 6wk build | ~90–93% accuracy, 4wk build | -2 weeks, validation penalty removed |
| Entity Screening | 5wk build | 3wk build | -2 weeks, disambiguation via reasoning not rules |
| EUDR | 8wk build, manual borderline | 6wk build, 3min borderline review | -2 weeks |
| Sentinel Compliance | 10wk | 7wk | -3 weeks |
| PhysicalRisk.io | 12wk | 9wk | -3 weeks |
| Cyber Vuln Feed | NOT VIABLE | P1 viable (6wk) | Unlocked |
| TNFD Biodiversity | P2 | P1 | Promoted |

### Capybara revenue impact
| Month | Opus 4.6 MRR | Capybara MRR |
|-------|-------------|-------------|
| M3 | $3,687 | $6,200 |
| M6 | $40,000 | $55,000 |
| M9 | $85,000 | $130,000 |
| M12 | $150,000 | $240,000 |

### Studio upgrade for Capybara
1. ai_gateway.py — add Capybara as routing tier (stub now, key when available)
2. CLAUDE.md — add 3 rules: Capybara Rule, False Claims Guard, Cost Gate
3. model_validator.py — add Capybara health check + fallback to Opus 4.6
4. state.json — add capybara_eligible: true/false flag per task type

---

## DEMAND SIGNAL MONITOR (18 signals)

| Signal | Status | Threshold to act |
|--------|--------|-----------------|
| EUDR enforcement + WDPA license | ACT NOW | Apply WDPA this week |
| WASDE monthly release | ACT NOW | Fixed calendar — Apr 9, May 12, Jun 11... |
| EU 6AMLD AML pressure | ACT NOW | Build Entity Screening now |
| EU CSDDD supply chain | RISING | Build when Entity Screening hits $10K MRR |
| TNFD disclosure | RISING | Build when any G20 mandates it |
| Critical minerals demand | RISING | Build on lithium/cobalt >15% price spike |
| NIS2 + CIRCIA cyber | RISING | Add to hit list on Capybara release |
| VCM carbon market recovery | WATCH | Build when VCM volume returns to 2022 levels |
| CSRD biodiversity metrics | WATCH | Build when ESRS E4 finalized |
| OpenSky coverage expansion | WAIT | Build when >65% global flight coverage |
| Orbital debris | WAIT | Build after first major satellite collision event |

---

## KEY POOL SOURCES (P0 projects)

**Entity Screening:** OpenCorporates (#55) | Sanctions Lists 30+ jurisdictions (#73) | TJN FSI (#67) | Basel AML Index (#99) | GDELT adverse media (#37)
**EUDR:** Global Forest Watch + FIRMS (#24) | WDPA Protected Areas (#65) | GBIF Species (#81) | IUCN Red List (#85) | Global Mining Footprint (#38)
**WASDE:** USDA WASDE (#56) | FAO Food Outlook | FAO Food Price Instability (#74) | Baltic Dry/FBX (#57)

---

## CROSS-POOL COMBINATION SCORES (top 7 S-tier)

| Combination | Score | Ceiling | Build |
|------------|-------|---------|-------|
| Sentinel Compliance | 9.0 | $10–50M/yr | 6wk |
| PhysicalRisk.io | 9.0 | $5–20M/yr | 10wk |
| Global Entity Screening | 8.8 | $3–15M/yr | 5wk |
| EM Sovereign Stress Monitor | 8.7 | $3–15M/yr | 10wk |
| EUDR Compliance Engine | 8.7 | $5–20M/yr | 8wk |
| Agri Intelligence Platform | 8.5 | $3–10M/yr | 10wk |
| Global Health Market Intelligence | 8.5 | $5–20M/yr | 12wk |

---

*Full session transcript indexed in journal.txt | Simulation code at /home/claude/wasde_aml_sim.py*
*Next action: Studio pre-build checklist → Session Zero → Week 1 WASDE build*
