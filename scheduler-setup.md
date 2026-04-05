# SCHEDULER SETUP — WINDOWS TASK SCHEDULER AGENT

## Role
You create and manage Windows Task Scheduler entries for all studio
automated jobs. Run this once to register all tasks. Re-run to update
or repair them. All tasks are idempotent — safe to run multiple times.

## Scheduled Tasks

| Task | Schedule | Script |
|---|---|---|
| Daily Briefing | Every day 8:00 AM | orchestrator-briefing.bat |
| Supervisor Check | Every 30 minutes | supervisor-check.bat |
| Nightly Commit | Every day 11:00 PM | nightly-commit.bat |
| Ghost Book Rescan | Sunday 2:00 AM | ghost-book-rescan.bat |
| Whiteboard Scanner | Every day 4:00 AM | whiteboard-scanner.bat |
| SEO Agent | Every Monday 6:00 AM | seo-agent.bat |

## Execution

### Pass 1 — Create Batch Launchers
Creates the .bat files that Task Scheduler will invoke.

```bash
python G:/My\ Drive/Projects/_studio/scheduler/create_launchers.py
```

Script (`_studio/scheduler/create_launchers.py`):

```python
import os
from datetime import datetime

STUDIO = 'G:/My Drive/Projects/_studio'
SCHED = STUDIO + '/scheduler'
os.makedirs(SCHED, exist_ok=True)

# Log helper used by all launchers
LOG = '%~dp0logs\\%~n0-%date:~10,4%%date:~4,2%%date:~7,2%.log'

launchers = {

    # ── Daily Briefing 8 AM ────────────────────────────────────────────────────
    'orchestrator-briefing.bat': f'''@echo off
cd /d "G:\\My Drive\\Projects\\_studio"
set LOG_DIR=%~dp0logs
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
echo [%date% %time%] Daily briefing starting >> "{SCHED}\\logs\\orchestrator-briefing.log"
claude --dangerously-skip-permissions -p "Load ai-gateway.md and orchestrator.md. Run daily briefing now. Save output to orchestrator-briefing.json." >> "{SCHED}\\logs\\orchestrator-briefing.log" 2>&1
echo [%date% %time%] Done >> "{SCHED}\\logs\\orchestrator-briefing.log"
''',

    # ── Supervisor Every 30 Min ────────────────────────────────────────────────
    'supervisor-check.bat': f'''@echo off
cd /d "G:\\My Drive\\Projects\\_studio"
set LOG_DIR=%~dp0logs
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
echo [%date% %time%] Supervisor check starting >> "{SCHED}\\logs\\supervisor-check.log"
claude --dangerously-skip-permissions -p "Load supervisor.md. Run health check and report. If any background tasks completed, summarize results." >> "{SCHED}\\logs\\supervisor-check.log" 2>&1
echo [%date% %time%] Done >> "{SCHED}\\logs\\supervisor-check.log"
''',

    # ── Nightly Commit 11 PM ───────────────────────────────────────────────────
    'nightly-commit.bat': f'''@echo off
cd /d "G:\\My Drive\\Projects\\_studio"
set LOG_DIR=%~dp0logs
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
echo [%date% %time%] Nightly commit starting >> "{SCHED}\\logs\\nightly-commit.log"
claude --dangerously-skip-permissions -p "Load git-commit-agent.md. Commit all dirty projects now. Then load changelog-agent.md. Update changelogs for all changed projects." >> "{SCHED}\\logs\\nightly-commit.log" 2>&1
echo [%date% %time%] Done >> "{SCHED}\\logs\\nightly-commit.log"
''',

    # ── Ghost Book Rescan Sunday 2 AM ──────────────────────────────────────────
    'ghost-book-rescan.bat': f'''@echo off
cd /d "G:\\My Drive\\Projects\\_studio"
set LOG_DIR=%~dp0logs
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
echo [%date% %time%] Ghost book rescan starting >> "{SCHED}\\logs\\ghost-book-rescan.log"
python "G:\\My Drive\\Projects\\ghost-book\\pass1_find_candidates.py" >> "{SCHED}\\logs\\ghost-book-rescan.log" 2>&1
python "G:\\My Drive\\Projects\\ghost-book\\pass1_atlantis_lore.py" >> "{SCHED}\\logs\\ghost-book-rescan.log" 2>&1
echo [%date% %time%] Done >> "{SCHED}\\logs\\ghost-book-rescan.log"
''',
}

os.makedirs(SCHED + '/logs', exist_ok=True)

for fname, content in launchers.items():
    path = os.path.join(SCHED, fname)
    with open(path, 'w', newline='\r\n') as f:
        f.write(content)
    print(f'Created: {fname}')

print(f'\nLaunchers written to: {SCHED}')
print('Next: run pass2_register_tasks.py to register with Task Scheduler')
```

