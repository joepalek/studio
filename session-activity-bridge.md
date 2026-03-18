# SESSION ACTIVITY BRIDGE — CLAUDE CODE → STUDIO LOG

## Role
You are the Session Activity Bridge. You are a lightweight Python script
that tails Claude Code's JSONL transcript files and writes structured
activity summaries to the studio session log. Zero AI cost. Zero quota.
Pure file watching.

This solves the "two separate systems" problem — Claude Code activity
becomes visible in studio.html without copy-pasting transcripts.

## How It Works
1. Claude Code writes all session activity to JSONL files at:
   `C:\Users\jpalek\.claude\projects\[project-hash]\*.jsonl`
2. This bridge watches those files for new entries
3. Extracts: tool calls, file writes, bash commands, agent completions
4. Writes a structured summary to `_studio\session-activity.json`
5. Studio reads `session-activity.json` on Refresh and injects into session log

## Installation

Save `session-bridge.py` to `G:\My Drive\Projects\_studio\session-bridge.py`

Then run it in a separate PowerShell window before starting Claude Code:
```powershell
cd "G:\My Drive\Projects\_studio"
python session-bridge.py
```

Leave it running in the background. It uses near-zero CPU.

## session-bridge.py

```python
#!/usr/bin/env python3
"""
Session Activity Bridge
Watches Claude Code JSONL transcripts → writes to studio session-activity.json
Run in background: python session-bridge.py
"""

import os, json, time, glob, re
from datetime import datetime
from pathlib import Path

# Config
CLAUDE_PROJECTS_DIR = os.path.expanduser(r'~\.claude\projects')
STUDIO_OUTPUT = r'G:\My Drive\Projects\_studio\session-activity.json'
POLL_INTERVAL = 5  # seconds between checks
MAX_ENTRIES = 100  # keep last N entries in output

# Track what we've already processed
seen_positions = {}  # file_path -> last byte position
activity_log = []

def load_existing():
    """Load existing activity log if present"""
    global activity_log
    try:
        if os.path.exists(STUDIO_OUTPUT):
            data = json.load(open(STUDIO_OUTPUT))
            activity_log = data.get('entries', [])[-MAX_ENTRIES:]
    except:
        activity_log = []

def parse_jsonl_entry(line):
    """Parse a single JSONL line from Claude Code transcript"""
    try:
        entry = json.loads(line.strip())
    except:
        return None

    msg_type = entry.get('type', '')
    content = entry.get('message', {})

    # Tool use — agent doing something
    if msg_type == 'assistant' and isinstance(content, dict):
        parts = content.get('content', [])
        if isinstance(parts, list):
            for part in parts:
                if isinstance(part, dict) and part.get('type') == 'tool_use':
                    tool = part.get('name', '')
                    inp = part.get('input', {})

                    if tool == 'bash':
                        cmd = inp.get('command', '')[:80]
                        return {'type': 'bash', 'text': f'$ {cmd}', 'icon': '⬡'}

                    elif tool in ('write_file', 'create_file'):
                        path = inp.get('path', inp.get('file_path', ''))
                        fname = os.path.basename(path)
                        return {'type': 'write', 'text': f'Wrote {fname}', 'icon': '✎'}

                    elif tool == 'str_replace_editor':
                        path = inp.get('path', '')
                        fname = os.path.basename(path)
                        cmd = inp.get('command', 'edit')
                        return {'type': 'edit', 'text': f'{cmd} {fname}', 'icon': '✎'}

                    elif tool == 'read_file':
                        path = inp.get('path', '')
                        fname = os.path.basename(path)
                        return {'type': 'read', 'text': f'Read {fname}', 'icon': '◎'}

                    elif tool in ('git', 'run_terminal_cmd'):
                        cmd = inp.get('command', '')[:60]
                        return {'type': 'git', 'text': cmd, 'icon': '⎇'}

    # Tool result — completion signal
    if msg_type == 'tool' and content:
        result_text = str(content)[:100]
        if 'error' in result_text.lower():
            return {'type': 'error', 'text': result_text[:80], 'icon': '✗'}

    # Text response — agent commentary
    if msg_type == 'assistant' and isinstance(content, dict):
        text_parts = [p.get('text','') for p in content.get('content',[]) if isinstance(p,dict) and p.get('type')=='text']
        full_text = ' '.join(text_parts).strip()
        if full_text and len(full_text) > 20:
            # Only capture meaningful lines — skip filler
            first_line = full_text.split('\n')[0][:100]
            if any(kw in first_line.lower() for kw in ['complete', 'done', 'fixed', 'created', 'found', 'error', 'success', 'fail', 'running', 'built']):
                return {'type': 'agent', 'text': first_line, 'icon': '●'}

    return None

def scan_new_activity():
    """Scan all Claude Code JSONL files for new entries"""
    global activity_log

    if not os.path.exists(CLAUDE_PROJECTS_DIR):
        return 0

    new_entries = 0
    jsonl_files = glob.glob(os.path.join(CLAUDE_PROJECTS_DIR, '**', '*.jsonl'), recursive=True)

    # Sort by modification time — most recent first
    jsonl_files.sort(key=lambda f: os.path.getmtime(f), reverse=True)

    # Only check files modified in last 2 hours
    cutoff = time.time() - 7200
    recent_files = [f for f in jsonl_files if os.path.getmtime(f) > cutoff]

    for filepath in recent_files[:5]:  # Max 5 active files
        last_pos = seen_positions.get(filepath, 0)
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                f.seek(last_pos)
                new_lines = f.readlines()
                seen_positions[filepath] = f.tell()
        except:
            continue

        for line in new_lines:
            if not line.strip():
                continue
            parsed = parse_jsonl_entry(line)
            if parsed:
                parsed['time'] = datetime.now().strftime('%H:%M:%S')
                parsed['project'] = extract_project_from_path(filepath)
                activity_log.append(parsed)
                new_entries += 1

    # Keep only last MAX_ENTRIES
    if len(activity_log) > MAX_ENTRIES:
        activity_log = activity_log[-MAX_ENTRIES:]

    return new_entries

def extract_project_from_path(filepath):
    """Try to guess project name from file path"""
    parts = Path(filepath).parts
    for part in reversed(parts):
        if part not in ('.claude', 'projects', 'claude') and not part.endswith('.jsonl'):
            # Check if matches a known project folder
            known = ['_studio','CTW','job-match','nutrimind','acuscan-ar',
                     'squeeze-empire','sentinel-core','sentinel-performer',
                     'sentinel-viewer','arbitrage-pulse','hibid-analyzer',
                     'listing-optimizer','whatnot-apps']
            for k in known:
                if k.lower() in part.lower():
                    return k
    return '_studio'

def write_output():
    """Write current activity log to studio output file"""
    output = {
        'updated': datetime.now().isoformat(),
        'entry_count': len(activity_log),
        'entries': activity_log
    }
    try:
        with open(STUDIO_OUTPUT, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2)
    except Exception as e:
        print(f'Write error: {e}')

def main():
    print('Session Activity Bridge started')
    print(f'Watching: {CLAUDE_PROJECTS_DIR}')
    print(f'Output:   {STUDIO_OUTPUT}')
    print(f'Poll interval: {POLL_INTERVAL}s')
    print('Ctrl+C to stop\n')

    load_existing()

    while True:
        try:
            new = scan_new_activity()
            if new > 0:
                write_output()
                print(f'[{datetime.now().strftime("%H:%M:%S")}] +{new} new entries ({len(activity_log)} total)')
            time.sleep(POLL_INTERVAL)
        except KeyboardInterrupt:
            print('\nBridge stopped.')
            break
        except Exception as e:
            print(f'Error: {e}')
            time.sleep(POLL_INTERVAL)

if __name__ == '__main__':
    main()
```

