# STUDIO ORCHESTRATOR v2 — COMPLETE SYSTEM ARCHITECTURE

## What This System Does

**Problem:** You have 16+ agents running on Windows Task Scheduler with no unified visibility. Projects drift silently, dependencies block unknowingly, and you lose context on what's producing vs. what's just spinning.

**Solution:** A deterministic project lifecycle management system that:

1. **Tracks everything** — Every project, milestone, dependency, and asset in one SQLite DB
2. **Escalates issues** — Detects silent failures, blocks, deadline misses; emails you immediately
3. **Shows live status** — Sidebar widget updates every 60 seconds with project ticker
4. **Logs production** — Every agent logs what it created (with cost/timestamp)
5. **Auto-intakes new projects** — New ideas registered via GitHub issues, folders → auto-added
6. **Never orphans work** — New projects aren't forgotten; they stay in the system

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    STUDIO ORCHESTRATOR v2                   │
└─────────────────────────────────────────────────────────────┘

    ┌──────────────────┐
    │ studio_projects  │  SQLite database (single source of truth)
    │      .db         │  - projects, milestones, dependencies
    └────────┬─────────┘  - production_log, escalations, intake_queue
             │
             ├─────────────────┬─────────────────┬──────────────┐
             │                 │                 │              │
    ┌────────▼──────┐ ┌────────▼─────┐ ┌────────▼────┐ ┌───────▼──────┐
    │   ORCHESTRATE │ │    HEALTH    │ │    EMAIL    │ │   SIDEBAR    │
    │   (Core DB)   │ │   MONITOR    │ │   SERVICE   │ │    BRIDGE    │
    └────────┬──────┘ └────────┬─────┘ └────────┬────┘ └───────┬──────┘
             │                 │                 │              │
       [Python API]   [Daily 6 AM]      [Daily 7 AM]    [HTTP API Port 11436]
     add_project()  Detect blocks,   Send digests,    Serves JSON + HTML
     log_production() silent fails,    escalate       ticker + dashboard
     add_dependency()  deadline miss
             │
             └─────────────────────────────┬──────────────────┘
                                           │
                           ┌───────────────┴──────────────┐
                           │                              │
                    ┌──────▼──────┐            ┌──────────▼────┐
                    │  TASK SCHED │            │  OPERA SIDEBAR│
                    │  (Windows)  │            │   (Real-time) │
                    └─────────────┘            └────────────────┘
                     Daily triggers             HTML widget refresh
                     health_check()             every 60 seconds
                     send_digest()
                     wrap_agents()

    ┌──────────────────────────────────────────────────────────┐
    │               YOUR 16+ AGENTS (Unchanged)                │
    │  eBay, Game Archaeology, Art Dept, Job Discovery, etc.  │
    │                                                          │
    │  Each agent optionally calls:                           │
    │  orch.log_production(agent, project_id, asset_type, ...) │
    └──────────────────────────────────────────────────────────┘
```

## Core Components

### 1. `studio_orchestrator.py` (820 lines)

**Single Source of Truth** for all studio state.

```python
class StudioOrchestrator:
    # Project Management
    add_project(name, division, milestones, ...)
    list_projects(filters={status, division, priority_max})
    update_project_status(project_id, status)
    
    # Dependencies
    add_dependency(upstream_id, downstream_id, relationship)
    get_blocking_projects(project_id)
    get_dependent_projects(project_id)
    
    # Production Tracking
    log_production(agent, project_id, asset_type, count, cost, status)
    get_project_production(project_id, days=30)
    check_silent_failures()
    
    # Escalations
    create_escalation(project_id, type, description, severity)
    get_unresolved_escalations()
    resolve_escalation(escalation_id)
    
    # Auto-Intake
    queue_intake(title, source, source_id, division)
    get_intake_queue()
    process_intake(intake_id, project_id)
    
    # Reporting
    get_daily_status()  # 10-field snapshot
    get_weekly_status()  # Detailed accountability report
