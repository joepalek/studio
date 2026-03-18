#!/usr/bin/env python3
"""
Session Activity Bridge
Watches Claude Code JSONL transcripts -> writes to studio session-activity.json
Run in background: python session-bridge.py
"""

import os, json, time, glob
from datetime import datetime
from pathlib import Path

CLAUDE_PROJECTS_DIR = os.path.expanduser(r'~\.claude\projects')
STUDIO_OUTPUT = r'G:\My Drive\Projects\_studio\session-activity.json'
POLL_INTERVAL = 5
MAX_ENTRIES = 100

seen_positions = {}
activity_log = []

def load_existing():
    global activity_log
    try:
        if os.path.exists(STUDIO_OUTPUT):
            data = json.load(open(STUDIO_OUTPUT))
            activity_log = data.get('entries', [])[-MAX_ENTRIES:]
    except:
        activity_log = []

def parse_jsonl_entry(line):
    try:
        entry = json.loads(line.strip())
    except:
        return None

    msg_type = entry.get('type', '')
    content = entry.get('message', {})

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
                        return {'type': 'write', 'text': f'Wrote {os.path.basename(path)}', 'icon': '✎'}
                    elif tool == 'str_replace_editor':
                        path = inp.get('path', '')
                        cmd = inp.get('command', 'edit')
                        return {'type': 'edit', 'text': f'{cmd} {os.path.basename(path)}', 'icon': '✎'}
                    elif tool == 'read_file':
                        return {'type': 'read', 'text': f'Read {os.path.basename(inp.get("path",""))}', 'icon': '◎'}

        text_parts = [p.get('text','') for p in parts if isinstance(p,dict) and p.get('type')=='text']
        full_text = ' '.join(text_parts).strip()
        if full_text and len(full_text) > 20:
            first_line = full_text.split('\n')[0][:100]
            if any(kw in first_line.lower() for kw in ['complete','done','fixed','created','found','error','success','fail','running','built','committed','pushed']):
                return {'type': 'agent', 'text': first_line, 'icon': '●'}

    return None

def extract_project(filepath):
    parts = Path(filepath).parts
    known = ['_studio','CTW','job-match','nutrimind','acuscan-ar','squeeze-empire',
             'sentinel-core','sentinel-performer','sentinel-viewer','arbitrage-pulse',
             'hibid-analyzer','listing-optimizer','whatnot-apps']
    for part in reversed(parts):
        for k in known:
            if k.lower() in part.lower():
                return k
    return '_studio'

def scan():
    global activity_log
    if not os.path.exists(CLAUDE_PROJECTS_DIR):
        return 0
    new_entries = 0
    files = sorted(glob.glob(os.path.join(CLAUDE_PROJECTS_DIR,'**','*.jsonl'),recursive=True),
                   key=lambda f: os.path.getmtime(f), reverse=True)
    cutoff = time.time() - 7200
    for filepath in [f for f in files if os.path.getmtime(f) > cutoff][:5]:
        last_pos = seen_positions.get(filepath, 0)
        try:
            with open(filepath,'r',encoding='utf-8',errors='ignore') as f:
                f.seek(last_pos)
                lines = f.readlines()
                seen_positions[filepath] = f.tell()
        except:
            continue
        for line in lines:
            if not line.strip(): continue
            parsed = parse_jsonl_entry(line)
            if parsed:
                parsed['time'] = datetime.now().strftime('%H:%M:%S')
                parsed['project'] = extract_project(filepath)
                activity_log.append(parsed)
                new_entries += 1
    if len(activity_log) > MAX_ENTRIES:
        activity_log = activity_log[-MAX_ENTRIES:]
    return new_entries

def write_output():
    try:
        with open(STUDIO_OUTPUT,'w',encoding='utf-8') as f:
            json.dump({'updated': datetime.now().isoformat(), 'entry_count': len(activity_log), 'entries': activity_log}, f, indent=2)
    except Exception as e:
        print(f'Write error: {e}')

def main():
    print('Session Activity Bridge started')
    print(f'Watching: {CLAUDE_PROJECTS_DIR}')
    print(f'Output:   {STUDIO_OUTPUT}')
    print('Ctrl+C to stop\n')
    load_existing()
    while True:
        try:
            new = scan()
            if new > 0:
                write_output()
                print(f'[{datetime.now().strftime("%H:%M:%S")}] +{new} entries ({len(activity_log)} total)')
            time.sleep(POLL_INTERVAL)
        except KeyboardInterrupt:
            print('\nBridge stopped.')
            break
        except Exception as e:
            print(f'Error: {e}')
            time.sleep(POLL_INTERVAL)

if __name__ == '__main__':
    main()