## Studio Integration

Studio reads `session-activity.json` on Refresh and injects entries
into the session log panel. Add this to the studio Refresh function:

The bridge writes entries in this format:
```json
{
  "updated": "2026-03-18T23:45:00",
  "entry_count": 42,
  "entries": [
    {"time": "23:41:15", "type": "bash", "text": "$ git add -A", "icon": "⬡", "project": "_studio"},
    {"time": "23:41:18", "type": "write", "text": "Wrote sre-report.json", "icon": "✎", "project": "_studio"},
    {"time": "23:41:22", "type": "agent", "text": "All 13 projects committed and clean", "icon": "●", "project": "_studio"}
  ]
}
```

## How to Run Tonight

Open a second PowerShell terminal (not your Claude Code one) and run:
```powershell
cd "G:\My Drive\Projects\_studio"
python session-bridge.py
```

Leave it running. It will watch the Wayback CDX overnight job and write
activity to session-activity.json. In the morning hit Refresh in studio
and the session log will show everything that happened overnight.

## Gateway Routing
| Task | Route | Cost |
|---|---|---|
| File watching | Python stdlib | FREE |
| JSONL parsing | Python stdlib | FREE |
| Output writing | Python stdlib | FREE |
| Everything | No AI needed | $0.00 |

## Rules
- Never read file content — only JSONL metadata and tool names
- Never log API keys or credential values
- Keep entries concise — max 100 chars per entry
- Rotate log to MAX_ENTRIES to prevent unbounded growth
- Handle file permission errors gracefully — never crash