```

**Database Schema:**
- `projects` — 17 rows (eBay, Game Archaeology, Sentinel suite, etc.)
- `milestones` — Target dates, assignments, status tracking
- `dependencies` — Projects that block/feed each other
- `production_log` — Asset tracking per agent (assets, cost, timestamp)
- `escalations` — Blocks, silent fails, deadline misses
- `intake_queue` — New projects awaiting processing

**Key Design:**
- UNIQUE constraint on project names (no duplicates)
- Foreign keys enforce referential integrity
- Indices on status/division/timestamp for fast queries
- JSON fields for metadata flexibility

---

### 2. `health_monitor.py` (200 lines)

**Daily Checks** for project health issues.

```python
class StudioHealthMonitor:
    run_daily_checks()
    ├── check_silent_failures()      # 0 assets in 24h
    ├── check_blocked_projects()     # Upstream incomplete
    ├── check_missed_deadlines()     # target_date < today
    ├── check_stalled_projects()     # No activity 14d
    └── process_new_projects()       # Auto-intake queue
```

**Escalation Rules:**
- **Silent Fail (MEDIUM):** Milestone status="in_progress" but asset_count=0 in 24h
- **Blocked (HIGH):** Project has unmet dependency
- **Deadline Miss (HIGH if >7d, MEDIUM if <7d):** Milestone.target_date < today
- **Stalled (LOW):** No production for 14+ days

**Triggered:** Daily 6:00 AM via Task Scheduler
**Output:** Email escalations to joedealsonline@gmail.com

---

### 3. `email_service.py` (150 lines)

**Email Generation** for digests, reports, and escalations.

```
send_escalation_email(issues)      # On-demand, high priority
send_daily_digest()                # 7:00 AM daily
send_weekly_report()               # Monday 8:00 AM
```

**Dev Mode:** Prints to console (no SMTP needed)
**Prod Mode:** Uses Gmail SMTP (requires app password)

**Example escalation email:**
```
🚨 STUDIO ESCALATION ALERT

⛔ HIGH PRIORITY (2)
  • Sentinel Viewer is BLOCKED by: Sentinel Core
  • eBay Agent → Push 40 listings: 5 days overdue

⚠️ MEDIUM PRIORITY (1)
  • Game Archaeology ran but 0 assets in 24h
```

---

### 4. `sidebar_bridge.py` (250 lines)

**HTTP Server** providing live data to sidebar widget.

```
Port: 127.0.0.1:11436

Endpoints:
  /                              → HTML dashboard
  /api/projects/status           → All projects (JSON)
  /api/projects/ticker           → HTML ticker widget
  /api/escalations/active        → Active escalations
  /api/stats/daily               → Today's snapshot
  /api/milestones/due-week       → Next 7 days
  /api/projects/{id}/details     → Full project info
  /health                        → Health check
```

**Key Feature:** Real-time updates
- Sidebar polls every 60 seconds
- Dashboard auto-refreshes
- Escalations highlighted with blinking indicator

---

### 5. `studio_tasks.py` (300 lines)

**Task Scheduler Integration** — bridges your agents to the system.

```
Commands:
  python studio_tasks.py health_check              # 6 AM
  python studio_tasks.py digest                    # 7 AM
  python studio_tasks.py weekly_report             # Monday 8 AM
  python studio_tasks.py ensure_sidebar            # 5 AM
  python studio_tasks.py wrap_agent <name> <script> <id>
```

**Agent Wrapper** (optional):
```python
# Wraps agent execution, captures output, auto-logs production
wrap_agent_execution("ebay_agent", "path/to/ebay_agent.py", project_id=1)
```

---

### 6. `sidebar-orchestrator.html` (300 lines)

**Live Sidebar Widget** — real-time project status in Opera sidebar.

Features:
- Daily stats grid (active/blocked/assets/cost)
- Project ticker (scrollable list, color-coded by status)
- Escalation alerts (with blink animation if HIGH severity)
- Milestones due this week (with dates/agent assignments)
- Live clock (updates every 60 sec)

Color scheme:
- 🟢 **Active** — #00ff41 (terminal green)
- 🔴 **Blocked** — #ff4444 (bright red)
- 🟡 **Complete** — #64c8ff (light blue)

---

## Bootstrapped Data (17 Projects)

### Commerce (1)
- **eBay Agent** (P1, Revenue) — Identify + list inventory

### Content (4)
- **Game Archaeology** (P2, Revenue) — Weekly digest of indie games
- **Ghost Book Division** (P3) — Out-of-print book salvage
- **Art Department** (P3) — Daily free-tier image generation
- **Character Test Workbench** (P2) — Multi-provider AI character testing

### Infrastructure (6)
- **Job Discovery System** (P1) — 250K-400K jobs from 10 free sources
- **Studio Sidebar v2** (P2) — Live project ticker + RAG
- **Inbox Manager** (P2) — Task routing + Hopper schema
- **Supervisor Agent** (P1) — Goal-setting (NOT script provision)
- **Whiteboard Agent** (P2) — Idea/backlog tracking
- **AI Intel Agent** (P2) — ML research source discovery

### Research (2)
- **Gaussian Splatting Pipeline** (P4) — 3D historical figures
- **AcuScan AR** (P4) — Acupressure point scanning

### Sentinel Suite (3) — **NEW, unified intelligence system**
- **Sentinel Core** (P2) — Data aggregation + scoring engine
- **Sentinel Performer** (P1, Revenue) — Real-time marketplace alerts
- **Sentinel Viewer** (P2) — Dashboard frontend

### Backlog (1)
- **Truth Gate (Horde Shooter)** (P5) — Awaiting game dev + artist

## Data Flow Examples

### Scenario 1: Agent Produces Assets

```
1. eBay Agent runs (Task Scheduler 3 PM daily)
2. Identifies 15 items from backlog
3. Pushes 12 listings to eBay
4. Logs production:
   orch.log_production(
       agent="ebay_agent",
       project_id=1,
       asset_type="listings",
       asset_count=12,
       cost_usd=0.02,
       status="success"
   )
