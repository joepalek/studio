# STUDIO ORCHESTRATOR v2 — QUICK REFERENCE & INDEX

## 📦 What You're Getting

A **complete, production-ready project lifecycle management system** for your 16+ agent studio.

**Core Promise:** Every project tracked, every block escalated, every asset logged, nothing orphaned.

---

## 📁 File Manifest

### Core System (4 files)

| File | Purpose | Size | Language |
|------|---------|------|----------|
| `studio_orchestrator.py` | Database + project API | 820 LOC | Python |
| `health_monitor.py` | Daily health checks | 200 LOC | Python |
| `email_service.py` | Digest + escalation emails | 150 LOC | Python |
| `sidebar_bridge.py` | HTTP server for live data | 250 LOC | Python |

### Integration (2 files)

| File | Purpose | Size | Language |
|------|---------|------|----------|
| `studio_tasks.py` | Task Scheduler scripts | 300 LOC | Python |
| `sidebar-orchestrator.html` | Live sidebar widget | 300 LOC | HTML/JS |

### Documentation (3 files)

| File | Purpose |
|------|---------|
| `DEPLOYMENT_GUIDE.md` | Step-by-step setup + config |
| `SYSTEM_ARCHITECTURE.md` | Deep dive on design + examples |
| `README.md` (this file) | Quick reference + FAQ |

### Utilities

| File | Purpose |
|------|---------|
| `quick_start.py` | One-command initialization |
| `studio_projects.db` | SQLite database (auto-created) |

---

## 🚀 Quick Start (5 Minutes)

```bash
# 1. Copy folder to studio directory
xcopy studio-project-system "G:\My Drive\Projects\_studio\orchestrator" /E /I

# 2. Install Flask
pip install flask

# 3. Initialize database
cd orchestrator
python studio_orchestrator.py

# 4. Start sidebar bridge (in terminal)
python sidebar_bridge.py

# 5. That's it! 
# Now configure Task Scheduler (see DEPLOYMENT_GUIDE.md)
```

---

## 📊 Database Schema

```sql
-- 17 projects pre-loaded (eBay, Game Archaeology, Sentinel suite, etc.)
projects (id, name, division, phase, priority, status, ...)

-- Milestones per project (target_date, status, assigned_agent)
milestones (id, project_id, title, target_date, status, ...)

-- Project dependencies (upstream → downstream)
dependencies (id, upstream_id, downstream_id, relationship)

-- Asset production tracking (agent, timestamp, asset_type, count, cost)
production_log (id, agent, project_id, asset_type, asset_count, cost_usd, ...)

-- Escalations (blocks, silent fails, deadline misses)
escalations (id, project_id, escalation_type, description, severity, emailed, ...)

-- New projects awaiting processing
intake_queue (id, title, source, source_id, division, processed, ...)
```

---

## 🔄 Daily Workflow

```
5:00 AM   → Sidebar bridge auto-starts
6:00 AM   → Health check runs
          ├─ Detects silent failures (0 assets in 24h)
          ├─ Detects blocked projects (unmet dependencies)
          ├─ Detects missed deadlines
          └─ Detects stalled projects (14+ days no activity)
6:XX AM   → Escalation email sent (if issues found)
7:00 AM   → Daily digest email sent
24/7      → Sidebar widget updates live (every 60 sec)
```

---

## 🎯 Key Features

### 1. **Live Project Ticker** (Sidebar)
- Real-time status: 🟢 Active, 🔴 Blocked, 🟡 Complete
- Priority order (P1 first)
- Next milestone for each project
- Escalation alerts with blink animation

### 2. **Automated Health Checks** (6 AM Daily)
- Silent failures: Agent ran but produced 0 assets
- Blocked projects: Waiting on upstream dependency
- Missed deadlines: target_date < today
- Stalled projects: No activity 14+ days

### 3. **Email Escalations** (On-Demand)
```
🚨 ESCALATION ALERT

⛔ HIGH PRIORITY (2)
  • Sentinel Viewer BLOCKED by: Sentinel Core
  • eBay Agent milestone overdue by 5 days

⚠️ MEDIUM PRIORITY (1)
  • Game Archaeology: 0 assets in 24h
```

### 4. **Production Logging**
Every agent can log what it created:
```python
orch.log_production(
    agent="ebay_agent",
    project_id=1,
    asset_type="listings",
    asset_count=12,
    cost_usd=0.02,
    status="success"
)
```

### 5. **Auto-Intake System**
New projects registered from GitHub issues, folders, etc. → Never orphaned.

### 6. **Dependency Tracking**
Project A requires output from Project B → Automatically escalates if B isn't complete.

---

## 💻 API Quick Reference

### Core Operations

