@echo off
cd /d "G:\My Drive\Projects\_studio"
python -c "
import json, sys
sys.path.insert(0, 'G:/My Drive/Projects/_studio')
# Load and run seo-agent via supervisor dispatch pattern
# Supervisor reads seo-agent.md and dispatches via ai_gateway
with open('seo-agent.md', encoding='utf-8') as f:
    spec = f.read()
from ai_gateway import call
result = call(spec, task_type='general', max_tokens=1000)
# Write output to seo-recommendations.json
import datetime
recs = json.load(open('seo-recommendations.json', encoding='utf-8'))
recs['_updated'] = datetime.datetime.utcnow().isoformat()
recs['_last_run_output'] = result.text[:2000]
json.dump(recs, open('seo-recommendations.json', 'w'), indent=2)
print('[seo-agent] Run complete.')
" >> logs\seo-agent.log 2>&1
