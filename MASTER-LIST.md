# STUDIO SYSTEM — MASTER AGENT & TOOL LIST
Last updated: 2026-03-16

Legend:
  [BUILT]    = exists and working
  [FILE]     = .md file created, not yet deployed
  [SETUP]    = needs setup steps, not code
  [BUILD]    = needs to be built (code or .md file)
  [RESEARCH] = promising, needs deeper evaluation before committing
  [DEFER]    = valid but not needed until later milestone
  [BLOCKED]  = waiting on external dependency

Priority:
  P0 = do this session or next session — blocking or high daily impact
  P1 = this week — meaningful productivity gain
  P2 = this month — important but not urgent
  P3 = when milestone is hit — deferred for a reason
  P4 = future / aspirational

---

## FOUNDATION

| Item | Status | Priority | Notes |
|---|---|---|---|
| studio.html | BUILT | — | v4, Drive connected, reconciler working |
| studio-config.json | BUILT | — | API key file, static, never changes |
| Google Drive integration | BUILT | — | read-write scope, re-auth needed after scope change |
| Live Server (VS Code ext) | BUILT | — | opens studio at localhost:5500 |
| Pixel Agents - Hootbu | BUILT | — | visual agent floor view |
| Claude Code CLI | BUILT | — | v2.1.76, working on both machines |

---

## TIER 0 — GOVERNANCE (already built)

| Agent | Status | Priority | File | Notes |
|---|---|---|---|---|
| Stress Tester — The Asshole | BUILT | — | stress-tester.md | 5 modes, daily/weekly triggers |
| Intel Feed | BUILT | — | intel-feed.md | web vuln/deprecation scan, weekly |
| Stress self-review (Mode 4) | BUILT | — | part of stress-tester.md | runs weekly |

---

## TIER 1 — BUILD NOW (Layer 1 — no dependencies)

| Agent | Status | Priority | File | Notes |
|---|---|---|---|---|
| Janitor | FILE | P0 | janitor.md ✓ | Studio inbox stubs wired. Run in Claude Code. |
| SRE Scout (health check) | BUILD | P0 | sre-scout.md needed | Startup script: Node/Python versions, .env files, API pings, stale state.json flags. Simple bash + Claude Code mode. |
| Git Scout | FILE | P0 | git-scout.md ✓ | Scans for Git tools, maps to gaps, generates tasks. Run once first. |
| Context cliff guard | BUILD | P0 | Add to all CLAUDE.md files | One rule: /compact at 70% context. Prevents session loss. |
| Market Scout (eBay-scoped) | BUILD | P1 | market-scout.md needed | eBay sold comps, category trends. Plugs into Arbitrage Pulse + Listing Optimizer. |

---

## TIER 2 — BUILD NEXT (depend on Tier 1 being stable)

| Agent | Status | Priority | File | Notes |
|---|---|---|---|---|
| eBay agent | BUILD | P1 | ebay-agent.md needed | Listing optimizer + arbitrage logic. Needs Market Scout first. |
| Job Search agent | BUILD | P1 | job-search-agent.md needed | Whatnot + Job Match. Needs Market Scout signals. |
| Git commit agent | BUILD | P1 | Add to CLAUDE.md | Auto-commits at session end using state.json nextAction as message. |
| Agent roster panel (studio) | BUILD | P1 | Add to studio.html | Lists all agents, status, last run, compatible inbox tasks. Ties Pixel Agents idle view to dispatch. |
| Task dispatch (studio) | BUILD | P1 | Add to studio.html | Match idle agent type to inbox item. One-click prompt copy. |
| Orchestrator | BUILD | P2 | orchestrator.md needed | Cross-project planning. Needs L1 agents stable first. |

---

## TIER 3 — QUALITY CONTROL (needs projects active)

| Agent | Status | Priority | File | Notes |
|---|---|---|---|---|
| Stress Tester | BUILT | — | — | Already deployed. Gets smarter as projects mature. |
| Intel Feed | BUILT | — | — | Already deployed. Run weekly. |
| Changelog agent | BUILD | P2 | changelog-agent.md needed | Reads session logs + state.json diffs. Writes CHANGELOG.md per project. |
| Test runner agent | BUILD | P2 | Add to CLAUDE.md | Runs tests after every session. Reports failures to inbox. |
| Dependency updater | BUILD | P2 | dependency-agent.md needed | npm audit, pip check. Intel feed partially covers this. |