```python
from studio_orchestrator import StudioOrchestrator

orch = StudioOrchestrator()

# Add project
project_id = orch.add_project(
    name="New Project",
    division="Infrastructure",
    milestones=[...],
    priority=2,
    target_date="2026-04-30"
)

# Log production
orch.log_production(
    agent="ebay_agent",
    project_id=1,
    asset_type="listings",
    asset_count=15,
    cost_usd=0.05
)

# Add dependency
orch.add_dependency(
    upstream_id=10,  # Sentinel Core
    downstream_id=11,  # Sentinel Viewer
    relationship="requires_output"
)

# Get daily status
status = orch.get_daily_status()
print(f"Active: {status['projects_active']}")
print(f"Blocked: {status['projects_blocked']}")
print(f"Assets today: {status['assets_produced_today']}")

# Get unresolved escalations
issues = orch.get_unresolved_escalations()
for issue in issues:
    print(f"[{issue['escalation_type']}] {issue['description']}")

orch.close()
```

### Task Scheduler Commands

```bash
# Health check
python studio_tasks.py health_check

# Send digest
python studio_tasks.py digest

# Weekly report
python studio_tasks.py weekly_report

# Ensure sidebar running
python studio_tasks.py ensure_sidebar

# Wrap agent execution
python studio_tasks.py wrap_agent ebay_agent "C:\path\to\agent.py" 1
```

### HTTP API (port 11436)

```
GET /api/projects/status           → All projects (JSON)
GET /api/escalations/active        → Unresolved escalations
GET /api/stats/daily               → Today's snapshot
GET /api/milestones/due-week       → Next 7 days
GET /api/projects/{id}/details     → Full project info
GET /health                        → Health check
```

---

## 📋 Pre-Loaded Projects (17 Total)

| ID | Name | Division | Priority | Status |
|----|------|----------|----------|--------|
| 1 | eBay Agent | Commerce | 1 | active |
| 2 | Game Archaeology | Content | 2 | active |
| 3 | Ghost Book Division | Content | 3 | active |
| 4 | AI Intel Agent | Infrastructure | 2 | active |
| 5 | Job Discovery System | Infrastructure | 1 | active |
| 6 | Studio Sidebar v2 | Infrastructure | 2 | active |
| 7 | Character Test Workbench | Research | 2 | active |
| 8 | Gaussian Splatting Pipeline | Research | 4 | active |
| 9 | Sentinel Performer | Sentinel Suite | 1 | active |
| 10 | Sentinel Core | Sentinel Suite | 2 | active |
| 11 | Sentinel Viewer | Sentinel Suite | 2 | active |
| 12 | Art Department | Content | 3 | active |
| 13 | Inbox Manager | Infrastructure | 2 | active |
| 14 | Supervisor Agent | Infrastructure | 1 | active |
| 15 | Whiteboard Agent | Infrastructure | 2 | active |
| 16 | Truth Gate (Horde Shooter) | Content | 5 | active |
| 17 | AcuScan AR | Research | 4 | active |

---

## 🔌 Integration Patterns

### Pattern 1: Agent Self-Logging (Minimal Changes)

Add 5 lines to end of each agent:

```python
from studio_orchestrator import StudioOrchestrator

orch = StudioOrchestrator()
try:
    # ... agent work ...
    orch.log_production("agent_name", PROJECT_ID, "asset_type", count, cost, "success")
finally:
    orch.close()
```

### Pattern 2: Task Scheduler Wrapper (No Agent Changes)

Wrap in Task Scheduler:

```
python studio_tasks.py wrap_agent ebay_agent "C:\path\to\ebay_agent.py" 1
```

### Pattern 3: Manual Logging (On-Demand)

```python
python -c "
from studio_orchestrator import StudioOrchestrator
orch = StudioOrchestrator()
orch.log_production('agent_name', 1, 'assets', 5, 0.01, 'success')
orch.close()
"
```

---

## 🛠️ Configuration Checklist

### Before Deployment

