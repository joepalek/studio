import sys, json, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
STUDIO = 'G:/My Drive/Projects/_studio'

# Read full orchestrator briefing
ob = json.load(open(STUDIO + '/orchestrator-briefing.json', encoding='utf-8', errors='replace'))
print('=== ORCHESTRATOR BRIEFING (2026-03-31) ===')
print(ob.get('briefing', '')[:2000])
print()

# Read full supervisor-report  
sr = json.load(open(STUDIO + '/supervisor-report.json', encoding='utf-8', errors='replace'))
print('=== SUPERVISOR REPORT ===')
print(json.dumps(sr, indent=2)[:1000])
