"""Fix heartbeat log and repopulate with agent runs"""
import json, sys
from datetime import datetime
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

STUDIO = 'G:/My Drive/Projects/_studio'

# Read current heartbeat log
try:
    current = json.load(open(STUDIO + '/heartbeat-log.json', encoding='utf-8'))
    existing = current.get('entries', [])
    print(f'Existing entries: {len(existing)}')
except Exception as e:
    existing = []
    print(f'Could not read existing: {e}')

# Create backup
with open(STUDIO + '/heartbeat-log-backup.json', 'w', encoding='utf-8') as f:
    json.dump({'entries': existing, 'backed_up_at': datetime.now().isoformat()}, f, indent=2)
print('Backup saved')

# Keep the structure but we need to repopulate
# The file already exists, just verify it's valid JSON
print(f'Heartbeat log has {len(existing)} entries - will repopulate by running agents')
