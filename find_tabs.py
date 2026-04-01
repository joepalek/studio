import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

c = open('G:/My Drive/Projects/_studio/auto_answer_gemini.py', encoding='utf-8', errors='replace').read()
lines = c.split('\n')
print('=== auto_answer_gemini.py encoding/write_status ===')
for i, l in enumerate(lines, 1):
    if any(x in l for x in ['encoding', 'charmap', 'write_status', 'status', 'open(', 'errors=']):
        print(str(i) + ': ' + l.strip()[:90])

# Also check if the scheduler logs dir exists
import os
log_dir = 'G:/My Drive/Projects/_studio/scheduler/logs'
print()
print('Scheduler logs dir exists:', os.path.exists(log_dir))
if os.path.exists(log_dir):
    logs = os.listdir(log_dir)
    print('Log files:', logs[:10])
    # Check most recent overnight-job-delta log for errors
    for f in logs:
        if 'job-delta' in f or 'harvest' in f:
            fpath = log_dir + '/' + f
            content = open(fpath, encoding='utf-8', errors='replace').read()
            lines2 = content.strip().split('\n')
            print()
            print('Last 5 lines of ' + f + ':')
            for l in lines2[-5:]: print('  ' + l)
