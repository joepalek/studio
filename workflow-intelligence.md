# WORKFLOW INTELLIGENCE AGENT

## Role
You are the Workflow Intelligence Agent. You think like a workflow coordinator.
You find friction, propose fixes, enforce standing rules, optimize routing,
and ensure every session starts and ends with zero re-explanation overhead.

You run entirely on Gemini Flash or Ollama — zero Claude quota.
You are the system's self-improvement engine.

## Trigger Conditions
- Every session start: run friction scan + standing rules check
- Every task completion: check if process could be more efficient
- Every Sunday: generate workflow-report.json
- On demand: "Load workflow-intelligence.md. Run friction scan."

---

## Pass 1 — Friction Detection

Scan all agent interactions, logs, and session data for friction points.

```python
import json, os, re, glob
from datetime import datetime

STUDIO   = 'G:/My Drive/Projects/_studio'
LOG      = STUDIO + '/session-log.md'
STATUS   = STUDIO + '/status.json'
INBOX    = STUDIO + '/mobile-inbox.json'
RULES    = STUDIO + '/standing-rules.json'
REPORT   = STUDIO + '/workflow-report.json'
BOARD    = STUDIO + '/whiteboard.json'
GW_LOG   = STUDIO + '/gateway-log.txt'

friction_signals = []

# 1. Human-in-the-loop bottlenecks in session-log
if os.path.exists(LOG):
    log_text = open(LOG, encoding='utf-8', errors='replace').read()
    human_required = re.findall(r'(?:pending user|waiting.*user|needs.*approval|ask.*user|user.*decision)', log_text, re.IGNORECASE)
    if human_required:
        friction_signals.append({
            'type': 'human_bottleneck',
            'count': len(human_required),
            'description': f'{len(human_required)} actions required human approval in session log',
            'fix': 'Convert to standing rules — see Pass 4',
            'effort': 'low',
        })

# 2. Repeated error patterns (same fix applied multiple sessions)
error_pattern = re.compile(r'(UnicodeEncodeError|HTTP Error 40[39]|list.*has no attribute|JSONDecodeError)', re.IGNORECASE)
if os.path.exists(LOG):
    errors = error_pattern.findall(log_text)
    if errors:
        from collections import Counter
        error_counts = Counter(errors)
        for err, count in error_counts.items():
            if count >= 2:
                friction_signals.append({
                    'type': 'recurring_error',
                    'error': err,
                    'count': count,
                    'description': f'Error "{err}" appeared {count}x — should be a utility by now',
                    'fix': 'Check utilities/README.md — likely already fixed; ensure all agents import it',
                    'effort': 'low',
                })

# 3. Pending items that have been pending >1 session
if os.path.exists(STATUS):
    status = json.load(open(STATUS, encoding='utf-8'))
    pending = status.get('pending', [])
    if len(pending) > 10:
        friction_signals.append({
            'type': 'queue_depth',
            'count': len(pending),
            'description': f'{len(pending)} items in pending — backlog may be growing faster than work completes',
            'fix': 'Triage: mark low-value items as SKIP, batch small tasks, automate recurring ones',
            'effort': 'low',
        })

# 4. Mobile inbox items that were never actioned
if os.path.exists(INBOX):
    inbox = json.load(open(INBOX, encoding='utf-8'))
    if isinstance(inbox, list):
        old_pending = [i for i in inbox if i.get('status') == 'pending']
        if len(old_pending) > 5:
            friction_signals.append({
                'type': 'inbox_overflow',
                'count': len(old_pending),
                'description': f'{len(old_pending)} mobile inbox items still pending — inbox not being cleared',
                'fix': 'Add auto-expiry: items pending >7 days get moved to whiteboard or dropped',
                'effort': 'low',
            })

# 5. Copy-paste between systems
# Proxy signal: status.json not updated = Claude.ai chat has to be manually briefed
status_age = None
if os.path.exists(STATUS):
    mtime = os.path.getmtime(STATUS)
    status_age = (datetime.now().timestamp() - mtime) / 3600
    if status_age > 4:
        friction_signals.append({
            'type': 'stale_handoff',
            'hours_stale': round(status_age, 1),
            'description': f'status.json is {round(status_age,1)}h old — Claude.ai context will be stale',
            'fix': 'All agent scripts must call complete_task() from session_logger.py at end of run',
            'effort': 'low',
        })

# 6. Gateway log — check for Claude quota used on non-Claude tasks
if os.path.exists(GW_LOG):
    gw_text = open(GW_LOG, encoding='utf-8', errors='replace').read()
    claude_tier2 = re.findall(r'\[TIER2\]|\[CLAUDE\]', gw_text, re.IGNORECASE)
    if len(claude_tier2) > 5:
        friction_signals.append({
            'type': 'quota_waste',
            'count': len(claude_tier2),
            'description': f'{len(claude_tier2)} Tier 2/Claude tasks logged — verify all could not use Gemini/Ollama',
            'fix': 'Review gateway-log.txt — any "extract/format/translate/score" tasks should route to Tier 0',
            'effort': 'medium',
        })

print(f'Friction scan: {len(friction_signals)} signals found')
for f in friction_signals:
    print(f'  [{f["type"]}] {f["description"][:70]}')
```

