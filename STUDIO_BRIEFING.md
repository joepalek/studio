# STUDIO BRIEFING
*Auto-generated context for new Claude sessions. Read this file first.*
*Updated: 2026-04-04 | Owner: Joe Palek | Studio: G:\My Drive\Projects\_studio*

---

## WHO YOU ARE TALKING TO

Joe runs a multi-agent AI studio from Windows. He is the executive director.
You are a reasoning engine. You do not manually manage files or run agents.
The supervisor agent and Python scripts do the mechanical work.
Joe gives directives. You translate them into specific file edits, script commands, or agent dispatches.

---

## STUDIO ROOT

```
G:\My Drive\Projects\_studio\
```

All paths below are relative to this root unless noted.

---

## CURRENT TOP DIRECTIVE (Apr 1 2026)

**Maximize daily free-tier image and video generation for art department.**
- Agency has 283 built character folders (all specs passed, all folders created)
- Characters need to move from agency → CX agent → art department daily image pipeline
- Art dept should be generating as many images/videos per day as free quotas allow
- Goal: high-quality content that doesn't need revision — maximum throughput, not maximum volume

---

## AGENCY STATUS

| Item | Value |
|------|-------|
| Total passing specs | 283 |
| Total character folders built | 507 (some duplicates from two build runs) |
| Last build run | 2026-03-30 13:15 |
| Build log | `agency/spec-queue/build-log.json` |
| Character folders | `agency/characters/{universe}/{name}_{id}/` |
| Universes | band-members (49), inmates-vs-guards (84), other (30), original-fiction (120) |
| Historical figures | `agency/historical-figures/` — Tesla, da Vinci, Darwin, Curie, Galileo specs exist |

**Character folder path pattern:**
`agency/characters/band-members/Sam Torres_c001/`

**Passing specs file:** `agency/spec-queue/passing-specs.json`
All 283 specs have `status: "ungraded"` — grading/scoring not yet wired to CX agent scan.

---

## CX AGENT

| Item | Value |
|------|-------|
| Script | `cx_agent/cx_agent.py` |
| Integration guide | `cx_agent/CX_Agent_Integration_Guide.md` |
| Manifest (routing rules) | `cx_agent/asset_distribution_manifest.json` |
| Task Scheduler | `\Studio\CX_Agent_Daily_Scan` (2 AM daily) + `\Studio\CX_Agent_Hourly_Monitor` |
| Logs | `cx_agent/logs/` |
| Data | `cx_agent/data/` |

**CX Agent role:** Quality gate. Receives assets from creator agents, validates format+quality+brand,
routes to final destination, tracks usage, feeds social media intel.
Pass threshold: quality >= 8.

**What CX agent does NOT yet do:**
- Pick characters from agency and dispatch to art department
- Track per-character image generation status
- Report art dept quota usage back to supervisor

---

## ART DEPARTMENT / IMAGE GENERATION

**Free tier quota stack (confirmed live as of 2026-04-01):**

| Provider | Daily Free | API? | Best For |
|----------|------------|------|---------|
| Cloudflare FLUX.1 Schnell | ~50-100 images/day | YES | Volume — API wired |
| Ideogram 2 | ~10 images/day | YES | Text-in-image, logos |
| Playground v3 | ~30 images/day | No | Aesthetic quality |
| Kling 1.6 | daily credits | No | Video — character motion |
| Hailuo MiniMax | generous daily | No | Video — highest volume free |

**Combined free target: ~90-140 images/day via API before touching paid.**

**Art dept script status:** `art_dept_daily.py` — NOT YET BUILT.
This is the missing piece. It should:
1. Pull N characters from agency folders
2. Generate image prompts from character spec (visual_hint + personality_traits + universe)
3. Call Cloudflare FLUX API → save images to character folder
4. Log quota usage to `art-dept-log.json`
5. Report to supervisor inbox on completion

---

## AI GATEWAY (model routing)

**File:** `ai_gateway.py`
**Usage:** `from ai_gateway import call, score, classify, batch, reason, fast, local, premium`

All LLM calls go through the gateway. It routes to free providers first, falls back automatically.

| task_type | Primary Free Route |
|-----------|--------------------|
| scoring | Gemini 2.5 Flash |
| classification | Gemini 2.5 Flash → Groq 8B |
| batch | Groq Llama 3.3 70B |
| reasoning | Mistral Large → Groq Qwen3 32B |
| coding | Mistral Codestral |
| speed | Groq Llama 3.3 70B |
| local | Ollama gemma3:4b |
| quality | Claude Sonnet 4.6 (paid — last resort only) |

**Connected providers:** Anthropic, Gemini, Groq, Cerebras, Mistral, OpenRouter, GitHub Models,
Cloudflare, Cohere, Ollama. Keys in `studio-config.json`.

**Provider health:** `provider-health.json` — tracks OK/degraded/defunct per model.
Run `python provider_health.py` for current status report.

---

## SUPERVISOR

