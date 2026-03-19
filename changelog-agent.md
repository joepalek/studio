# CHANGELOG AGENT — STATE DIFFS → CHANGELOG.MD

## Role
You are the Changelog Agent. You compare current state.json files
against the previous git commit's state.json, extract meaningful
changes, and write a human-readable CHANGELOG.md per project.

Zero LLM needed for most projects. Pure Python diff logic.
Gemini Flash only for summarizing complex multi-file changes.

## When to Run
- After git-commit-agent completes
- Weekly (Sunday nights with Market Scout)
- When a project reaches a milestone (progress crosses 25/50/75/100%)

## Execution

### Pass 1 — Diff state.json vs last commit
```bash
python -c "
import json, os, subprocess
from datetime import datetime

projects_root = 'G:/My Drive/Projects'
projects = [
    'acuscan-ar', 'arbitrage-pulse', 'CTW', 'hibid-analyzer',
    'job-match', 'listing-optimizer', 'nutrimind', 'sentinel-core',
    'sentinel-performer', 'sentinel-viewer', 'squeeze-empire',
    'whatnot-apps', '_studio'
]

changes = {}

for p in projects:
    path = os.path.join(projects_root, p).replace('/', chr(92))
    state_file = None
    for fname in [f'{p}-state.json', 'state.json']:
        sf = os.path.join(projects_root, p, fname)
        if os.path.exists(sf):
            state_file = fname
            break

    if not state_file:
        continue

    try:
        # Get current state
        current = json.load(open(os.path.join(projects_root, p, state_file)))

        # Get previous state from git
        result = subprocess.run(
            ['git', '-C', path, 'show', f'HEAD:{state_file}'],
            capture_output=True, text=True, timeout=5
        )

        if result.returncode != 0:
            changes[p] = {'type': 'new', 'current': current}
            continue

        previous = json.loads(result.stdout)

        # Compare key fields
        diff = {}
        for field in ['status', 'progress', 'nextAction', 'lastUpdated']:
            prev_val = previous.get(field)
            curr_val = current.get(field)
            if prev_val != curr_val:
                diff[field] = {'from': prev_val, 'to': curr_val}

        # Compare decisions count
        prev_decisions = len(previous.get('decisions', []))
        curr_decisions = len(current.get('decisions', []))
        if prev_decisions != curr_decisions:
            diff['decisions'] = {'from': prev_decisions, 'to': curr_decisions}

        if diff:
            changes[p] = {'type': 'changed', 'diff': diff}
            print(f'{p}: {len(diff)} changes')
        else:
            print(f'{p}: no changes')

    except Exception as e:
        print(f'{p}: ERROR — {e}')

json.dump(changes, open('G:/My Drive/Projects/_studio/changelog-diffs.json', 'w'), indent=2)
print(f'Found changes in {len(changes)} projects')
"
```

### Pass 2 — Write CHANGELOG.md per project
```bash
python -c "
import json, os
from datetime import datetime

changes = json.load(open('G:/My Drive/Projects/_studio/changelog-diffs.json'))
today = datetime.now().strftime('%Y-%m-%d')

for project, change_data in changes.items():
    project_path = f'G:/My Drive/Projects/{project}'
    changelog_path = os.path.join(project_path, 'CHANGELOG.md')

    # Build new entry
    lines = [f'## [{today}]\n']

    if change_data['type'] == 'new':
        lines.append('### Added\n')
        lines.append(f'- Project initialized\n')
        state = change_data.get('current', {})
        if state.get('status'):
            lines.append(f'- Status: {state[\"status\"]}\n')
        if state.get('nextAction'):
            lines.append(f'- Next action: {state[\"nextAction\"][:80]}\n')
    else:
        diff = change_data.get('diff', {})

        if 'progress' in diff:
            p_from = diff['progress']['from']
            p_to = diff['progress']['to']
            direction = 'increased' if (p_to or 0) > (p_from or 0) else 'decreased'
            lines.append(f'### Changed\n')
            lines.append(f'- Progress {direction}: {p_from}% → {p_to}%\n')

        if 'status' in diff:
            lines.append(f'- Status changed: {diff[\"status\"][\"from\"]} → {diff[\"status\"][\"to\"]}\n')

        if 'nextAction' in diff:
            lines.append(f'- Next action updated: {diff[\"nextAction\"][\"to\"][:80]}\n')

        if 'decisions' in diff:
            d = diff['decisions']
            if (d['to'] or 0) < (d['from'] or 0):
                lines.append(f'- Decisions resolved: {d[\"from\"]} → {d[\"to\"]}\n')
            else:
                lines.append(f'- New decisions added: {d[\"from\"]} → {d[\"to\"]}\n')

    new_entry = ''.join(lines) + '\n'

    # Prepend to existing changelog or create new
    if os.path.exists(changelog_path):
        existing = open(changelog_path).read()
        # Insert after the header
        if '# Changelog' in existing:
            content = existing.replace('# Changelog\n', f'# Changelog\n\n{new_entry}', 1)
        else:
            content = f'# Changelog\n\n{new_entry}{existing}'
    else:
        content = f'# Changelog\n\n{new_entry}'

    with open(changelog_path, 'w') as f:
        f.write(content)
    print(f'Updated CHANGELOG.md: {project}')
"
```

### Pass 3 — Master changelog for _studio
```bash
python -c "
import json, os
from datetime import datetime

changes = json.load(open('G:/My Drive/Projects/_studio/changelog-diffs.json'))
today = datetime.now().strftime('%Y-%m-%d')

master_lines = [f'# Studio Master Changelog\n\n## {today}\n\n']

for project, change_data in changes.items():
    if change_data['type'] == 'new':
        master_lines.append(f'- **{project}**: initialized\n')
    else:
        diff = change_data.get('diff', {})
        notes = []
        if 'progress' in diff:
            notes.append(f'progress {diff[\"progress\"][\"from\"]}% → {diff[\"progress\"][\"to\"]}%')
        if 'status' in diff:
            notes.append(f'status → {diff[\"status\"][\"to\"]}')
        if 'nextAction' in diff:
            notes.append(f'next: {diff[\"nextAction\"][\"to\"][:60]}')
        if notes:
            master_lines.append(f'- **{project}**: {\" | \".join(notes)}\n')

master_path = 'G:/My Drive/Projects/_studio/MASTER-CHANGELOG.md'

if os.path.exists(master_path):
    existing = open(master_path).read()
    content = ''.join(master_lines) + '\n---\n\n' + existing
else:
    content = ''.join(master_lines)

with open(master_path, 'w') as f:
    f.write(content)

print(f'Master changelog updated — {len(changes)} projects')
"
```

## Gateway Routing
| Task | Route | Cost |
|---|---|---|
| Git diff state files | Python + git | FREE |
| Write CHANGELOG.md | Python | FREE |
| Complex change summary | Gemini Flash | FREE |
| Everything | No Claude needed | $0.00 |

## Running the Changelog Agent
```
Load changelog-agent.md. Run changelog update for all projects.
```

## Add to Session End
Add to root CLAUDE.md SESSION END PROTOCOL:
```
5. Load changelog-agent.md. Update changelogs for all changed projects.
```
