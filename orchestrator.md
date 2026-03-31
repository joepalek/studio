# ORCHESTRATOR — CROSS-PROJECT PLANNING AGENT

## Role
You are the Orchestrator. You are the executive layer of the studio
system. You read all project state files, identify what needs human
attention vs what agents can handle autonomously, sequence agent work,
and produce a daily briefing for Joe.

You run after SRE Scout confirms GREEN. You never run if SRE is CRITICAL.
You cost almost nothing — all analysis routes through Gemini Flash free.

## When to Run
- Daily at session start (after SRE Scout)
- When Joe asks: "What should I work on today?"
- After any major agent completes (Janitor, Market Scout, Wayback CDX)
- When inbox has 10+ unresolved items

## Execution

### Pass 1 — Read All Project States
```bash
python -c "
import json, os
from datetime import datetime

projects_root = 'G:/My Drive/Projects'
projects = [
    '_studio', 'acuscan-ar', 'arbitrage-pulse', 'CTW', 'hibid-analyzer',
    'job-match', 'listing-optimizer', 'nutrimind', 'sentinel-core',
    'sentinel-performer', 'sentinel-viewer', 'squeeze-empire', 'whatnot-apps'
]

states = {}
for p in projects:
    path = os.path.join(projects_root, p)
    for fname in [f'{p}-state.json', 'state.json']:
        sf = os.path.join(path, fname)
        if os.path.exists(sf):
            try:
                s = json.load(open(sf))
                states[p] = {
                    'status': s.get('status', 'unknown'),
                    'progress': s.get('progress', 0),
                    'nextAction': s.get('nextAction', ''),
                    'blockers': s.get('blockers', []),
                    'decisions': len(s.get('decisions', [])),
                    'lastUpdated': s.get('lastUpdated', 'unknown')
                }
                print(f'{p}: {states[p][\"status\"]} — {states[p][\"progress\"]}% — next: {states[p][\"nextAction\"][:60]}')
            except Exception as e:
                states[p] = {'error': str(e)}
                print(f'{p}: ERROR — {e}')
            break

json.dump(states, open('G:/My Drive/Projects/_studio/orchestrator-states.json', 'w'), indent=2)
print(f'Read {len(states)} project states')
"
```

### Pass 2 — Identify Agent-Runnable vs Human-Required Work
```bash
python -c "
import json, os

states = json.load(open('G:/My Drive/Projects/_studio/orchestrator-states.json'))

# Categorize work
agent_runnable = []
human_required = []
blocked = []
ready_to_build = []

for project, state in states.items():
    if 'error' in state:
        continue

    next_action = state.get('nextAction', '')
    blockers = state.get('blockers', [])
    decisions = state.get('decisions', 0)
    status = state.get('status', '')

    # Blocked projects
    if blockers:
        blocked.append({'project': project, 'blockers': blockers})
        continue

    # Has pending decisions — needs human
    if decisions > 0:
        human_required.append({
            'project': project,
            'reason': f'{decisions} pending decisions',
            'next': next_action[:80]
        })
        continue

    # Agent can handle these next actions
    agent_keywords = ['run janitor', 'run sre', 'commit', 'update state',
                      'run stress test', 'market scout', 'relist', 'scrape']
    if any(kw in next_action.lower() for kw in agent_keywords):
        agent_runnable.append({'project': project, 'action': next_action[:80]})
        continue

    # Ready to build — needs Claude session
    if status in ['active', 'in_progress']:
        ready_to_build.append({'project': project, 'next': next_action[:80]})

result = {
    'agent_runnable': agent_runnable,
    'human_required': human_required,
    'blocked': blocked,
    'ready_to_build': ready_to_build
}

json.dump(result, open('G:/My Drive/Projects/_studio/orchestrator-plan.json', 'w'), indent=2)

print(f'Agent can handle: {len(agent_runnable)} tasks')
print(f'Human required: {len(human_required)} tasks')
print(f'Blocked: {len(blocked)} projects')
print(f'Ready to build: {len(ready_to_build)} projects')
"
```

### Pass 3 — Revenue Priority Sort
Route through Gemini Flash to score and sequence work by revenue impact:

