import sys, json, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
STUDIO = 'G:/My Drive/Projects/_studio'

def load(f, d=None):
    try: return json.load(open(STUDIO+'/'+f, encoding='utf-8', errors='replace'))
    except: return d

# 1. NightlyRollup — digest
dd = load('daily-digest.json', {})
digests = dd.get('digests', [])
last = digests[-1] if digests else {}
print('NIGHTLY ROLLUP:')
print('  Digest entries: ' + str(len(digests)))
print('  Latest: ' + last.get('date','?') + ' — ' + last.get('health_status','?') + ' ' + str(last.get('health_score','?')) + '/100')
print('  Agents checked in: ' + str(last.get('agent_checkins',{}).get('checked_in',[])))
print('  Missed: ' + str(last.get('agent_checkins',{}).get('missed',[])))

# 2. AutoAnswer — inbox state
mob = load('mobile-inbox.json', [])
mob_list = mob if isinstance(mob, list) else mob.get('items', [])
pending  = [i for i in mob_list if i.get('status') not in ('answered','resolved','RESOLVED','auto-resolved','done')]
answered = [i for i in mob_list if i.get('status') == 'answered']
print()
print('INBOX (mobile-inbox.json):')
print('  Total: ' + str(len(mob_list)) + ' | Pending: ' + str(len(pending)) + ' | Answered: ' + str(len(answered)))

# 3. WhiteboardScore
wb = load('whiteboard.json', {})
items = wb.get('items', [])
scored = [i for i in items if i.get('gemini_score')]
top3 = sorted(scored, key=lambda x: x.get('gemini_score',{}).get('total_score',0), reverse=True)[:3]
print()
print('WHITEBOARD:')
print('  Total: ' + str(len(items)) + ' | Scored: ' + str(len(scored)))
for i in top3:
    sc = i.get('gemini_score',{})
    print('  #' + str(sc.get('total_score','?')) + ' ' + i.get('title','')[:50] + ' — ' + sc.get('recommended_action','?'))

# 4. ProductArchaeology
pa = load('product-archaeology-results.json', {})
pa_items = pa.get('results', []) if isinstance(pa, dict) else pa
print()
print('PRODUCT ARCHAEOLOGY:')
print('  Results: ' + str(pa.get('count', len(pa_items))) + ' | Updated: ' + pa.get('updated','?')[:10] if isinstance(pa, dict) else '  Results: ' + str(len(pa_items)))

# 5. VintageAgent
vint_dir = STUDIO + '/vintage'
vfiles = [f for f in os.listdir(vint_dir) if f.endswith('-profile.json')] if os.path.exists(vint_dir) else []
ebay = load('vintage/ebay-vintage-intel.json', {})
print()
print('VINTAGE AGENT:')
print('  Decade profiles: ' + str(len(vfiles)))
print('  eBay hot items: ' + str(len(ebay.get('hot',[]))) + ' | Sleepers: ' + str(len(ebay.get('sleepers',[]))) + ' | Gaps: ' + str(len(ebay.get('gaps',[]))))

# 6. Agency
agency_dir = STUDIO + '/agency'
chars = [f for f in os.listdir(agency_dir) if f.endswith('.json') and 'character' in f.lower()] if os.path.exists(agency_dir) else []
print()
print('AGENCY:')
print('  Character JSONs: ' + str(len(chars)))
for c in chars: print('  ' + c)

# 7. AIIntel
intel = load('ai-intel-daily.json', {})
hi = intel.get('high_priority', [])
print()
print('AI INTEL:')
print('  High priority: ' + str(len(hi)) + ' | Generated: ' + str(intel.get('generated','?'))[:16])
for item in hi[:3]:
    print('  * ' + str(item.get('title', item.get('headline','?')))[:60])

# 8. OrchestratorPlan
plan = load('orchestrator-plan.json', {})
ar = plan.get('agent_runnable', [])
hr = plan.get('human_required', [])
print()
print('ORCHESTRATOR PLAN:')
print('  Agent runnable: ' + str(len(ar)) + ' | Human required: ' + str(len(hr)))
for t in ar[:3]: print('  [' + t.get('priority','?') + '] ' + t.get('action','?')[:60])

# 9. SupervisorCheck
sr = load('supervisor-report.json', {})
print()
print('SUPERVISOR:')
print('  Time: ' + str(sr.get('time','?'))[:16])
print('  Ollama: ' + str(sr.get('ollama_up','?')) + ' | Gemini: ' + str(sr.get('gemini_available','?')))
print('  Work queue depth: ' + str(sr.get('work_queue_depth','?')))
print('  Dispatched: ' + str(len(sr.get('dispatched',[]))) + ' tasks')

# 10. GitCommit
gc_log = STUDIO + '/scheduler/logs/nightly-commit.log'
if os.path.exists(gc_log):
    lines = open(gc_log, encoding='utf-8', errors='replace').read().strip().split('\n')
    for l in lines[-4:]:
        if 'Committed' in l or 'committed' in l or 'Clean' in l:
            print()
            print('GIT COMMIT: ' + l.strip()[:80])
            break
