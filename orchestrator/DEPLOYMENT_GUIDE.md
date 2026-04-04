# STUDIO ORCHESTRATOR v2 — DEPLOYMENT GUIDE

## Overview

This is a **complete project lifecycle management system** for your 16+ agent studio. It provides:

- **Centralized project registry** (SQLite database)
- **Automated health monitoring** (detects silent failures, blocks, deadline misses)
- **Live sidebar updates** (real-time project ticker via HTTP bridge)
- **Email escalations** (immediate notification of critical issues)
- **Daily digests & weekly reports** (accountability)
- **Auto-intake system** (new projects auto-registered from GitHub, folders)
- **Production tracking** (every asset logged with cost/timestamp)

## File Structure

```
studio-project-system/
├── studio_orchestrator.py          # Core database + project management
├── health_monitor.py               # Daily health checks & escalation detection
├── email_service.py                # Email generation (digests, reports, alerts)
├── sidebar_bridge.py               # HTTP server for live sidebar data
├── studio_tasks.py                 # Task Scheduler integration scripts
├── sidebar-orchestrator.html       # Sidebar widget UI
├── bootstrap_projects.py           # Initial data load (optional)
└── README.md                       # This file
```

## Installation

### Step 1: Copy Files to Studio Directory

```bash
# Copy entire folder to your studio workspace
xcopy studio-project-system "G:\My Drive\Projects\_studio\orchestrator" /E /I

# Or use WSL/Git:
cd "G:\My Drive\Projects\_studio"
git clone <repo> orchestrator
cd orchestrator
```

### Step 2: Install Python Dependencies

```bash
# Only Flask is required (for sidebar_bridge.py)
pip install flask

# All other modules are stdlib (sqlite3, logging, datetime, json, etc.)
```

### Step 3: Initialize Database

```bash
cd "G:\My Drive\Projects\_studio\orchestrator"
python studio_orchestrator.py

# Output:
# [INFO] Orchestrator initialized: studio_projects.db
# [INFO] Database schema verified
# [INFO] === BOOTSTRAPPING STUDIO ===
# [INFO] Project added: eBay Agent (id=1)
# [INFO] Project added: Game Archaeology (id=2)
# ... (16+ projects)
# [INFO] === BOOTSTRAP COMPLETE ===
```

This creates `studio_projects.db` with all 16+ existing projects + Sentinel suite.

### Step 4: Configure Email Service

Edit `email_service.py`:

```python
# Line ~10: Set your email
SENDER_EMAIL = "your-email@gmail.com"  # or use studio-alerts@yourmail.com
RECIPIENT_EMAIL = "joedealsonline@gmail.com"
SMTP_PASSWORD = "your_app_password"  # Gmail: create via "App Passwords"
```

For **development/testing**: Email logs to console (no SMTP needed).
For **production**: Uncomment SMTP section and set credentials.

### Step 5: Start Sidebar Bridge

```bash
# Terminal 1: Start the HTTP server
python sidebar_bridge.py

# Output:
# [INFO] Starting Studio Sidebar Bridge on port 11436...
# * Running on http://127.0.0.1:11436
```

This provides live API endpoints:
- `http://127.0.0.1:11436/` — Web dashboard (optional)
- `http://127.0.0.1:11436/api/projects/status` — All projects
- `http://127.0.0.1:11436/api/escalations/active` — Active issues
- `http://127.0.0.1:11436/api/stats/daily` — Today's metrics

### Step 6: Configure Windows Task Scheduler

Create 4 automated tasks. Open Task Scheduler and add each:

#### Task 1: Daily Health Check (6:00 AM)

```
Program: C:\Users\[YOU]\AppData\Local\Programs\Python\Python312\python.exe
Arguments: C:\path\to\orchestrator\studio_tasks.py health_check
Start in: C:\path\to\orchestrator
Trigger: Daily at 6:00 AM
Run with highest privileges: No
Run whether logged in or not: No (user account only)
```

#### Task 2: Daily Digest (7:00 AM)

```
Program: C:\Users\[YOU]\AppData\Local\Programs\Python\Python312\python.exe
Arguments: C:\path\to\orchestrator\studio_tasks.py digest
Start in: C:\path\to\orchestrator
Trigger: Daily at 7:00 AM
```

#### Task 3: Weekly Report (Monday 8:00 AM)