---

## TIER 4 — GOVERNANCE (needs active agents to govern)

| Agent | Status | Priority | File | Notes |
|---|---|---|---|---|
| Supervisor | BUILD | P2 | supervisor.md needed | Cross-agent QA + conflict resolution. Needs L1+L2 running. |
| Audit logger | BUILD | P2 | audit-logger.md needed | What agents did and when. Governance trail. |
| Kill switch | BUILD | P3 | kill-switch.md needed | Stops runaway agents. Low urgency until more agents are active. |
| Cost monitor | BUILD | P2 | cost-monitor.md needed | API token spend per project. Alert on budget breach. |

---

## TIER 5 — REVENUE AGENTS (build when core is stable)

| Agent | Status | Priority | File | Notes |
|---|---|---|---|---|
| Talent Agency (character gen) | BUILD | P3 | talent-agency.md needed | Needs CTW Phase 3 closer to done. |
| Story Generator | BUILD | P3 | story-gen.md needed | CTW scenario library. Needs Talent Agency first. |
| Patent Scout | BUILD | P2 | patent-scout.md needed | PatentsView API. Directly relevant to AcuScan AR research now. |
| Public Domain upcycler | BUILD | P3 | pd-upcycler.md needed | archive.org, 1930 works. Deferred until revenue pipeline is active. |
| OS Arbitrageur | BUILD | P4 | — | GitHub trend monitoring for SaaS wrap opportunities. Future. |

---

## TIER 6 — SENTINEL AGENTS (blocked on LLC)

| Agent | Status | Priority | File | Notes |
|---|---|---|---|---|
| Sentinel Core dev | BLOCKED | P3 | — | LLC formation required. Tennessee LLC ~$300. |
| Sentinel Performer dev | BLOCKED | P3 | — | Needs Core first. |
| Sentinel Viewer dev | BLOCKED | P3 | — | Needs Performer MVP. |
| Billing agent (Stripe MCP) | BLOCKED | P3 | — | Needs LLC + payment processor first. |
| Compliance agent | BUILD | P1 | compliance-agent.md needed | Monitors LLC status, flags legal blockers. Already partially in stress tester. |

---

## TIER 7 — INFRASTRUCTURE (build as needed)

| Item | Status | Priority | Notes |
|---|---|---|---|
| Drive sync (write) | BUILT | — | driveWriteStateJson + driveWriteToStudio in studio.html |
| Notifier (Discord webhook) | BUILD | P3 | Low urgency. Nice to have for long-running sessions. |
| Local AI fallback (Ollama) | SETUP | P3 | Install Ollama + LM Studio on HP Pavilion. Emergency offline. |

---

## EXTERNAL TOOLS FROM ECOSYSTEM

| Tool | Status | Priority | Action |
|---|---|---|---|
| GitHub CLI (gh) | SETUP | P0 | Run Git Scout first to check if installed. Install if not: winget install GitHub.cli |
| GitHub Actions + @claude | SETUP | P1 | Enable on project repos. @claude in PR = auto-implement. Free. |
| Repomix | SETUP | P1 | Packs entire repo into AI-readable file. Great for cold-start sessions. npm install -g repomix |
| fvadicamo/dev-agent-skills | SETUP | P1 | Git + GitHub workflow skills for Claude Code. /plugin marketplace add |
| wshobson/agents (112 agents) | RESEARCH | P2 | 112 specialized agents. Evaluate: security-scanner + code-reviewer most relevant. |
| VoltAgent/awesome-claude-code-subagents | RESEARCH | P2 | 100+ subagents. agent-installer subagent can browse/install others. |
| Parry (prompt injection scanner) | SETUP | P1 | Add to Claude Code hooks. Scans for injection attacks. Early dev but worth it for Sentinel. |
| AgentSys | RESEARCH | P2 | Drift detection + multi-agent review. Borrow patterns for Janitor upgrade. |
| Gas Town / Multiclaude | DEFER | P3 | Multi-agent orchestration. Add when 5+ agents running in parallel. |
| Ruflo / Claude Flow | DEFER | P4 | 60+ agent swarms, shared memory. Overkill for solo dev now. |
| GSD framework | SKIP | — | You already do Discuss→Plan→Execute→Verify via CONTEXT.md. |
| Claude Agent Teams | SETUP | P3 | Native Claude Code. Use for Sentinel Core + Performer parallel sessions. |
| Kiro (Amazon IDE) | RESEARCH | P3 | Spec-driven workflow IDE. Worth evaluating when Sentinel build starts. |
| Claude Cowork | RESEARCH | P2 | Task delegation + workflow management. Evaluation pending. |
| Shipyard | DEFER | P4 | Ephemeral environments for PR testing. Needs team workflow to justify. |
| CLI-Anything | RESEARCH | P3 | Makes any CLI tool agent-native. Relevant for eBay CLI + HiBid if resurrected. |
| Simone | RESEARCH | P2 | Project management workflow for Claude Code. Evaluate against current CONTEXT.md approach. |
| Ralph for Claude Code | RESEARCH | P2 | Autonomous loop until spec fulfilled. Useful for long Sentinel sessions. |