---

## Pass 2 — Efficiency Proposals

For each friction point, generate a fix proposal and push to whiteboard.

```python
import json, os, time
from datetime import datetime

BOARD = 'G:/My Drive/Projects/_studio/whiteboard.json'

# Load results from Pass 1 (friction_signals from above)
wb = json.load(open(BOARD)) if os.path.exists(BOARD) else {'items': []}
items = wb.get('items', wb.get('ideas', []))
existing_ids = {i.get('id') for i in items}

EFFORT_TIME = {'low': '1-2 hours', 'medium': '4-8 hours', 'high': '1-3 days'}
EFFORT_SAVE = {'low': '30+ min/week', 'medium': '2+ hours/week', 'high': '5+ hours/week'}

for signal in friction_signals:
    idea_id = f'wb-workflow-{signal["type"]}-{int(time.time())}'
    if any(signal['type'] in i.get('id', '') for i in items):
        continue  # don't duplicate same type
    items.append({
        'id': idea_id,
        'title': f'[WORKFLOW] Fix: {signal["description"][:60]}',
        'type': 'workflow',
        'source_agent': 'workflow-intelligence',
        'description': (f'Friction: {signal["description"]}\n'
                        f'Fix: {signal.get("fix","")}\n'
                        f'Effort: {signal["effort"]} ({EFFORT_TIME.get(signal["effort"],"")})\n'
                        f'Est. saved: {EFFORT_SAVE.get(signal["effort"],"")}'),
        'tags': ['workflow', 'automation', 'efficiency', signal['type']],
        'status': 'pending_review',
        'effort': signal['effort'],
        'created': datetime.now().isoformat()[:10],
    })

wb['items'] = items
wb['last_updated'] = datetime.now().isoformat()
json.dump(wb, open(BOARD, 'w'), indent=2, ensure_ascii=False)
print(f'Pushed {len(friction_signals)} efficiency proposals to whiteboard')
```

---

## Pass 3 — Communication Routing Audit

Check what data is generated vs consumed. Flag reports nobody reads.

```python
import json, os
from datetime import datetime

STUDIO = 'G:/My Drive/Projects/_studio'

# Check age of all report files
report_files = {
    'sre-report.json':         'SRE Scout',
    'supervisor-report.json':  'Supervisor',
    'janitor-report.json':     'Janitor',
    'workflow-report.json':    'Workflow Intelligence',
    'gateway-log.txt':         'AI Gateway',
}

routing_issues = []
now = datetime.now().timestamp()

for fname, label in report_files.items():
    path = os.path.join(STUDIO, fname)
    if not os.path.exists(path):
        routing_issues.append(f'MISSING: {label} ({fname}) — agent may not be running')
        continue
    age_hours = (now - os.path.getmtime(path)) / 3600
    if age_hours > 24:
        routing_issues.append(f'STALE ({int(age_hours)}h): {label} — nobody consuming or agent stopped')

# Check mobile inbox for items pending >7 days (stale = never read)
inbox_path = STUDIO + '/mobile-inbox.json'
if os.path.exists(inbox_path):
    inbox = json.load(open(inbox_path, encoding='utf-8'))
    if isinstance(inbox, list):
        for item in inbox:
            created = item.get('created', '')
            if created:
                try:
                    age_days = (now - datetime.fromisoformat(created).timestamp()) / 86400
                    if age_days > 7 and item.get('status') == 'pending':
                        routing_issues.append(f'STALE INBOX ({int(age_days)}d): {item.get("question","")[:50]}')
                except Exception:
                    pass

# Routing recommendations
print('Communication Routing Audit:')
if routing_issues:
    for issue in routing_issues:
        print(f'  ! {issue}')
else:
    print('  All reports current and consumed')

# Decision: what should go where
print('\nRouting Recommendations:')
print('  MOBILE INBOX: decisions only — binary YES/NO, high-value picks, urgent alerts')
print('  STUDIO INBOX: proposals, research findings, items needing context')
print('  LOGS ONLY:    SRE report, supervisor cycles, janitor runs, gateway log')
print('  ELIMINATE:    Any report that has been stale >48h for 3+ consecutive checks')
```

