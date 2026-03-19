# SETUP SYNC AGENT — CROSS-MACHINE ENVIRONMENT SYNC

## Role
You are the Setup Sync Agent. You capture the full development
environment of one machine into a manifest file on Google Drive,
then replicate that environment on any other machine that runs you.

Run on Machine A to capture. Run on Machine B to sync.
Zero Claude quota — pure bash/python install commands.

## When to Run
- After installing any new global tool or MCP server
- When setting up a new machine
- Weekly to catch environment drift between machines
- On demand: "Sync this machine to studio manifest"

## PART 1 — CAPTURE (run on primary machine first)

```bash
python -c "
import subprocess, json, os, sys
from datetime import datetime

manifest = {
    'captured': datetime.now().isoformat(),
    'machine': os.environ.get('COMPUTERNAME', 'unknown'),
    'tools': {},
    'npm_globals': [],
    'python_packages': [],
    'mcp_servers': {},
    'vscode_extensions': [],
    'claude_plugins': [],
    'notes': []
}

def run(cmd):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, shell=True, timeout=10)
        return r.stdout.strip()
    except: return ''

# Tool versions
manifest['tools'] = {
    'git': run('git --version'),
    'node': run('node --version'),
    'npm': run('npm --version'),
    'python': run('python --version'),
    'claude_code': run('claude --version'),
    'repomix': run('repomix --version'),
    'gh': run('& \"C:/Program Files/GitHub CLI/gh.exe\" --version'),
}

# npm global packages
npm_list = run('npm list -g --depth=0 --json')
try:
    npm_data = json.loads(npm_list)
    deps = npm_data.get('dependencies', {})
    manifest['npm_globals'] = [
        {'name': k, 'version': v.get('version', '?')}
        for k,v in deps.items()
    ]
except: pass

# Python packages relevant to studio
relevant_pkgs = ['requests', 'playwright', 'supabase', 'anthropic', 'google-generativeai']
pip_list = run('pip list --format=json')
try:
    all_pkgs = json.loads(pip_list)
    manifest['python_packages'] = [
        p for p in all_pkgs
        if any(r in p['name'].lower() for r in relevant_pkgs)
    ]
except: pass

# MCP servers from ~/.claude.json
claude_json = os.path.expanduser('~/.claude.json')
if os.path.exists(claude_json):
    try:
        data = json.load(open(claude_json))
        # Extract MCP servers
        for key in ['mcpServers', 'mcp_servers']:
            if key in data:
                manifest['mcp_servers'] = data[key]
                break
        # Also check projects
        projects = data.get('projects', {})
        for proj_path, proj_data in projects.items():
            if 'mcpServers' in proj_data:
                manifest['mcp_servers'].update(proj_data['mcpServers'])
    except Exception as e:
        manifest['notes'].append(f'claude.json parse error: {e}')

# Claude Code plugins
plugins_out = run('claude plugins list')
manifest['claude_plugins'] = [
    line.strip() for line in plugins_out.split(chr(10))
    if line.strip() and not line.startswith('Installed')
]

# VS Code extensions
ext_out = run('code --list-extensions')
manifest['vscode_extensions'] = [
    e.strip() for e in ext_out.split(chr(10)) if e.strip()
]

# ebay-mcp env (keys masked)
ebay_env = os.path.join(
    os.environ.get('APPDATA',''),
    'npm', 'node_modules', 'ebay-mcp', '.env'
)
if os.path.exists(ebay_env):
    manifest['notes'].append('ebay-mcp .env present — copy manually to new machine')
    manifest['ebay_mcp_env_path'] = ebay_env

output_path = 'G:/My Drive/Projects/_studio/setup-manifest.json'
json.dump(manifest, open(output_path, 'w'), indent=2)
print(f'Manifest captured — {len(manifest[\"npm_globals\"])} npm packages, {len(manifest[\"mcp_servers\"])} MCP servers')
print(f'Saved to: {output_path}')
"
```

## PART 2 — SYNC (run on any other machine)

