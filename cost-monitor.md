# COST MONITOR — API SPEND TRACKER

## Role
You are the Cost Monitor. You track API token spend and costs across
all models used by the studio system. You read gateway-log.txt and
Claude Code session data to produce weekly spend reports and budget
alerts.

Zero LLM needed. Pure Python math.

## When to Run
- Weekly (Sunday nights)
- When gateway-log.txt exceeds 1000 lines
- On demand: "How much have I spent this week?"

## Cost Reference Table (2026 pricing)

| Model | Input $/1M tokens | Output $/1M tokens |
|---|---|---|
| Claude Sonnet 4 | $3.00 | $15.00 |
| Claude Haiku | $0.25 | $1.25 |
| Gemini Flash 1.5 | $0.075 | $0.30 |
| GPT-4o mini | $0.15 | $0.60 |
| DeepSeek Coder | $0.14 | $0.28 |
| Ollama local | $0.00 | $0.00 |

## Execution

### Pass 1 — Read gateway-log.txt
```bash
python -c "
import json, os, re
from datetime import datetime, timedelta

log_path = 'G:/My Drive/Projects/_studio/gateway-log.txt'

if not os.path.exists(log_path):
    print('No gateway-log.txt found — no tracked usage yet')
    print('Gateway log will be created when agents start running through the gateway')
    exit(0)

# Parse log entries
# Format: [GATEWAY] [DATE] [TIER] [MODEL] [TASK-TYPE] [RESULT] [EST-COST: \$X.XX]
entries = []
with open(log_path) as f:
    for line in f:
        line = line.strip()
        if not line or not line.startswith('[GATEWAY]'):
            continue
        # Extract cost
        cost_match = re.search(r'EST-COST:\s*\\\$?([\d.]+)', line)
        model_match = re.search(r'\[([^\]]+)\]\s*\[TASK', line)
        date_match = re.search(r'\[(\d{4}-\d{2}-\d{2})', line)

        entries.append({
            'raw': line,
            'date': date_match.group(1) if date_match else 'unknown',
            'cost': float(cost_match.group(1)) if cost_match else 0.0,
        })

# Weekly summary
week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
weekly = [e for e in entries if e['date'] >= week_ago]
total_week = sum(e['cost'] for e in weekly)
total_all = sum(e['cost'] for e in entries)

print(f'Total entries logged: {len(entries)}')
print(f'This week: {len(weekly)} calls, \${total_week:.4f}')
print(f'All time: \${total_all:.4f}')
"
```

### Pass 2 — Estimate Claude Code session costs
```bash
python -c "
import os, glob, json
from datetime import datetime, timedelta

# Claude Code writes JSONL transcripts
claude_dir = os.path.expanduser(r'~\.claude\projects')
if not os.path.exists(claude_dir):
    print('No Claude Code session data found')
    exit(0)

# Estimate tokens from JSONL file sizes
# Rough estimate: 1 byte ≈ 0.3 tokens for JSON
week_ago = datetime.now() - timedelta(days=7)
total_bytes = 0
session_count = 0

for f in glob.glob(os.path.join(claude_dir, '**', '*.jsonl'), recursive=True):
    mtime = datetime.fromtimestamp(os.path.getmtime(f))
    if mtime > week_ago:
        total_bytes += os.path.getsize(f)
        session_count += 1

est_tokens = total_bytes * 0.3
# Assume 70% input (Sonnet \$3/1M) + 30% output (Sonnet \$15/1M)
est_cost = (est_tokens * 0.7 / 1_000_000 * 3.00) + (est_tokens * 0.3 / 1_000_000 * 15.00)

print(f'Claude Code sessions this week: {session_count}')
print(f'Estimated tokens: {est_tokens:,.0f}')
print(f'Estimated cost: \${est_cost:.2f}')
print('(Rough estimate — actual usage in Anthropic console)')
"
```

### Pass 3 — Budget alert check
```bash
python -c "
import json

# Budget thresholds
WEEKLY_BUDGET = 10.00   # \$10/week total
CLAUDE_BUDGET = 8.00    # \$8/week Claude only
GEMINI_BUDGET = 0.50    # \$0.50/week Gemini (mostly free tier)

# Load any tracked costs
try:
    costs = json.load(open('G:/My Drive/Projects/_studio/cost-report.json'))
    weekly_total = costs.get('weekly_total', 0)
    claude_total = costs.get('claude_estimate', 0)
except:
    weekly_total = 0
    claude_total = 0

alerts = []
if weekly_total > WEEKLY_BUDGET * 0.8:
    alerts.append(f'WARNING: Weekly spend \${weekly_total:.2f} approaching budget \${WEEKLY_BUDGET}')
if claude_total > CLAUDE_BUDGET * 0.8:
    alerts.append(f'WARNING: Claude spend \${claude_total:.2f} approaching budget \${CLAUDE_BUDGET}')

if alerts:
    for a in alerts:
        print(a)
    print('Consider routing more tasks through Gemini Flash or Ollama')
else:
    print('Spend within budget — all clear')
"
```

### Pass 4 — Write cost report
```bash
python -c "
import json
from datetime import datetime

report = {
    'generated': datetime.now().isoformat(),
    'period': '7 days',
    'gateway_calls': 0,
    'gateway_cost': 0.0,
    'claude_estimate': 0.0,
    'weekly_total': 0.0,
    'by_model': {
        'ollama': {'calls': 0, 'cost': 0.0},
        'gemini_flash': {'calls': 0, 'cost': 0.0},
        'openrouter': {'calls': 0, 'cost': 0.0},
        'claude': {'calls': 0, 'cost': 0.0},
    },
    'budget_status': 'GREEN',
    'notes': 'Gateway log not yet populated — run agents through gateway to track costs'
}

json.dump(report, open('G:/My Drive/Projects/_studio/cost-report.json', 'w'), indent=2)
print('Cost report written to cost-report.json')
print('Run agents through ai-gateway.md to start tracking actual costs')
"
```

## Weekly Cost Report Format
```
=== COST MONITOR — WEEK OF [DATE] ===

By model:
  Ollama (local):    FREE    — 847 calls
  Gemini Flash:      \$0.04  — 312 calls  
  OpenRouter:        \$0.18  — 45 calls
  Claude Sonnet:     \$4.23  — 12 sessions

Weekly total:        \$4.45
Budget remaining:    \$5.55 of \$10.00

Biggest spender:     CTW session (3,200 tokens output — \$0.048)
Best optimization:   Wayback CDX ran 100% on Ollama — \$0.00

VERDICT: GREEN — under budget
```

## Gateway Routing
| Task | Route | Cost |
|---|---|---|
| Parse log files | Python | FREE |
| Token estimation | Python math | FREE |
| Budget alerts | Python | FREE |
| Everything | No LLM needed | $0.00 |

## Running Cost Monitor
```
Load cost-monitor.md. Run weekly cost report.
```