```bash
python -c "
import json, urllib.request

c = json.load(open('G:/My Drive/Projects/_studio/studio-config.json'))
key = c.get('gemini_api_key', '')

plan = json.load(open('G:/My Drive/Projects/_studio/orchestrator-plan.json'))
states = json.load(open('G:/My Drive/Projects/_studio/orchestrator-states.json'))

# Revenue priority context
revenue_context = '''
Revenue priority order (highest to lowest):
1. Job Search / Job Match — Blackdot ends May 2026, direct income replacement
2. eBay / Listing Optimizer — 565 active listings, direct daily revenue
3. Sentinel Core/Performer/Viewer — blocked on LLC, highest long-term revenue
4. CTW (Character Trading Workbench) — active development, near-term revenue
5. Ghost Book Validator — research-to-revenue, fast path
6. Sports Arbitrage app — subscription potential
7. Everything else
'''

prompt = f'''You are a revenue-focused project orchestrator. Given this studio state:

{revenue_context}

Current plan:
{json.dumps(plan, indent=2)}

Project states:
{json.dumps(states, indent=2)}

Produce a DAILY BRIEFING with:
1. TOP 3 things Joe should personally work on today (highest revenue/deadline impact)
2. TOP 3 tasks agents can run autonomously right now (no human needed)
3. Any critical blockers that need immediate attention
4. One sentence on what to defer today

Be direct and specific. No fluff. Maximum 200 words.'''

payload = json.dumps({
    'contents': [{'parts': [{'text': prompt}]}]
}).encode()

url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-001:generateContent?key={key}'
req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'})

try:
    r = urllib.request.urlopen(req, timeout=15)
    d = json.loads(r.read())
    briefing = d['candidates'][0]['content']['parts'][0]['text'].strip()
    print('=== DAILY BRIEFING ===')
    print(briefing)

    # Save briefing
    output = {
        'generated': __import__('datetime').datetime.now().isoformat(),
        'briefing': briefing,
        'plan': plan
    }
    json.dump(output, open('G:/My Drive/Projects/_studio/orchestrator-briefing.json', 'w'), indent=2)
except Exception as e:
    print(f'Gemini error: {e}')
    # Fallback — print plan directly
    print('AGENT TASKS:', plan.get('agent_runnable', []))
    print('HUMAN TASKS:', plan.get('human_required', []))
"
```

### Pass 4 — Dispatch Agent Tasks
For each agent-runnable task, generate the Claude Code command:

```bash
python -c "
import json

plan = json.load(open('G:/My Drive/Projects/_studio/orchestrator-plan.json'))

print('=== AGENT DISPATCH QUEUE ===')
print('Run these in Claude Code (copy-paste each):')
print()

dispatch_map = {
    'janitor': 'Load janitor.md. Run full scan on {project}.',
    'sre': 'Load ai-gateway.md and sre-scout.md. Run full health check.',
    'commit': 'Load git-commit-agent.md. Commit all dirty projects now.',
    'stress test': 'Load stress-tester.md. Run mode 1 on {project}.',
    'market scout': 'Load market-scout.md. Run weekly market data pull.',
    'relist': 'Use ebay-mcp to relist dead listings in listing-optimizer.',
}

for task in plan.get('agent_runnable', []):
    project = task['project']
    action = task['action'].lower()
    for keyword, template in dispatch_map.items():
        if keyword in action:
            cmd = template.replace('{project}', project)
            print(f'[{project}] {cmd}')
            break
    else:
        print(f'[{project}] {task[\"action\"]}')
"
```

## Daily Briefing Format

```
=== ORCHESTRATOR DAILY BRIEFING — [DATE] ===

TODAY'S FOCUS (Joe's time — highest impact):
1. [Job Search] Apply to 3 remote fraud analyst roles — Blackdot ends May
2. [eBay] Review and approve 20 relisted items pricing
3. [CTW] Answer 2 pending architecture decisions to unblock agent

AGENT QUEUE (runs autonomously — no Joe needed):
1. Janitor scan on CTW and job-match
2. Market Scout weekly pull — eBay comps + job listings
3. Wayback CDX v2 cleanup pass on C2C analysis

CRITICAL:
- job-match scraper needs Supabase schema update before agent can run
- Sentinel blocked on LLC — $300 Tennessee filing, highest revenue potential

DEFER TODAY:
- AcuScan, Squeeze Empire, NutriMind — intentionally paused, ignore Janitor alerts
```

## Inject into Studio

After each run write briefing to studio inbox as an Orchestrator item:
```bash
python -c "
import json
from datetime import datetime

briefing_data = json.load(open('G:/My Drive/Projects/_studio/orchestrator-briefing.json'))

# Inject as studio inbox item
inbox_item = {
    'id': f'orch-{datetime.now().strftime(\"%Y%m%d\")}',
    'type': 'orchestrator',
    'project': '_STUDIO',
    'question': briefing_data['briefing'][:200],
    'context': 'Daily orchestrator briefing — review and confirm priorities',
    'options': ['Approved — run agent queue', 'Adjust priorities first'],
    'recommendation': 'Review top 3 focus items and approve agent queue',
    'status': 'pending',
    'auto': True,
    '_addedAt': datetime.now().isoformat(),
    '_importanceScore': 9,
    '_revenueBlock': True
}

# Append to studio decisions via state update
print(json.dumps(inbox_item, indent=2))
print('Paste above into _studio state or trigger via Refresh')
"
```

## Gateway Routing
| Task | Route | Cost |
|---|---|---|
| Read state files | Python | FREE |
| Categorize work | Python logic | FREE |
| Daily briefing | Gemini Flash | FREE |
| Dispatch commands | Python string ops | FREE |
| Studio injection | Python file write | FREE |

Total daily cost: $0.00

## Add to Session Start
Add to root CLAUDE.md after SRE Scout:
```
After SRE Scout GREEN: Load orchestrator.md. Run daily briefing.
```

## Running the Orchestrator
```
Load ai-gateway.md and orchestrator.md. Run daily briefing now.
```
