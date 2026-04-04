# STUDIO ORCHESTRATOR — OPERATIONS MANUAL

## Daily Operations (Copy-Paste Ready)

### Morning Routine (7:00 AM)

Check your email for escalation report. If issues:

```bash
# View active escalations
python -c "
from studio_orchestrator import StudioOrchestrator
orch = StudioOrchestrator()
issues = orch.get_unresolved_escalations()
for issue in issues:
    print(f\"[{issue['escalation_type']}] {issue['name']}: {issue['description']}\")
orch.close()
"
```

### Check Daily Production (7:15 AM)

```bash
# View what agents produced today
python -c "
from studio_orchestrator import StudioOrchestrator
from datetime import datetime

orch = StudioOrchestrator()
today = datetime.now().isoformat()[:10]

prod = orch.db.execute(f'''
    SELECT agent, asset_type, SUM(asset_count) as count, SUM(cost_usd) as cost
    FROM production_log
    WHERE DATE(timestamp) = '{today}'
    GROUP BY agent, asset_type
''').fetchall()

print('\\n📊 TODAY\\'S PRODUCTION')
for agent, asset_type, count, cost in prod:
    print(f'  {agent} → {asset_type}: {count} (${cost:.2f})')

orch.close()
"
```

### Resolve Escalation (As Needed)

```bash
# If you fixed the issue, mark as resolved
python -c "
from studio_orchestrator import StudioOrchestrator
orch = StudioOrchestrator()
orch.resolve_escalation(escalation_id=5)  # Replace with actual ID
orch.close()
"
```

### Weekly Review (Monday Morning)

```bash
# View last week's performance
python analytics_engine.py
# or:
python -c "
from analytics_engine import generate_insights_report
print(generate_insights_report())
"
```

---

## Command Reference

### Database Queries

**Active projects:**
```sql
SELECT name, priority, division FROM projects WHERE status='active' ORDER BY priority;
```

**Blocked projects:**
```sql
SELECT p.name, GROUP_CONCAT(b.name) as blockers
FROM projects p
JOIN dependencies d ON p.id = d.downstream_project_id
JOIN projects b ON d.upstream_project_id = b.id
WHERE b.status != 'complete'
GROUP BY p.id;
```

**Production this week:**
```sql
SELECT agent, SUM(asset_count) as assets, SUM(cost_usd) as cost
FROM production_log
WHERE datetime(timestamp) > datetime('now', '-7 days')
GROUP BY agent
ORDER BY assets DESC;
```

**Milestones due:**
```sql
SELECT p.name, m.title, m.target_date, m.assigned_agent
FROM milestones m
JOIN projects p ON m.project_id = p.id
WHERE m.status IN ('pending', 'in_progress')
AND m.target_date < date('now', '+7 days')
AND m.target_date >= date('now')
ORDER BY m.target_date;
```

**Cost breakdown (last 30 days):**
```sql
SELECT agent, SUM(cost_usd) as total_cost
FROM production_log
WHERE datetime(timestamp) > datetime('now', '-30 days')
GROUP BY agent
ORDER BY total_cost DESC;
```

---

## Manual Procedures

### Add a New Project

```python
from studio_orchestrator import StudioOrchestrator

orch = StudioOrchestrator()

project_id = orch.add_project(
    name="My New Project",
    division="Infrastructure",
    description="What is this project?",
    priority=2,  # 1=urgent, 5=backlog
    target_date="2026-05-15",
    owner_agent="orchestrator",
    tags=["revenue", "infrastructure"],
    milestones=[
        {
            "title": "First milestone",
            "target_date": "2026-04-20",
            "agent": "orchestrator"
        },
        {
            "title": "Second milestone",
            "target_date": "2026-05-10",
            "agent": "orchestrator"
        }
    ]
)

print(f"Project created: ID={project_id}")
orch.close()
```

### Add Project Dependency

```python
from studio_orchestrator import StudioOrchestrator

orch = StudioOrchestrator()

# Project 5 (Job Discovery) requires output from Project 4 (AI Intel)
orch.add_dependency(
    upstream_id=4,   # AI Intel Agent (must complete first)
    downstream_id=5, # Job Discovery System (depends on AI Intel)
    relationship="requires_output"
)

print("Dependency added: Job Discovery depends on AI Intel")
orch.close()
```

### Update Milestone Status

```python
from studio_orchestrator import StudioOrchestrator

orch = StudioOrchestrator()

# Mark a milestone as complete
orch.db.execute(
    "UPDATE milestones SET status='complete', completed_date=CURRENT_TIMESTAMP WHERE id=?",
    (milestone_id,)  # Find ID from database
)
orch.db.commit()

print(f"Milestone {milestone_id} marked complete")
orch.close()
```

