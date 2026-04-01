import sys, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
STUDIO = 'G:/My Drive/Projects/_studio'
SCHED  = STUDIO + '/scheduler'

disabled = {
    'WhiteboardAgent':    'whiteboard-agent.md',
    'WhiteboardScorer':   'overnight-whiteboard-score.bat',
    'SkillImprover':      'skill-improver.md',
    'PeerReview':         'peer-review.md',
    'MonthlyJobDiscovery':'monthly-job-discovery.bat',
    'SidebarBridge':      'start-bridge.bat',
    'CommonCrawlTrigger': None,
}

print('Disabled task bat status:')
for task, bat in sorted(disabled.items()):
    if not bat:
        print(f'  {task:<28} intentionally parked')
        continue
    full = SCHED + '/' + bat if not bat.endswith('.md') else STUDIO + '/' + bat
    exists = os.path.exists(full)
    kind = 'BAT' if bat.endswith('.bat') else 'MD'
    print(f'  {task:<28} {kind} {"✓" if exists else "✗"} {bat}')

# Check VectorReindex - find the actual script
print()
print('VectorReindex script search:')
for f in os.listdir(STUDIO):
    if 'vector' in f.lower() and 'reindex' in f.lower():
        print('  FOUND:', f)
for f in os.listdir(SCHED):
    if 'vector' in f.lower():
        print('  SCHED:', f)

# Check Heartbeat script
print()
print('HeartbeatCheck script search:')
for f in os.listdir(STUDIO):
    if 'heartbeat' in f.lower():
        print('  FOUND:', f, '(' + str(os.path.getsize(STUDIO+'/'+f)) + 'b)')
