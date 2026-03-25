import subprocess, os, json
from datetime import datetime

SCHED_WIN = r'G:\My Drive\Projects\_studio\scheduler'

tasks = [
    {
        'name':    r'Studio\DailyBriefing',
        'bat':     'orchestrator-briefing.bat',
        'trigger': 'DAILY',
        'time':    '08:00',
        'days':    None,
        'mo':      None,
    },
    {
        'name':    r'Studio\SupervisorCheck',
        'bat':     'supervisor-check.bat',
        'trigger': 'MINUTE',
        'time':    '00:00',
        'days':    None,
        'mo':      '30',
    },
    {
        'name':    r'Studio\NightlyCommit',
        'bat':     'nightly-commit.bat',
        'trigger': 'DAILY',
        'time':    '23:00',
        'days':    None,
        'mo':      None,
    },
    {
        'name':    r'Studio\GhostBookRescan',
        'bat':     'ghost-book-rescan.bat',
        'trigger': 'WEEKLY',
        'time':    '02:00',
        'days':    'SUN',
        'mo':      None,
    },
    # --- Overnight batch tasks ---
    {
        'name':    r'Studio\OvernightVintageAgent',
        'bat':     'overnight-vintage-agent.bat',
        'trigger': 'WEEKLY',
        'time':    '01:00',
        'days':    'MON',
        'mo':      None,
    },
    {
        'name':    r'Studio\OvernightGhostBookPass3',
        'bat':     'overnight-ghost-book-pass3.bat',
        'trigger': 'WEEKLY',
        'time':    '01:30',
        'days':    'WED',
        'mo':      None,
    },
    {
        'name':    r'Studio\OvernightProductArchaeology',
        'bat':     'overnight-product-archaeology.bat',
        'trigger': 'DAILY',
        'time':    '02:00',
        'days':    None,
        'mo':      None,
    },
    {
        'name':    r'Studio\OvernightJobDelta',
        'bat':     'overnight-job-delta.bat',
        'trigger': 'DAILY',
        'time':    '03:00',
        'days':    None,
        'mo':      None,
    },
    {
        'name':    r'Studio\OvernightAutoAnswer',
        'bat':     'overnight-auto-answer.bat',
        'trigger': 'DAILY',
        'time':    '03:30',
        'days':    None,
        'mo':      None,
    },
    {
        'name':    r'Studio\OvernightWhiteboardScore',
        'bat':     'overnight-whiteboard-score.bat',
        'trigger': 'DAILY',
        'time':    '04:00',
        'days':    None,
        'mo':      None,
    },
]

def delete_task(name):
    subprocess.run(['schtasks', '/delete', '/tn', name, '/f'], capture_output=True)

def create_task(task):
    bat_path = os.path.join(SCHED_WIN, task['bat'])
    cmd = ['schtasks', '/create', '/tn', task['name'], '/tr', bat_path,
           '/sc', task['trigger'], '/f', '/rl', 'HIGHEST']
    if task['time']:
        cmd += ['/st', task['time']]
    if task['days']:
        cmd += ['/d', task['days']]
    if task['mo']:
        cmd += ['/mo', task['mo']]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0, (result.stdout + result.stderr).strip()

results = []
print('=== Registering Studio Tasks ===\n')
for task in tasks:
    delete_task(task['name'])
    ok, out = create_task(task)
    status = 'OK  ' if ok else 'FAIL'
    sched_map = {
        'DAILY':  f"Daily {task['time']}",
        'MINUTE': f"Every {task['mo']}min",
        'WEEKLY': f"Weekly {task['days']} {task['time']}",
    }
    sched_str = sched_map.get(task['trigger'], task['trigger'])
    short_name = task['name'].split('\\')[-1]
    print(f'  [{status}] {short_name:<22} {sched_str}')
    if not ok:
        print(f'           Error: {out[:80]}')
    results.append({'task': task['name'], 'status': 'OK' if ok else 'FAIL', 'schedule': sched_str})

# Verify
print('\n=== Verification ===')
verify = subprocess.run(['schtasks', '/query', '/fo', 'LIST', '/tn', r'Studio\\'],
                        capture_output=True, text=True)
if verify.returncode == 0:
    for line in verify.stdout.splitlines():
        if line.startswith('TaskName:'):
            print(f'  Registered: {line.split(":",1)[1].strip()}')
else:
    print('  Verify via: taskschd.msc -> Task Scheduler Library -> Studio')

manifest = {
    'created': datetime.now().isoformat(),
    'tasks': results,
    'scheduler_folder': 'Studio\\',
    'launcher_dir': SCHED_WIN,
    'log_dir': SCHED_WIN + r'\logs'
}
sched_fwd = SCHED_WIN.replace('\\', '/')
json.dump(manifest, open(sched_fwd + '/task-manifest.json', 'w'), indent=2)
print('\nManifest saved to scheduler/task-manifest.json')
print('To view: taskschd.msc -> Task Scheduler Library -> Studio')
