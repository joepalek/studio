import sys, json, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

STUDIO = 'G:/My Drive/Projects/_studio'

# Check whiteboard.json items count and score range
wb = json.load(open(STUDIO + '/whiteboard.json', encoding='utf-8'))
items = wb.get('items', [])
scored = [i for i in items if i.get('gemini_score')]
print('Whiteboard: ' + str(len(items)) + ' total, ' + str(len(scored)) + ' scored')

# Check agency directory
agency_dir = STUDIO + '/agency'
if os.path.exists(agency_dir):
    files = os.listdir(agency_dir)
    chars = [f for f in files if f.endswith('.json') and 'character' in f.lower()]
    scripts = [f for f in files if f.endswith('.py')]
    print('Agency: ' + str(len(files)) + ' files, ' + str(len(chars)) + ' char JSONs, ' + str(len(scripts)) + ' scripts')

# Check ai-intel-daily.json
intel = json.load(open(STUDIO + '/ai-intel-daily.json', encoding='utf-8'))
print('AI Intel: generated=' + str(intel.get('generated','?'))[:20])
high = intel.get('high_priority', intel.get('findings', []))
print('  High priority items: ' + str(len(high) if isinstance(high, list) else '?'))

# Check product-archaeology-results.json
pa = json.load(open(STUDIO + '/product-archaeology-results.json', encoding='utf-8'))
pa_items = pa if isinstance(pa, list) else pa.get('results', pa.get('items', []))
print('Product Archaeology: ' + str(len(pa_items)) + ' results')

# Check vintage directory
vint_dir = STUDIO + '/vintage'
if os.path.exists(vint_dir):
    vfiles = [f for f in os.listdir(vint_dir) if f.endswith('.json')]
    print('Vintage: ' + str(len(vfiles)) + ' decade files')

# Check task-queue.json
tq = json.load(open(STUDIO + '/task-queue.json', encoding='utf-8'))
tq_list = tq if isinstance(tq, list) else tq.get('tasks', [])
queued = [t for t in tq_list if t.get('status') == 'queued']
print('Task queue: ' + str(len(queued)) + ' queued')

# Check orchestrator-plan.json
op = json.load(open(STUDIO + '/orchestrator-plan.json', encoding='utf-8'))
ar = op.get('agent_runnable', [])
print('Orchestrator plan - agent_runnable: ' + str(len(ar)) + ' tasks')
for t in ar[:3]: print('  - ' + str(t.get('project','?')) + ': ' + str(t.get('action','?'))[:60])