### Log Manual Work

```python
from studio_orchestrator import StudioOrchestrator

orch = StudioOrchestrator()

# If you did work that agents didn't log
orch.log_production(
    agent="manual_work",
    project_id=1,  # Which project
    asset_type="testing",
    asset_count=5,
    cost_usd=0.00,
    status="success"
)

print("Manual work logged")
orch.close()
```

### Export Data to CSV

```bash
# Install (if needed):
pip install pandas

# Run export:
python -c "
import sqlite3
import pandas as pd

conn = sqlite3.connect('studio_projects.db')

# Export production log
prod = pd.read_sql('SELECT * FROM production_log', conn)
prod.to_csv('production_log.csv', index=False)
print('✓ Exported production_log.csv')

# Export escalations
esc = pd.read_sql('SELECT * FROM escalations', conn)
esc.to_csv('escalations.csv', index=False)
print('✓ Exported escalations.csv')

conn.close()
"
```

---

## Troubleshooting Guide

### Issue: Sidebar not updating

**Symptoms:** Sidebar shows stale data

**Solution:**
```bash
# Check if sidebar bridge is running
curl http://127.0.0.1:11436/health

# If fails, restart it
python sidebar_bridge.py

# Or in Task Scheduler, run:
python studio_tasks.py ensure_sidebar
```

### Issue: Email not sending

**Symptoms:** No email received at 7 AM

**Solution:**
```bash
# Test email generation manually
python email_service.py

# Check Task Scheduler logs
Get-EventLog -LogName "Application" -Source "Task Scheduler" -Newest 5

# Verify email config (email_service.py)
# Check SMTP_PASSWORD is set correctly
```

### Issue: Agent produced no assets (Silent failure)

**Symptoms:** Agent ran but produced 0 assets

**Solution:**
```bash
# Check agent logs
tail -f logs/agent_name.log

# Check if database is accessible
python -c "from studio_orchestrator import StudioOrchestrator; orch = StudioOrchestrator(); print('✓ DB connected'); orch.close()"

# Manually log production if data exists elsewhere
python -c "
from studio_orchestrator import StudioOrchestrator
orch = StudioOrchestrator()
orch.log_production('agent_name', project_id, 'assets', count, cost, 'success')
orch.close()
"
```

### Issue: Database errors

**Symptoms:** SQLite database locked, query errors

**Solution:**
```bash
# Check database integrity
python test_suite.py validate

# Run diagnostics
python test_suite.py diagnostics

# Rebuild database (CAUTION: loses data)
python test_suite.py reset
```

### Issue: Task Scheduler not triggering

**Symptoms:** Tasks don't run at scheduled time

**Solution:**
```bash
# Check Windows Event Viewer
# Event Viewer → Windows Logs → Application
# Search for "Task Scheduler" errors

# Verify Task Scheduler can access Python
# In Task Scheduler, test the command manually

# Check if Python path is correct
python -c "import sys; print(sys.executable)"
# Use this path in Task Scheduler action

# Check permissions
# Right-click task → Properties → General → "Run with highest privileges"
```

---

## Maintenance Checklist

### Daily
- [ ] Check email escalations (7 AM)
- [ ] Review daily digest (7 AM)
- [ ] Resolve any HIGH severity escalations

### Weekly
- [ ] Review analytics report
- [ ] Check for overdue milestones
- [ ] Update milestone status where needed
- [ ] Review blocked projects

### Monthly
- [ ] Backup `studio_projects.db` to external drive
- [ ] Export data (CSV) for analysis
- [ ] Audit costs by division
- [ ] Plan next month's priorities
- [ ] Update project target dates

### Quarterly
- [ ] Review agent productivity trends
- [ ] Identify which agents to scale/reduce
- [ ] Evaluate ROI by division
- [ ] Plan new projects
- [ ] Archive old projects

---

## Advanced Techniques

### Custom Analytics Query

```python
from studio_orchestrator import StudioOrchestrator
from datetime import datetime, timedelta

orch = StudioOrchestrator()

# Cost per asset by agent (last 30 days)
cutoff = (datetime.now() - timedelta(days=30)).isoformat()

rows = orch.db.execute(f"""
    SELECT 
        agent,
        SUM(asset_count) as total_assets,
        SUM(cost_usd) as total_cost,
        CAST(SUM(cost_usd) as FLOAT) / CAST(SUM(asset_count) as FLOAT) as cost_per_asset
    FROM production_log
    WHERE timestamp > '{cutoff}'
    GROUP BY agent
    ORDER BY cost_per_asset ASC
""").fetchall()

print("Cost per asset (lower = better ROI):")
for agent, assets, cost, per_asset in rows:
    print(f"  {agent}: ${per_asset:.4f}/asset (produced {assets}, cost ${cost:.2f})")

orch.close()
```