### Pass 2 — Register Tasks with Windows Task Scheduler
Uses `schtasks` to create or update all scheduled entries.

```bash
python G:/My\ Drive/Projects/_studio/scheduler/register_tasks.py
```

Script (`_studio/scheduler/register_tasks.py`):

```python
import subprocess, os, sys
from datetime import datetime

SCHED = 'G:/My Drive/Projects/_studio/scheduler'
SCHED_WIN = r'G:\My Drive\Projects\_studio\scheduler'

tasks = [
    {
        'name':    'Studio\\DailyBriefing',
        'bat':     'orchestrator-briefing.bat',
        'trigger': 'DAILY',
        'time':    '08:00',
        'days':    None,
        'repeat':  None,
        'desc':    'Studio daily briefing via orchestrator',
    },
    {
        'name':    'Studio\\SupervisorCheck',
        'bat':     'supervisor-check.bat',
        'trigger': 'MINUTE',
        'time':    None,
        'days':    None,
        'repeat':  30,       # every 30 minutes
        'desc':    'Studio supervisor health check',
    },
    {
        'name':    'Studio\\NightlyCommit',
        'bat':     'nightly-commit.bat',
        'trigger': 'DAILY',
        'time':    '23:00',
        'days':    None,
        'repeat':  None,
        'desc':    'Nightly git commit of all studio projects',
    },
    {
        'name':    'Studio\\GhostBookRescan',
        'bat':     'ghost-book-rescan.bat',
        'trigger': 'WEEKLY',
        'time':    '02:00',
        'days':    'SUN',
        'repeat':  None,
        'desc':    'Weekly ghost book candidate rescan',
    },
]

def delete_task(name):
    subprocess.run(
        ['schtasks', '/delete', '/tn', name, '/f'],
        capture_output=True
    )

def create_task(task):
    bat_path = os.path.join(SCHED_WIN, task['bat'])
    cmd = [
        'schtasks', '/create',
        '/tn', task['name'],
        '/tr', f'"{bat_path}"',
        '/sc', task['trigger'],
        '/f',   # force overwrite if exists
        '/rl', 'HIGHEST',
    ]

    if task['trigger'] == 'DAILY':
        cmd += ['/st', task['time']]
    elif task['trigger'] == 'WEEKLY':
        cmd += ['/st', task['time'], '/d', task['days']]
    elif task['trigger'] == 'MINUTE':
        cmd += ['/mo', str(task['repeat']), '/st', '00:00']

    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0, result.stdout + result.stderr

results = []
print('=== Registering Studio Tasks ===\n')
for task in tasks:
    # Delete existing first to ensure clean state
    delete_task(task['name'])

    ok, output = create_task(task)
    status = 'OK' if ok else 'FAIL'
    sched_str = (
        f"Daily {task['time']}" if task['trigger'] == 'DAILY' else
        f"Every {task['repeat']}min" if task['trigger'] == 'MINUTE' else
        f"Weekly {task['days']} {task['time']}"
    )
    print(f'  [{status}] {task["name"]:<30} {sched_str}')
    if not ok:
        print(f'         {output.strip()[:80]}')
    results.append({'task': task['name'], 'status': status, 'schedule': sched_str})

# Verify all tasks are registered
print('\n=== Verification ===')
verify = subprocess.run(
    ['schtasks', '/query', '/fo', 'LIST', '/tn', 'Studio\\'],
    capture_output=True, text=True
)
if verify.returncode == 0:
    lines = [l for l in verify.stdout.splitlines() if l.strip()]
    task_names = [l.split(':',1)[1].strip() for l in lines if l.startswith('TaskName:')]
    for name in task_names:
        print(f'  Registered: {name}')
else:
    print('  (verify failed — check Task Scheduler manually)')

# Save manifest
import json
manifest = {
    'created': datetime.now().isoformat(),
    'tasks': results,
    'scheduler_folder': 'Studio\\',
    'launcher_dir': SCHED_WIN,
    'log_dir': SCHED_WIN + r'\logs'
}
json.dump(manifest, open(SCHED + '/task-manifest.json', 'w'), indent=2)
print(f'\nManifest saved to scheduler/task-manifest.json')
print('\nTo view in Task Scheduler UI: taskschd.msc -> Task Scheduler Library -> Studio')
```