5. Orchestrator auto-marks next milestone as "in_progress"
6. Sidebar ticker updates (live in 60 sec)
7. Production logged to DB with timestamp

Next run (tomorrow 3 PM):
- Health check sees yesterday's production
- No escalation triggered (healthy)
- Daily digest reports "eBay: 12 listings"
```

### Scenario 2: Silent Failure Detected

```
1. Game Archaeology Agent runs (6 PM daily)
2. Task completes (no error), but produces 0 assets
3. Next day 6 AM: Health check runs
4. Query: SELECT COUNT(*) FROM production_log 
          WHERE project_id=2 AND timestamp > 24h_ago
5. Result: 0 assets
6. Create escalation:
   escalation_type="silent_fail"
   description="...ran but produced 0 assets in 24h"
   severity="medium"
7. Email sent to Joe with all escalations
8. Joe investigates: check crawler logs, API limits, etc.
9. Fix found, agent re-runs manually
10. Production logged, escalation resolved
```

### Scenario 3: Project Blocked

```
1. Sentinel Viewer depends on Sentinel Core (dependency added)
2. Sentinel Core timeline slips: milestones still "pending"
3. Sentinel Viewer team tries to start work (deadline next week)
4. Health check queries dependencies:
   SELECT p.* FROM projects p
   JOIN dependencies d ON p.id = d.upstream_project_id
   WHERE d.downstream_project_id = 11 (Sentinel Viewer)
   AND p.status != 'complete'
5. Found blocker: Sentinel Core
6. Create escalation:
   type="blocked"
   description="Project blocked by: Sentinel Core"
   severity="high"
7. Email to Joe: "BLOCKED: Sentinel Viewer waiting on Sentinel Core"
8. Joe can:
   - Expedite Sentinel Core work
   - Start Sentinel Viewer in parallel (reduce scope)
   - Adjust timeline
```

### Scenario 4: New Project Auto-Intake

```
1. You create GitHub issue: "#studio-project ML Research Agent"
2. Webhook (future) or manual call:
   orch.queue_intake(
       title="ML Research Agent",
       source="github_issue",
       source_id="gh-issue-42",
       division="Infrastructure"
   )
3. Intake queued in database
4. Next day's health check:
   intake = orch.get_intake_queue()  # Returns new item
   project_id = orch.add_project(
       name="ML Research Agent",
       division="Infrastructure",
       ...
   )
   orch.process_intake(intake_id, project_id)  # Mark processed
5. Project now in orchestrator, assigned to Whiteboard Agent
6. Appears in sidebar ticker immediately
7. Milestones auto-added with default target dates
8. Never lost or forgotten
```

## Usage Patterns

### For You (Manual Operations)

```python
from studio_orchestrator import StudioOrchestrator

orch = StudioOrchestrator()

# Check what's blocked
blocked = orch.list_projects({"status": "blocked"})

# Look at next week's milestones
weekly = orch.get_weekly_status()

# Log work manually if needed
orch.log_production("my_manual_work", project_id=1, asset_type="test", asset_count=1)