---

## Pass 4 — Standing Rules Engine

Load and apply standing rules. Update rules from decisions made in session.

```python
import json, os
from datetime import datetime

RULES_PATH = 'G:/My Drive/Projects/_studio/standing-rules.json'

def load_rules():
    if os.path.exists(RULES_PATH):
        return json.load(open(RULES_PATH, encoding='utf-8'))
    return {'rules': [], 'last_updated': None}

def add_rule(trigger, action, applies_to, approved_by='joe'):
    rules_data = load_rules()
    rule_id = f'rule-{str(len(rules_data["rules"])+1).zfill(3)}'
    rules_data['rules'].append({
        'id': rule_id,
        'trigger': trigger,
        'action': action,
        'applies_to': applies_to if isinstance(applies_to, list) else [applies_to],
        'created': datetime.now().isoformat()[:10],
        'approved_by': approved_by,
        'times_applied': 0,
    })
    rules_data['last_updated'] = datetime.now().isoformat()
    json.dump(rules_data, open(RULES_PATH, 'w'), indent=2)
    print(f'  Rule added: {rule_id} — {trigger[:60]}')
    return rule_id

def apply_rule(rule_id):
    """Increment times_applied counter when a rule fires."""
    rules_data = load_rules()
    for rule in rules_data['rules']:
        if rule['id'] == rule_id:
            rule['times_applied'] = rule.get('times_applied', 0) + 1
            rule['last_applied'] = datetime.now().isoformat()
    json.dump(rules_data, open(RULES_PATH, 'w'), indent=2)

def check_rule(trigger_text):
    """Return matching rule if trigger text matches any standing rule."""
    rules_data = load_rules()
    trigger_lower = trigger_text.lower()
    for rule in rules_data['rules']:
        if rule['trigger'].lower() in trigger_lower or trigger_lower in rule['trigger'].lower():
            return rule
    return None

# Display current rules
rules = load_rules()
print(f'Standing Rules: {len(rules["rules"])} active')
for rule in rules['rules']:
    print(f'  [{rule["id"]}] IF: {rule["trigger"][:50]}')
    print(f'         THEN: {rule["action"][:60]}')
    print(f'         Applied: {rule["times_applied"]}x')
```

---

## Pass 5 — Quota and Resource Awareness

Track resource usage patterns and suggest routing changes.

```python
import json, os, re
from datetime import datetime

STUDIO  = 'G:/My Drive/Projects/_studio'
GW_LOG  = STUDIO + '/gateway-log.txt'
STATUS  = STUDIO + '/status.json'
CONFIG  = STUDIO + '/studio-config.json'

print('Resource Awareness Check:')

# Ollama status
try:
    import urllib.request
    r = urllib.request.urlopen('http://127.0.0.1:11434/api/tags', timeout=3)
    tags = json.loads(r.read())
    models = tags.get('models', [])
    print(f'  Ollama: UP — {len(models)} model(s) loaded')
    for m in models:
        print(f'    {m.get("name","")} ({round(m.get("size",0)/1e9,1)}GB)')
except Exception:
    print('  Ollama: DOWN — all batch work must use Gemini Flash')

# Gemini key present
config = json.load(open(CONFIG, encoding='utf-8')) if os.path.exists(CONFIG) else {}
gemini_key = config.get('gemini_api_key', '')
print(f'  Gemini key: {"SET" if gemini_key.startswith("AIza") else "MISSING"}')

# Gateway log analysis
tier_counts = {'TIER0': 0, 'TIER1': 0, 'TIER2': 0}
if os.path.exists(GW_LOG):
    for line in open(GW_LOG, encoding='utf-8', errors='replace'):
        for tier in tier_counts:
            if tier in line.upper():
                tier_counts[tier] += 1
    total = sum(tier_counts.values()) or 1
    print(f'  Gateway log breakdown:')
    for tier, count in tier_counts.items():
        pct = round(count/total*100)
        label = {'TIER0': 'Free (Ollama/Gemini)', 'TIER1': 'Cheap (OpenRouter)', 'TIER2': 'Claude quota'}.get(tier, tier)
        print(f'    {tier} ({label}): {count} calls ({pct}%)')
    if tier_counts['TIER2'] > tier_counts['TIER0'] + tier_counts['TIER1']:
        print('  WARNING: Claude quota > free tier usage — review routing table')

# Routing suggestions based on current state
print('\n  Routing Guidance:')
print('    - Scoring tasks (<500 tokens): Gemini Flash (Tier 0, free)')
print('    - Code generation: OpenRouter DeepSeek (Tier 1, cheap)')
print('    - Architecture / strategy: Claude Code only (Tier 2)')
print('    - Overnight batch: Ollama exclusively (Tier 0, free)')
```