### Pass 3 — Verify and Show Status
```bash
python G:/My\ Drive/Projects/_studio/scheduler/check_status.py
```

Script (`_studio/scheduler/check_status.py`):

```python
import subprocess, json, os
from datetime import datetime

SCHED = 'G:/My Drive/Projects/_studio/scheduler'
TASK_NAMES = [
    'Studio\\DailyBriefing',
    'Studio\\SupervisorCheck',
    'Studio\\NightlyCommit',
    'Studio\\GhostBookRescan',
]

print('=== Studio Task Scheduler Status ===\n')
for task in TASK_NAMES:
    result = subprocess.run(
        ['schtasks', '/query', '/fo', 'LIST', '/tn', task],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f'  MISSING: {task}')
        continue

    info = {}
    for line in result.stdout.splitlines():
        if ':' in line:
            k, _, v = line.partition(':')
            info[k.strip()] = v.strip()

    name = info.get('TaskName', task).split('\\')[-1]
    status = info.get('Status', '?')
    next_run = info.get('Next Run Time', '?')
    last_run = info.get('Last Run Time', '?')
    last_result = info.get('Last Result', '?')

    ok = status in ('Ready', 'Running')
    icon = 'OK' if ok else '!!'
    print(f'  [{icon}] {name:<22} Status: {status:<10} Next: {next_run}')
    print(f'       Last run: {last_run}  Result: {last_result}')
    print()

# Check log files for recent activity
log_dir = os.path.join(SCHED, 'logs')
if os.path.exists(log_dir):
    print('=== Recent Log Activity ===')
    for fname in sorted(os.listdir(log_dir)):
        if not fname.endswith('.log'):
            continue
        path = os.path.join(log_dir, fname)
        size = os.path.getsize(path)
        mtime = datetime.fromtimestamp(os.path.getmtime(path))
        age_h = (datetime.now() - mtime).total_seconds() / 3600
        with open(path) as f:
            lines = f.readlines()
        last_line = lines[-1].strip() if lines else '(empty)'
        print(f'  {fname:<35} {size:>6} bytes  {age_h:.1f}h ago')
        print(f'    Last: {last_line[:70]}')
```

## Run Command

```
Load scheduler-setup.md. Create all 4 Task Scheduler entries now.
```

Or step by step:
```bash
python "G:/My Drive/Projects/_studio/scheduler/create_launchers.py"
python "G:/My Drive/Projects/_studio/scheduler/register_tasks.py"
python "G:/My Drive/Projects/_studio/scheduler/check_status.py"
```

## Task Details

### Daily Briefing — 8:00 AM
- Loads orchestrator.md, runs daily briefing via Gemini Flash
- Outputs to `orchestrator-briefing.json`
- Cost: $0 (Gemini free tier)

### Supervisor Check — Every 30 Minutes
- Loads supervisor.md, runs health check
- Summarizes any completed background tasks
- Cost: $0 (rule-based, minimal Claude)

### Nightly Commit — 11:00 PM
- Loads git-commit-agent.md, commits all dirty projects
- Loads changelog-agent.md, updates changelogs
- Cost: $0 (git operations only)

### Ghost Book Rescan — Sunday 2:00 AM
- Runs pass1_find_candidates.py (12 core topics, 5 sources)
- Runs pass1_atlantis_lore.py (16 lore/atlantis topics)
- Writes fresh candidate lists for Pass 2 validation
- Cost: $0 (Internet Archive + Open Library APIs)

## Log Rotation
Logs are date-stamped per run. Clean old logs monthly:
```bash
forfiles /p "G:\My Drive\Projects\_studio\scheduler\logs" /s /m *.log /d -30 /c "cmd /c del @path"
```

## Troubleshooting

| Problem | Fix |
|---|---|
| Task not running | Check `Task Scheduler > Studio > History` tab |
| "Access denied" on create | Run `register_tasks.py` as Administrator |
| Claude not found | Ensure `claude` is in system PATH, or use full path in .bat |
| Bat file path error | Verify no spaces issue — path already quoted in script |
| Log file growing too large | Add `> logfile 2>&1` instead of `>>` to overwrite each run |

## Output Files
- `scheduler/orchestrator-briefing.bat`
- `scheduler/supervisor-check.bat`
- `scheduler/nightly-commit.bat`
- `scheduler/ghost-book-rescan.bat`
- `scheduler/task-manifest.json` — created after Pass 2
- `scheduler/logs/*.log` — per-task run logs