```
Program: C:\Users\[YOU]\AppData\Local\Programs\Python\Python312\python.exe
Arguments: C:\path\to\orchestrator\studio_tasks.py weekly_report
Start in: C:\path\to\orchestrator
Trigger: Weekly on Monday at 8:00 AM
```

#### Task 4: Sidebar Bridge Launcher (5:00 AM)

```
Program: C:\Users\[YOU]\AppData\Local\Programs\Python\Python312\python.exe
Arguments: C:\path\to\orchestrator\studio_tasks.py ensure_sidebar
Start in: C:\path\to\orchestrator
Trigger: Daily at 5:00 AM
```

**Find Python path:**
```bash
python -c "import sys; print(sys.executable)"
# Output: C:\Users\joe\AppData\Local\Programs\Python\Python312\python.exe
```

## Integration with Existing Agents

### Option A: Auto-Logging (Minimal Changes)

Each agent wraps its execution with logging. Add to agent exit:

```python
# At end of your agent script
from orchestrator.studio_orchestrator import StudioOrchestrator

orch = StudioOrchestrator("G:/My Drive/Projects/_studio/orchestrator/studio_projects.db")

# Log what you produced
orch.log_production(
    agent="ebay_agent",           # Your agent name
    project_id=1,                 # From projects table (set once)
    asset_type="listings",        # What you produced
    asset_count=15,               # How many
    cost_usd=0.05,                # API costs
    status="success"              # or "partial" or "failed"
)

orch.close()
```

**Find your project_id:**
```bash
python -c "
from studio_orchestrator import StudioOrchestrator
orch = StudioOrchestrator()
for p in orch.list_projects():
    print(f'{p[\"id\"]}: {p[\"name\"]}')
orch.close()
"
```

### Option B: Task Scheduler Wrapper

Wrap agent execution in Task Scheduler instead of modifying agent code:

```
Program: python studio_tasks.py wrap_agent ebay_agent "C:\path\to\ebay_agent.py" 1
```

The wrapper:
- Runs your agent
- Captures output for asset counts
- Logs to database automatically
- Reports execution time + errors

### Option C: Manual Logging

If you don't want automation, log manually when needed:

```bash
# From any script or CLI
python
>>> from studio_orchestrator import StudioOrchestrator
>>> orch = StudioOrchestrator()
>>> orch.log_production("ebay_agent", 1, "listings", 15, 0.05, "success")
>>> orch.close()
```

## Operating the System

### Daily Workflow

**5:00 AM** — Sidebar bridge auto-starts
**6:00 AM** — Health check runs → escalations emailed if issues found
**7:00 AM** — Daily digest emailed
**Real-time** — Sidebar widget updates every 60 seconds (at `http://127.0.0.1:8765/sidebar-orchestrator.html`)

### Escalation Handling

When health check detects issues, you receive an email:

```
🚨 STUDIO ESCALATION ALERT 🚨

⛔ HIGH PRIORITY (2)
  • Sentinel Viewer is BLOCKED by: Sentinel Core, API schema
  • eBay Agent → Push 40 listings
    5 days overdue (assigned: ebay_agent)

⚠️ MEDIUM PRIORITY (1)
  • Game Archaeology → Weekly crawler operational
    Ran but produced 0 assets in 24h (agent: game_archaeology_agent)
```

### Manual Project Management

Add new projects to the system:

```python
from studio_orchestrator import StudioOrchestrator

orch = StudioOrchestrator()

# Add a new project
project_id = orch.add_project(
    name="AI Character Generation",
    division="Content",
    description="Generate 10 unique character models for indie game",
    priority=2,
    target_date="2026-05-15",
    owner_agent="art_department",
    tags=["revenue", "content"],
    milestones=[
        {
            "title": "Character model 1 complete",
            "target_date": "2026-04-20",
            "agent": "art_department"
        },
        {
            "title": "All 10 characters done",
            "target_date": "2026-05-15",
            "agent": "art_department"
        }
    ]
)

# Add dependency: this project depends on Art Department
orch.add_dependency(5, project_id, "requires_output")  # 5=Art Department id

orch.close()
```

### Query the Database