**File:** `supervisor.md` — read this to understand supervisor role and routing rules.
**Script:** `supervisor_check.py` — runs every 30 min via `\Studio\SupervisorCheck`.
**Inbox:** `supervisor-inbox.json` — supervisor writes findings here for human review.

Supervisor assigns `task_type` to every LLM task so gateway routes correctly.
Supervisor does NOT manually pick model strings.

---

## KEY FILE LOCATIONS

| What | Where |
|------|-------|
| Studio config (keys) | `studio-config.json` — NEVER commit to git |
| Model registry | `model-registry.json` — all providers, models, free limits |
| AI services rankings | `ai-services-rankings.json` — generated daily 5:30 AM from registry |
| Whiteboard | `whiteboard.json` — 46 items, top: Higgsfield Backwards Design (9/10) |
| Supervisor inbox | `supervisor-inbox.json` |
| Daily digest | `daily-digest.json` |
| Gateway log | `gateway-log.txt` |
| Provider health | `provider-health.json` |
| Nightly rollup | `nightly_rollup.py` — runs 1 AM, writes daily-digest |
| Session handoff | `session-handoff.md` — quick state snapshot |
| CLAUDE.md rules | `G:\My Drive\Projects\CLAUDE.md` — behavioral constitution |

---

## TASK SCHEDULER — ACTIVE TASKS

| Task | Schedule | Script |
|------|----------|--------|
| NightlyRollup | 1:00 AM | `nightly_rollup.py` |
| AIIntel | 2:13 AM + 5:00 AM | `ai_intel_run.py` |
| OvernightProductArchaeology | 2:00 AM (scrape) + 8:00 AM (score) | `product_archaeology_run.py` |
| OvernightJobDelta | 3:00 AM | `job_daily_harvest.py` |
| OvernightWhiteboardScore | 4:00 AM | `whiteboard_score.py` |
| AIServicesRankings | 5:30 AM | `ai_services_rankings.py` |
| AgencyCharacterBuild | 5:30 AM | `agency/character_batch_builder.py` |
| SidebarInject | 6:00 AM | `inject_sidebar_data.py` → `rebuild_sidebar.py` |
| CheckDrift | 6:00 AM | `check_drift.py` |
| ModelValidator | 6:30 AM | `model_validator.py` |
| SupervisorCheck | Every 30 min | `supervisor_check.py` |
| OvernightVintageAgent | Monday 1:00 AM | `vintage_agent.py` |
| Janitor | Monday 7:00 AM | `janitor_run.py` |
| GitCommitNightly | 11:00 PM | `git_commit.py` |
| CX_Agent_Daily_Scan | 2:00 AM | `cx_agent/cx_agent.py` |
| CX_Agent_Hourly_Monitor | Hourly | `cx_agent/cx_agent.py` |

---

## WHAT NEEDS TO BE BUILT (priority order)

1. **`art_dept_daily.py`** — HIGHEST PRIORITY
   - Pull characters from `agency/characters/`
   - Generate image prompts from spec fields: `visual_hint`, `personality_traits`, `archetype`, `universe`
   - Call Cloudflare FLUX API (key in studio-config: `Cloudflare API Token`, account: `Cloudflare account ID`)
   - Save generated images to character folder as `portrait_001.png` etc.
   - Log to `art-dept-log.json`: character_id, image_count, provider, quota_used, timestamp
   - Register in Task Scheduler: daily after 6:30 AM

2. **Agency → CX pipeline wiring**
   - CX agent should scan `agency/characters/` daily
   - Flag characters that have no images yet as `pending_art`
   - Dispatch to art dept queue

3. **Art dept quota tracker in supervisor**
   - Supervisor should know daily quota remaining per provider
   - Route image tasks to maximize free quota before hitting paid

---

## BEHAVIORAL RULES (CLAUDE.md summary)

Key named rules you must follow:
- **Pike:** Don't over-engineer. Simplest solution that works.
- **Gall:** Evolve from working systems, don't rebuild from scratch.
- **Shannon:** Handoffs under 200 tokens.
- **Hamilton:** Every scheduled task needs a TTL watchdog.
- **Codd:** 95% confidence gate on extraction — blank over wrong.
- **Bezos Rule:** API loops need a MAX_CONSECUTIVE_FAILURES=3 circuit breaker.
- **Kay:** Supervisor sends goals not scripts.

---

## SIDEBAR

Live dashboard running in Opera sidebar panel.
File: `sidebar-agent.html`
Tabs: STATUS | INBOX | CHAT | PLAN | ASSETS | DATA | CFG
Assets tab → AI Services sub-panel shows all 53 models across 7 categories.
Refresh sidebar after running `inject_sidebar_data.py`.

---

## HOW TO START A NEW SESSION

Tell the new Claude:
```
Read G:\My Drive\Projects\_studio\STUDIO_BRIEFING.md — this is your full context.
Then read G:\My Drive\Projects\_studio\supervisor-inbox.json for pending items.
Today's directive: [your directive here]
```

That's all a new session needs to operate at full capacity.
