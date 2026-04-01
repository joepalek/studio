import json, os
from datetime import datetime

# Read with BOM stripping
with open(os.path.join('..', 'technical-peer-guides.json'), 'rb') as f:
    guides_config = json.loads(f.read().decode('utf-8-sig'))

with open(os.path.join('..', 'adversary-test-packages.json'), 'rb') as f:
    packages_config = json.loads(f.read().decode('utf-8-sig'))

with open('ghost_outlines/linked_deep_outline.json', 'rb') as f:
    outline = json.loads(f.read().decode('utf-8-sig'))

def log_msg(msg):
    ts = datetime.now().isoformat()
    print(f'[{ts}] {msg}')

log_msg('=== TECHNICAL PEER REVIEW: LINKED OUTLINE ===')
log_msg(f'Item: {outline.get("book", "Unknown")}')

if 'packages' in packages_config and 'complete_technical_stress_test' in packages_config['packages']:
    guides_to_run = packages_config['packages']['complete_technical_stress_test'].get('guides', [])
    log_msg(f'Running {len(guides_to_run)} technical guides...')
    for guide_name in guides_to_run:
        if guide_name in guides_config['guides']:
            guide = guides_config['guides'][guide_name]
            log_msg(f'  ✓ {guide["name"]}')
    log_msg(f'Setup complete. Ready for Claude evaluation.')
else:
    log_msg('ERROR: Package configuration missing')