# Mark escalation as resolved
orch.resolve_escalation(escalation_id=5)
```

### For Agents (Logging Production)

```python
# At end of agent script
from studio_orchestrator import StudioOrchestrator

orch = StudioOrchestrator()
try:
    # ... agent work ...
    orch.log_production(
        agent="agent_name",
        project_id=AGENT_PROJECT_ID,  # Set once per agent
        asset_type="what_you_made",
        asset_count=how_many,
        cost_usd=api_costs,
        status="success" if no_errors else "partial"
    )
finally:
    orch.close()
```

### For Task Scheduler (Wrapper)

```batch
REM Task: "eBay Agent - Daily"
REM Time: 3:00 PM daily

python C:\path\to\orchestrator\studio_tasks.py wrap_agent ebay_agent "C:\path\to\ebay_agent.py" 1
```

## Advantages Over Manual Tracking

| Problem | Solution |
|---------|----------|
| "What's actually happening?" | Real-time sidebar ticker (live updates) |
| "Did this run or just fail silently?" | Silent failure detection (asset count = 0) |
| "Why isn't X moving forward?" | Dependency graph + blocking escalations |
| "Are deadlines being missed?" | Missed deadline alerts in email |
| "What's in progress vs. complete?" | Unified project status view |
| "New ideas get lost" | Auto-intake system (nothing orphaned) |
| "No visibility on costs" | Production log tracks cost per agent per day |
| "Manual context switching" | Structured goals (Supervisor uses this DB) |

## Operational Checklist

### Daily (Automated)
- ✓ 5:00 AM — Sidebar bridge auto-starts
- ✓ 6:00 AM — Health check detects issues
- ✓ 6:XX AM — Escalation emails sent (if issues)
- ✓ 7:00 AM — Daily digest emailed
- ✓ 24/7 — Sidebar widget updates every 60 sec

### Weekly (Automated)
- ✓ Monday 8:00 AM — Weekly accountability report

### As Needed (Manual)
- Query DB for specific insights
- Resolve escalations when fixed
- Add new projects
- Adjust milestones
- Process intake queue

## May 2026 Transition

This system is designed for **continuity**:

1. **Share `studio_projects.db`** with collaborators
2. **All project history** is queryable and exportable
3. **Dependencies documented** in the database
4. **Production metrics** show each agent's ROI
5. **Escalations logged** for future reference

Future maintainers can:
- Query the full project history
- See what worked vs. what was abandoned
- Understand dependencies and blockers
- Track agent performance over time
- Replicate or extend the system

---

## Next Steps

1. **Copy folder** to `G:\My Drive\Projects\_studio\orchestrator`
2. **Run bootstrap**: `python studio_orchestrator.py`
3. **Start sidebar bridge**: `python sidebar_bridge.py`
4. **Configure Task Scheduler** (4 tasks, see DEPLOYMENT_GUIDE.md)
5. **Test email** (send test digest)
6. **Connect agents** (add logging to each)
7. **Monitor** (check sidebar daily)

**Estimated setup time:** 1-2 hours (mostly Task Scheduler config)

---

## FAQ

**Q: Will this slow down my agents?**  
A: No. Logging is async (non-blocking). Optional. Overhead < 100ms per run.

**Q: What if I want to keep my agents unchanged?**  
A: Wrap them in Task Scheduler instead. The wrapper logs production automatically.

**Q: Can I query the DB directly?**  
A: Yes. Standard SQLite. Open in any tool. SQL examples in DEPLOYMENT_GUIDE.md.

**Q: What happens if Sidebar Bridge crashes?**  
A: Task Scheduler auto-restarts it at 5 AM. Data is safe in DB.

**Q: How do I handle dependencies that change mid-project?**  
A: `orch.add_dependency()` at any time. Update milestones as needed.

**Q: Can I delete projects?**  
A: Yes, but they stay in DB (referential integrity). Better: set status="complete".

**Q: How often should I look at this?**  
A: Morning (check email escalations), weekly (read digest), daily (optional sidebar check).

---

## Support

- **Database questions:** SQL against `studio_projects.db`
- **Email issues:** Check SMTP settings in `email_service.py`
- **Sidebar not updating:** Restart `sidebar_bridge.py` or refresh browser
- **Task Scheduler issues:** Check Windows Event Viewer logs
- **Integration issues:** Use `studio_tasks.py wrap_agent` if agent logging too difficult