```python
from studio_orchestrator import StudioOrchestrator

orch = StudioOrchestrator()

# Get all active projects
active = orch.list_projects({"status": "active"})
for p in active:
    print(f"{p['name']} (P{p['priority']}) - {p['division']}")

# Get weekly status
weekly = orch.get_weekly_status()
print(f"Active: {weekly['projects_active']}, Blocked: {weekly['projects_blocked']}")

# Get production for a project
prod = orch.get_project_production(1, days=7)
for p in prod:
    print(f"{p['agent']} produced {p['total_count']} {p['asset_type']} (${p['total_cost']})")

# Check for blocks
blockers = orch.get_blocking_projects(3)
if blockers:
    print(f"Project 3 is blocked by: {[b['name'] for b in blockers]}")

orch.close()
```

## Sidebar Integration

The sidebar widget needs to be served via HTTP. Two options:

### Option 1: Serve from sidebar_bridge.py (Recommended)

The bridge already serves static files. Access:

```
http://127.0.0.1:11436/sidebar-orchestrator.html
```

Then add to Opera sidebar:

1. Right-click sidebar
2. "Manage Sidebar Panels"
3. Add new URL-based panel
4. Enter: `http://127.0.0.1:11436/sidebar-orchestrator.html`
5. Refresh every 1 minute

### Option 2: Serve from your existing sidebar port (8765)

Copy `sidebar-orchestrator.html` to your existing sidebar folder and update Opera to point there.

## Monitoring & Troubleshooting

### Check if everything is running:

```bash
# Sidebar bridge
curl http://127.0.0.1:11436/health
# Output: {"status": "operational", "timestamp": "..."}

# Database integrity
python -c "
from studio_orchestrator import StudioOrchestrator
orch = StudioOrchestrator()
print(f'Projects: {len(orch.list_projects())}')
print(f'Escalations: {len(orch.get_unresolved_escalations())}')
orch.close()
"

# Task Scheduler logs (Windows)
Get-EventLog -LogName "Application" -Source "Task Scheduler" -Newest 10
```

### Common Issues

**Issue: "No module named 'flask'"**
```bash
pip install flask
```

**Issue: "Port 11436 already in use"**
```bash
# Windows: Find and kill process
netstat -ano | findstr :11436
taskkill /PID [PID] /F
```

**Issue: Sidebar not updating**
- Check if `sidebar_bridge.py` is running: `curl http://127.0.0.1:11436/health`
- Refresh Opera sidebar panel (Ctrl+R or menu)
- Check browser console for CORS errors

**Issue: Email not sending**
- Dev mode: Check stdout logs (not Gmail)
- Prod mode: Verify `SMTP_PASSWORD` is set correctly
- Gmail: Create "App Password" at myaccount.google.com/security

## Architecture Decisions

### Why SQLite?

- Zero setup (no external DB needed)
- Single file backup
- Queryable from any Python script
- Good for 16 agents + 50 projects

### Why HTTP bridge instead of direct DB?

- Sidebar (Opera) can't access local file paths
- HTTP allows real-time polling without reloading
- Easy to extend with future features (notifications, webhooks)

### Why Task Scheduler instead of Cron?

- Windows native (no WSL/Git Bash needed)
- Integrates with your existing agent schedule
- Can trigger on specific windows events

### Why not a single "Supervisor" agent?

- Supervisors are unpredictable (AI-driven goal-setting)
- This system is deterministic (rules-based escalations)
- Supervisor can use this DB as input for higher-level decisions

## Future Enhancements

**Phase 2:**
- Slack integration (escalations → Slack channel)
- GitHub auto-intake (issues tagged #studio-project)
- Calendar integration (milestones in Google Calendar)
- Cost tracking per division per month

**Phase 3:**
- Dependency visualization (Mermaid diagram)
- Burndown charts per division
- AI-driven milestone prediction (based on historical velocity)
- Agent performance scoring

## Support & Debugging

For questions or issues:

1. Check logs in stdout from Task Scheduler
2. Query `studio_projects.db` directly:
   ```bash
   sqlite3 studio_projects.db
   > .schema projects
   > SELECT * FROM escalations WHERE resolved_date IS NULL;
   ```
3. Test email generation: `python email_service.py`
4. Test orchestrator: `python studio_orchestrator.py`

## Notes for May 2026 Transition

This system is designed to scale with your studio:

- All active projects tracked in one place
- New projects auto-added (no orphaned work)
- Escalations force visibility on what's blocked
- Production metrics show ROI per agent
- Database is easily migrated or queried by future maintainers

After May: Share `studio_projects.db` with collaborators to maintain project continuity.
