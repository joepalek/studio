import sys, subprocess
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

result = subprocess.run(['schtasks', '/query', '/fo', 'csv', '/v'],
    capture_output=True, text=True, encoding='utf-8', errors='replace')

lines = result.stdout.split('\n')
headers = None
tasks = {}

for line in lines:
    line = line.strip()
    if not line: continue
    parts = [p.strip('"') for p in line.split('","')]
    if len(parts) < 7: continue
    if parts[0] == 'HostName' and not headers:
        headers = parts; continue
    if headers and len(parts) >= 7:
        name = parts[1]
        status = parts[3]
        last_run = parts[4]
        last_result = parts[6]
        if any(x in name for x in ['Studio','Agent','Overnight','Nightly','Monthly','Sidebar','Daily','Supervisor']):
            if 'SpacePort' in name or 'Firefox' in name: continue
            tasks[name] = {'status': status, 'last_run': last_run, 'result': last_result}

ok, disabled, err214, other_err = [], [], [], []
for name, info in sorted(tasks.items()):
    r = info['result']
    short = name.split('\\')[-1]
    if r == '0':
        ok.append(short)
    elif '267' in r:
        disabled.append(short)
    elif r in ('-214','-2147024894'):
        err214.append(short)
    else:
        other_err.append((short, r))

print('=== RUNNING OK (' + str(len(ok)) + ') ===')
for n in ok: print('  ' + n)

print()
print('=== DISABLED/267011 (' + str(len(disabled)) + ') ===')
for n in disabled: print('  ' + n)

print()
print('=== ERR:-214 ACCOUNT ISSUE (' + str(len(err214)) + ') ===')
for n in err214: print('  ' + n)

print()
print('=== OTHER (' + str(len(other_err)) + ') ===')
for n, r in other_err: print('  ' + n + ' ERR:' + r)