- [ ] Copy folder to `G:\My Drive\Projects\_studio\orchestrator`
- [ ] `pip install flask`
- [ ] Run `python studio_orchestrator.py` (creates DB)
- [ ] Test sidebar bridge: `python sidebar_bridge.py`
- [ ] Configure email in `email_service.py` (lines 10-13)
- [ ] Create 4 Task Scheduler tasks (see DEPLOYMENT_GUIDE.md)
- [ ] Test email: `python email_service.py`
- [ ] Add sidebar widget to Opera (http://127.0.0.1:11436/sidebar-orchestrator.html)
- [ ] Integrate agents (pick Pattern 1, 2, or 3 above)

### Ongoing Maintenance

- [ ] Check email escalations daily (6 AM)
- [ ] Monitor sidebar ticker (real-time)
- [ ] Resolve escalations as needed
- [ ] Query DB for insights (weekly)
- [ ] Back up `studio_projects.db` (monthly)

---

## 📈 Metrics This System Captures

### Daily
- Projects active / blocked / complete
- Assets produced (by type)
- API costs incurred
- Escalations created
- Production runs completed

### Weekly
- Milestones due / complete / overdue
- Assets per agent (productivity)
- Blockers (what's holding up projects)
- New projects intake (discovery)

### Monthly (via SQL query)
- Cost per division
- Agent productivity (assets/cost ratio)
- Project completion rate
- Dependency violations

---

## 🐛 Troubleshooting

### Sidebar not updating
```bash
# Check if bridge is running
curl http://127.0.0.1:11436/health

# If not running, manually start
python sidebar_bridge.py

# Refresh Opera sidebar (Ctrl+R)
```

### Email not sending (dev mode)
```bash
# Check stdout/stderr from Task Scheduler run
# Dev mode prints to console instead of Gmail
python email_service.py  # Run manually to test
```

### No projects in database
```bash
# Re-run bootstrap
python studio_orchestrator.py
```

### Port 11436 in use
```bash
# Find and kill process
netstat -ano | findstr :11436
taskkill /PID [PID] /F
```

### Task Scheduler not triggering
```bash
# Check Task Scheduler history
# Event Viewer → Windows Logs → Application
# Look for "Task Scheduler" errors

# Test manually
python studio_tasks.py health_check
```

---

## 📚 Documentation Structure

| Document | Audience | Contents |
|----------|----------|----------|
| `README.md` (this) | Everyone | Overview, quick ref, FAQ |
| `DEPLOYMENT_GUIDE.md` | DevOps/Setup | Step-by-step installation |
| `SYSTEM_ARCHITECTURE.md` | Architects | Deep design, data flows, examples |
| Code docstrings | Developers | Method signatures, examples |

---

## 🎯 Design Principles

This system follows:

1. **Single Source of Truth** — All state in `studio_projects.db`
2. **Deterministic** — Rules-based escalations (not AI-driven)
3. **Audit Trail** — Every action logged with timestamp
4. **No Orphans** — New projects auto-registered
5. **Low Overhead** — Optional agent integration (non-blocking)
6. **Extensible** — Schema supports custom fields via JSON
7. **Queryable** — Standard SQL (no proprietary format)

---

## 🚪 Exit Strategy (May 2026)

When transitioning:

1. Export `studio_projects.db` (single file)
2. Share with collaborators/successors
3. All project history queryable by future maintainers
4. Production metrics show each agent's ROI
5. Escalations document what was blocking
6. Dependencies show project structure

Future team can:
- Continue using exact system
- Query for insights on past projects
- Understand what worked vs. what didn't
- Replicate or extend architecture

---

## 💡 Pro Tips

**Tip 1: Check status without email**
```bash
python -c "
from studio_orchestrator import StudioOrchestrator
orch = StudioOrchestrator()
status = orch.get_daily_status()
for k, v in status.items(): print(f'{k}: {v}')
orch.close()
"
```

**Tip 2: Query blocked projects**
```bash
sqlite3 studio_projects.db
> SELECT p.name FROM projects p
> JOIN dependencies d ON p.id = d.downstream_project_id
> WHERE d.upstream_project_id IN (SELECT id FROM projects WHERE status != 'complete');
```

**Tip 3: Production summary (last 7 days)**
```bash
sqlite3 studio_projects.db
> SELECT agent, asset_type, SUM(asset_count) as total, SUM(cost_usd) as cost
> FROM production_log
> WHERE datetime(timestamp) > datetime('now', '-7 days')
> GROUP BY agent, asset_type ORDER BY total DESC;
```

**Tip 4: Auto-backup database**
```batch
REM Add to Task Scheduler (weekly)
copy "G:\My Drive\Projects\_studio\orchestrator\studio_projects.db" ^
     "G:\My Drive\Projects\_studio\orchestrator\backups\studio_projects_%date:~-4,4%%date:~-10,2%%date:~-7,2%.db"
```

---

## ❓ FAQ

**Q: Will this interfere with my existing agents?**  
A: No. Agents run unchanged. Logging is optional and non-blocking.

**Q: How do I handle urgencies that arise mid-sprint?**  
A: Update milestones via `orch.update_milestone_status()` or CLI. Health check adjusts.

**Q: Can I export/backup the data?**  
A: Yes. It's standard SQLite. Use `sqlite3 dump` or copy `studio_projects.db`.

**Q: What if Task Scheduler is disabled?**  
A: Run scripts manually: `python studio_tasks.py health_check`

**Q: Can I run this on a server instead of local?**  
A: Yes. Sidebar bridge can run anywhere. Update API_BASE in sidebar-orchestrator.html.

**Q: Is there a web UI instead of sidebar?**  
A: Yes, at `http://127.0.0.1:11436/` (simple dashboard). Browser-based alternative.

---

## 🎓 Next Moves

1. **Read DEPLOYMENT_GUIDE.md** (45 minutes)
2. **Run quick_start.py** (5 minutes)
3. **Set up Task Scheduler** (30 minutes)
4. **Integrate first agent** (15 minutes)
5. **Monitor for 1 week** (daily checks)
6. **Integrate remaining agents** (ongoing)

---

## 📞 Support

**Questions?** Check:
1. This README.md (quick reference)
2. DEPLOYMENT_GUIDE.md (setup help)
3. SYSTEM_ARCHITECTURE.md (design deep-dive)
4. Code docstrings (method docs)

**Bugs or features?** Database is fully queryable — debug locally before asking for help.

---

**Ready to deploy?** Start with `DEPLOYMENT_GUIDE.md` →