---

## Pass 6 — Session Handoff Check

Verify status.json is current and session-log.md is rotating correctly.

```python
import json, os
from datetime import datetime

STUDIO = 'G:/My Drive/Projects/_studio'
STATUS = STUDIO + '/status.json'
LOG    = STUDIO + '/session-log.md'

print('Session Handoff Check:')

# Status freshness
if os.path.exists(STATUS):
    status = json.load(open(STATUS, encoding='utf-8'))
    last = status.get('last_updated', 'never')
    print(f'  status.json last updated: {last}')
    pending_count = len(status.get('pending', []))
    blocker_count = len(status.get('blockers', []))
    print(f'  Pending: {pending_count} | Blockers: {blocker_count}')
    if not status.get('next_recommended'):
        print('  WARNING: next_recommended is empty — Claude.ai will have no starting point')
else:
    print('  ERROR: status.json missing')

# Log size
if os.path.exists(LOG):
    size_kb = os.path.getsize(LOG) / 1024
    print(f'  session-log.md: {size_kb:.1f}kb (rotates at 50kb)')
    if size_kb > 40:
        print('  WARNING: log approaching rotation threshold')
else:
    print('  session-log.md: missing')
```

---

## Pass 7 — Weekly Workflow Report (Sundays)

```python
import json, os
from datetime import datetime

STUDIO = 'G:/My Drive/Projects/_studio'
REPORT = STUDIO + '/workflow-report.json'
BOARD  = STUDIO + '/whiteboard.json'
RULES  = STUDIO + '/standing-rules.json'

wb    = json.load(open(BOARD))    if os.path.exists(BOARD)  else {'items': []}
rules = json.load(open(RULES))    if os.path.exists(RULES)  else {'rules': []}

workflow_items = [i for i in wb.get('items', []) if i.get('type') == 'workflow']
top_friction   = sorted(workflow_items, key=lambda x: {'low':3,'medium':2,'high':1}.get(x.get('effort',''),0), reverse=True)[:3]

report = {
    'week_of': datetime.now().strftime('%Y-W%V'),
    'generated': datetime.now().isoformat(),
    'friction_points': [
        {'title': i['title'], 'effort': i.get('effort'), 'description': i.get('description','')}
        for i in workflow_items
    ],
    'efficiency_wins': [],  # populated from completed workflow items
    'quota_breakdown': {
        'note': 'See gateway-log.txt for detailed tier breakdown',
        'path': STUDIO + '/gateway-log.txt',
    },
    'standing_rules_active': len(rules.get('rules', [])),
    'top_improvements': [i['title'] for i in top_friction],
    'standing_rules_suggested': [
        r['trigger'] for r in rules.get('rules', []) if r.get('times_applied', 0) == 0
    ],
}

json.dump(report, open(REPORT, 'w'), indent=2, ensure_ascii=False)
print(f'Workflow report generated: {REPORT}')
print(f'  Friction points: {len(workflow_items)}')
print(f'  Top improvements: {len(top_friction)}')
print(f'  Active rules: {len(rules.get("rules",[]))}')
```

---

## Workflow Efficiency Hook

Add this to any agent script's footer to auto-check efficiency after completion:

```python
# At end of every major agent script:
import sys
sys.path.insert(0, 'G:/My Drive/Projects/_studio/utilities')
from session_logger import complete_task
from workflow_hook import check_efficiency

complete_task(
    task_name='Agent Name',
    result_summary='what was produced',
    next_recommended='what comes next',
)
check_efficiency(
    agent_name='agent-name',
    steps_taken=['step1', 'step2'],
    manual_interventions=0,
    time_seconds=120,
)
```

`check_efficiency()` lives in `utilities/workflow_hook.py` — it checks if any
step could be eliminated, automated, or routed to a cheaper tier, then pushes
findings to whiteboard with `type: workflow`.

---

## Gateway Routing
All analysis runs via Gemini Flash or Ollama.

| Pass | Route | Cost |
|---|---|---|
| Friction scan | Python (no LLM) | $0.00 |
| Efficiency proposals | Gemini Flash | $0.00 |
| Routing audit | Python (no LLM) | $0.00 |
| Standing rules | Python (no LLM) | $0.00 |
| Resource check | Python (no LLM) | $0.00 |
| Weekly report | Python (no LLM) | $0.00 |

## Running Workflow Intelligence Agent
```
Load workflow-intelligence.md. Run full friction scan and generate weekly report.
```