```bash
python -c "
import subprocess, json, os, sys
from datetime import datetime

manifest_path = 'G:/My Drive/Projects/_studio/setup-manifest.json'
if not os.path.exists(manifest_path):
    print('ERROR: setup-manifest.json not found in _studio')
    print('Run PART 1 on your primary machine first')
    sys.exit(1)

manifest = json.load(open(manifest_path))
print(f'Manifest from: {manifest[\"machine\"]} ({manifest[\"captured\"][:10]})')
print()

def run(cmd, capture=True):
    try:
        r = subprocess.run(cmd, capture_output=capture, text=True, shell=True, timeout=60)
        return r.stdout.strip(), r.returncode
    except Exception as e:
        return str(e), 1

issues = []
installed = []
skipped = []

# Check and install npm globals
print('=== NPM GLOBALS ===')
npm_current_out, _ = run('npm list -g --depth=0 --json')
try:
    npm_current = json.loads(npm_current_out).get('dependencies', {})
except:
    npm_current = {}

for pkg in manifest.get('npm_globals', []):
    name = pkg['name']
    if name in npm_current:
        print(f'  ✓ {name}')
        skipped.append(name)
    else:
        print(f'  ↓ Installing {name}...')
        out, code = run(f'npm install -g {name}')
        if code == 0:
            print(f'    ✓ Installed')
            installed.append(name)
        else:
            print(f'    ✗ Failed: {out[:60]}')
            issues.append(f'npm install failed: {name}')

# Check Claude Code version
print()
print('=== CLAUDE CODE ===')
current_claude, _ = run('claude --version')
target_claude = manifest['tools'].get('claude_code', '')
if current_claude == target_claude:
    print(f'  ✓ {current_claude}')
else:
    print(f'  ~ Version mismatch: have {current_claude}, manifest has {target_claude}')
    print(f'    Run: npm install -g @anthropic-ai/claude-code')

# Check and install Claude plugins
print()
print('=== CLAUDE PLUGINS ===')
current_plugins_out, _ = run('claude plugins list')
current_plugins = current_plugins_out.lower()

for plugin in manifest.get('claude_plugins', []):
    plugin_clean = plugin.strip('❯ ').strip()
    if not plugin_clean or len(plugin_clean) < 3:
        continue
    if plugin_clean.lower() in current_plugins:
        print(f'  ✓ {plugin_clean}')
    else:
        print(f'  ~ Missing plugin: {plugin_clean}')
        issues.append(f'Missing Claude plugin: {plugin_clean}')

# Register MCP servers
print()
print('=== MCP SERVERS ===')
current_claude_json = os.path.expanduser('~/.claude.json')
current_mcp = {}
if os.path.exists(current_claude_json):
    try:
        data = json.load(open(current_claude_json))
        current_mcp = data.get('mcpServers', {})
    except: pass

for server_name, server_config in manifest.get('mcp_servers', {}).items():
    if server_name in current_mcp:
        print(f'  ✓ {server_name}')
    else:
        print(f'  ~ Missing MCP: {server_name} — registering...')
        cmd_parts = server_config.get('command', '')
        args = ' '.join(server_config.get('args', []))
        out, code = run(f'claude mcp add -s user {server_name} {cmd_parts} {args}')
        if code == 0:
            print(f'    ✓ Registered')
            installed.append(f'mcp:{server_name}')
        else:
            print(f'    ~ Manual registration may be needed')
            issues.append(f'MCP registration needed: {server_name}')

# Check VS Code extensions
print()
print('=== VS CODE EXTENSIONS ===')
current_ext_out, _ = run('code --list-extensions')
current_ext = current_ext_out.lower()

for ext in manifest.get('vscode_extensions', []):
    if ext.lower() in current_ext:
        print(f'  ✓ {ext}')
    else:
        print(f'  ↓ Installing {ext}...')
        out, code = run(f'code --install-extension {ext}')
        if code == 0:
            installed.append(f'vscode:{ext}')
        else:
            issues.append(f'VS Code extension failed: {ext}')

# Summary
print()
print('=== SYNC SUMMARY ===')
print(f'  Installed: {len(installed)} items')
print(f'  Skipped (already present): {len(skipped)} items')
if issues:
    print(f'  Issues requiring manual attention:')
    for issue in issues:
        print(f'    ! {issue}')
else:
    print(f'  No issues — machine synced successfully')

print()
print('MANUAL STEPS REQUIRED:')
print('  1. Copy ebay-mcp .env from primary machine:')
print('     From: C:/Users/jpalek/AppData/Roaming/npm/node_modules/ebay-mcp/.env')
print('     To:   [new machine same path]')
print('  2. Copy studio-config.json API keys are already on Drive — verify they loaded')
print('  3. Start Ollama app on new machine if local AI needed')
print('  4. Restart VS Code to load new extensions and MCP servers')
"
```

## PART 3 — DRIFT CHECK (weekly, compare both machines)

```bash
python -c "
import json, os, subprocess
from datetime import datetime

manifest_path = 'G:/My Drive/Projects/_studio/setup-manifest.json'
manifest = json.load(open(manifest_path))

def run(cmd):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, shell=True, timeout=10)
        return r.stdout.strip()
    except: return ''

current_machine = os.environ.get('COMPUTERNAME', 'unknown')
manifest_machine = manifest.get('machine', 'unknown')

print(f'Manifest machine: {manifest_machine}')
print(f'Current machine:  {current_machine}')
print()

# Check key tools
diffs = []
for tool, expected in manifest['tools'].items():
    if not expected: continue
    if tool == 'git':
        current = run('git --version')
    elif tool == 'node':
        current = run('node --version')
    elif tool == 'npm':
        current = run('npm --version')
    elif tool == 'python':
        current = run('python --version')
    elif tool == 'claude_code':
        current = run('claude --version')
    else:
        continue

    if current != expected:
        diffs.append(f'  {tool}: manifest={expected} | current={current}')

if diffs:
    print('DRIFT DETECTED:')
    for d in diffs:
        print(d)
    print()
    print('Run PART 2 to sync, or update manifest with PART 1 if current machine is now primary')
else:
    print('NO DRIFT — machines are in sync')
"
```

## Key Files That Sync Via Google Drive (automatic)
These never need manual sync — Drive handles them:
- All `.md` agent files in `_studio`
- All `state.json` project files
- `studio-config.json` (API keys)
- `studio.html` dashboard
- All `CHANGELOG.md` files
- `setup-manifest.json` (this manifest)

## Files That Need Manual Copy
These are machine-local and don't sync via Drive:
- `C:\Users\[user]\AppData\Roaming\npm\node_modules\ebay-mcp\.env` (eBay credentials)
- `~/.claude.json` (MCP registrations — agent handles this)
- Ollama models (re-pull on new machine: `ollama pull gemma3:4b`)

## Running the Sync Agent

**On primary machine (capture current state):**
```
Load setup-sync.md. Run PART 1 — capture this machine's environment to manifest.
```

**On secondary machine (sync to match):**
```
Load setup-sync.md. Run PART 2 — sync this machine to match the studio manifest.
```

**Weekly drift check:**
```
Load setup-sync.md. Run PART 3 — check for environment drift.
```

## Gateway Routing
| Task | Route | Cost |
|---|---|---|
| Capture manifest | Python/bash | FREE |
| Install npm packages | npm | FREE |
| Register MCP servers | claude mcp add | FREE |
| Install VS Code extensions | code CLI | FREE |
| Everything | No LLM needed | $0.00 |