### Automated Escalation Response

```python
from studio_orchestrator import StudioOrchestrator

orch = StudioOrchestrator()

# Get all blocked projects
blocked = orch.list_projects({"status": "blocked"})

for project in blocked:
    blockers = orch.get_blocking_projects(project["id"])
    
    # Auto-notify (example: email, Slack, etc)
    print(f"ALERT: {project['name']} blocked by {[b['name'] for b in blockers]}")

orch.close()
```

### Performance Optimization

```bash
# Create index for faster queries (if not exists)
sqlite3 studio_projects.db "CREATE INDEX IF NOT EXISTS idx_production_date ON production_log(DATE(timestamp));"

# Analyze query performance
sqlite3 studio_projects.db ".explain on" "SELECT * FROM production_log WHERE agent='ebay_agent';"
```

---

## Escalation Response Matrix

| Escalation Type | Severity | Action | Timeline |
|---|---|---|---|
| Blocked | HIGH | Review blocker status, expedite if needed | Immediate |
| Silent Failure | MEDIUM | Check agent logs, verify configuration | Within 1 hour |
| Deadline Miss | HIGH (if >7d) | Adjust timeline or reassign work | Same day |
| Deadline Miss | MEDIUM (if <7d) | Monitor closely, adjust if needed | Next check |
| Stalled | LOW | Check if still active, investigate | Within 24h |

---

## Key Metrics to Monitor

**Weekly:**
- Total assets produced
- Total costs incurred
- Number of active escalations
- Percentage of milestones on-time

**Monthly:**
- Cost per asset (ROI)
- Milestones completed vs. target
- Agent productivity ranking
- Division performance breakdown

**Quarterly:**
- Project completion rate
- Cost trends (up/down/stable)
- Agent utilization (high/medium/low)
- Dependency violations

---

## When Things Go Wrong

### Project Falls Behind Schedule

1. Check dependencies: Is it blocked?
2. Check production: Is agent producing?
3. Check escalations: What's the issue?
4. Action: Expedite blocker OR adjust timeline

### Agent Not Producing Assets

1. Check logs: Any errors?
2. Check database: Can it connect?
3. Check config: Is it enabled?
4. Action: Fix issue OR disable agent (temporary)

### Database Corrupted

1. Run: `python test_suite.py validate`
2. If errors, backup old DB
3. Run: `python test_suite.py reset`
4. Restore from backup if needed

### Too Many Escalations

1. Triage by severity (HIGH first)
2. Resolve HIGH immediately
3. Plan MEDIUM for next day
4. LOW can wait (review weekly)

---

## Integration with Your Workflow

### In VS Code (Terminal)

```bash
# Quick status check
cd "G:\My Drive\Projects\_studio\orchestrator"
python -c "from studio_orchestrator import *; orch = StudioOrchestrator(); print(orch.get_daily_status()); orch.close()"

# Quick diagnostics
python test_suite.py diagnostics
```

### In Windows PowerShell

```powershell
# Check if sidebar running
Invoke-WebRequest http://127.0.0.1:11436/health

# Restart services
python C:\path\to\orchestrator\studio_tasks.py ensure_sidebar

# View escalations
sqlite3 C:\path\to\studio_projects.db "SELECT * FROM escalations WHERE resolved_date IS NULL;"
```

### On Your eBay Reselling Hours

Set a recurring 15-minute block at 7:15 AM to:
1. Check email escalations
2. Resolve any HIGH priority issues
3. Manually update milestone status if needed

---

## Documentation Quick Links

- **DEPLOYMENT_GUIDE.md** — Initial setup
- **SYSTEM_ARCHITECTURE.md** — How it all works
- **README.md** — Quick reference
- **Code docstrings** — Method documentation

---

## Support

**Question:** How do I...?  
**Answer:** Check DEPLOYMENT_GUIDE.md or SYSTEM_ARCHITECTURE.md

**Bug:** System isn't working right  
**Action:** Run `python test_suite.py diagnostics` and share output

**Feature request:** Need something new  
**Action:** All code is yours to modify. Or ask in GitHub.

---

**You're now an operator.** 🎬