---

## STUDIO DASHBOARD FEATURES TO ADD

| Feature | Status | Priority | Notes |
|---|---|---|---|
| Agent roster panel | BUILD | P1 | Shows all agents, status, last run, compatible tasks |
| Task dispatch system | BUILD | P1 | Match agent type to inbox item, one-click prompt |
| Cost tracker panel | BUILD | P2 | Per-project API spend, budget alerts |
| Git status panel | BUILD | P2 | Shows which projects have git repos, last commit, dirty files |
| Token health display | BUILD | P2 | Per-session context % (mirrors Pixel Agents token bars) |

---

## WHAT TO SET UP RIGHT NOW (P0 actions)

These require no building — just setup steps:

1. **Install GitHub CLI**
   ```
   winget install GitHub.cli
   gh auth login
   ```
   Takes 5 minutes. Unlocks PR creation, issue management, @claude on PRs.

2. **Run Git Scout** (git-scout.md is ready)
   Open Claude Code in _studio, load git-scout.md, run scan.
   Tells you exactly what's missing across all 10 projects.

3. **Add context cliff guard to all CLAUDE.md files**
   Add this line to every project's CLAUDE.md:
   ```
   If context usage exceeds 70%, run /compact immediately and
   update state.json with a checkpoint note before compacting.
   ```
   Takes 10 minutes across all 10 projects.

4. **Initialize git repos in active projects**
   After Git Scout confirms none exist:
   ```
   cd G:\My Drive\Projects\job-match
   git init
   git add .
   git commit -m "Initial commit — Job Match scraper in progress"
   ```
   Do this for: job-match, nutrimind, acuscan-ar, CTW

5. **Install Repomix**
   ```
   npm install -g repomix
   ```
   Then before any session: `repomix --output repomix-output.txt`
   Gives Claude Code full codebase context in one file.

6. **Add Janitor to rotation**
   janitor.md is ready in _studio.
   Run it on any paused project before resuming.
   Inbox stubs will auto-generate when projects go stale.

---

## SUMMARY COUNTS

| Category | Built | File Ready | Needs Build | Deferred/Blocked |
|---|---|---|---|---|
| Foundation | 6 | 0 | 0 | 0 |
| Governance agents | 3 | 0 | 2 | 0 |
| Tier 1 (build now) | 0 | 2 | 3 | 0 |
| Tier 2 (build next) | 0 | 0 | 6 | 0 |
| Tier 3 (quality) | 2 | 0 | 3 | 0 |
| Tier 4 (governance) | 0 | 0 | 4 | 0 |
| Tier 5 (revenue) | 0 | 0 | 5 | 0 |
| Tier 6 (Sentinel) | 0 | 0 | 1 | 3 |
| Tier 7 (infra) | 1 | 0 | 1 | 1 |
| External tools | 3 | 0 | 0 | 8 |
| Studio features | 0 | 0 | 5 | 0 |
| **TOTAL** | **15** | **2** | **30** | **12** |

**Immediate action items (P0):** 6 setup tasks above — no code required.
**Files ready to deploy:** janitor.md, git-scout.md, stress-tester.md, intel-feed.md
**Next build session targets:** SRE Scout, Market Scout, Agent Roster Panel
