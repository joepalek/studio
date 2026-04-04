
MAX_CONSECUTIVE_FAILURES = 3  # Bezos Rule
"""
rebuild_sidebar.py
Single source of truth for sidebar-agent.html structure.
Strips ALL generated blocks and rebuilds cleanly from scratch each run.
Called by inject_sidebar_data.py (Task Scheduler nightly).
"""
import sys, re, json
from datetime import datetime, timezone
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

STUDIO = 'G:/My Drive/Projects/_studio'
path   = STUDIO + '/sidebar-agent.html'

# ── 1. Load raw source ─────────────────────────────────────────────────────
src = open(path, encoding='utf-8', errors='replace').read()

# ── 2. Strip everything between <body> and the first permanent landmark ────
# Permanent landmark = <!-- TAB BAR: (never changes, always present)
TABBAR_MARKER = '<!-- TAB BAR: INBOX ONLY -->'
body_pos   = src.find('<body>')
tabbar_pos = src.find(TABBAR_MARKER)

if body_pos < 0 or tabbar_pos < 0:
    print('ERROR: Could not find <body> or TAB BAR marker')
    sys.exit(1)

# Everything from <body>\n to the TAB BAR marker gets replaced with our blocks
before_body = src[:body_pos]         # head + doctype
after_tabbar = src[tabbar_pos:]      # TAB BAR onwards (panels, JS, </html>)

# ── 3. Build fresh data ────────────────────────────────────────────────────
def load_json(f, default):
    try: return json.load(open(STUDIO+'/'+f, encoding='utf-8'))
    except: return default

def sanitize(obj):
    if isinstance(obj, dict): return {k: sanitize(v) for k, v in obj.items()}
    elif isinstance(obj, list): return [sanitize(i) for i in obj]
    elif isinstance(obj, str):
        s = obj.replace('</script>','<\\/script>').replace('`',"'")
        for a,b in [('\u2018',"'"),('\u2019',"'"),('\u201c','"'),('\u201d','"'),('\u2013','-'),('\u2014','-')]:
            s = s.replace(a,b)
        return re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]','',s)
    return obj

sup   = load_json('supervisor-inbox.json', {'items':[]})
mob   = load_json('mobile-inbox.json', [])
wb    = load_json('whiteboard.json', {'items':[]})
al    = load_json('asset-log.json', {'assets':[]})
svc   = load_json('ai-services-rankings.json', {'categories':{}})
reg   = load_json('model-registry.json', {})
try:
    intel = open(STUDIO+'/ai-intel-summary.txt', encoding='utf-8', errors='replace').read()[:800]
except: intel = ''

try:
    briefing = open(STUDIO+'/STUDIO_BRIEFING.md', encoding='utf-8', errors='replace').read()[:3000]
except: briefing = ''

digest_data = load_json('daily-digest.json', {})
digests     = digest_data.get('digests', [])
last_digest = digests[-1] if digests else None

rq_data    = load_json('data/review-queue.json', {'entries': []})
rq_entries = rq_data.get('entries', [])

RESOLVED = ('resolved','RESOLVED','auto-resolved','build','done','DONE','answered','ANSWERED')

# Load answered IDs from inbox-log.jsonl — written by bridge on every Submit
answered_ids = set()
try:
    with open(STUDIO + '/inbox-log.jsonl', encoding='utf-8') as _f:
        for _line in _f:
            _line = _line.strip()
            if _line:
                _entry = json.loads(_line)
                if _entry.get('id'):
                    answered_ids.add(_entry['id'])
except Exception:
    pass

sup_items = sup.get('items', sup) if isinstance(sup, dict) else sup
mob_items = mob if isinstance(mob, list) else mob.get('items', [])

inbox = []
for i in sup_items:
    if isinstance(i,dict) and i.get('status') not in RESOLVED and i.get('id') not in answered_ids:
        inbox.append(sanitize({'id':i.get('id','sup-'+str(len(inbox))),'title':i.get('title','')[:80],'finding':i.get('finding','')[:120],'urgency':i.get('urgency','INFO'),'date':i.get('date',''),'source':'supervisor','project':i.get('project','studio'),'options':[],'recommendation':''}))
_consecutive_failures = 0
for i in mob_items:
    if isinstance(i,dict) and i.get('status') not in RESOLVED and i.get('id') not in answered_ids:
        title = i.get('question',i.get('title',''))
        if 'WHITEBOARD' in title or i.get('id','').startswith('wb-'): continue
        inbox.append(sanitize({'id':i.get('id','mob-'+str(len(inbox))),'title':title[:80],'finding':i.get('context',i.get('description',''))[:120],'urgency':'WARN' if i.get('priority')=='high' else 'INFO','date':i.get('created_at',i.get('date','')),'source':'mobile','project':i.get('project',''),'options':i.get('options',[])[:4],'recommendation':i.get('recommendation','')[:100]}))

wb_items  = wb.get('items',[])
wb_scored = sorted([i for i in wb_items if i.get('gemini_score')], key=lambda x: x.get('gemini_score',{}).get('total_score',0), reverse=True)
wb_top    = [sanitize({'title':i.get('title','')[:60],'description':(i.get('description','') or '')[:60],'score':i.get('gemini_score',{}).get('total_score',0),'action':i.get('gemini_score',{}).get('recommended_action','')}) for i in wb_scored[:10]]

# Build compact model registry summary for sidebar
registry_summary = {}
for prov_key, prov in reg.get('providers', {}).items():
    models_active = [
        {'id': mk, 'display': mv.get('display', mk),
         'tier': mv.get('tier','?'), 'free_limits': mv.get('free_limits',''),
         'studio_use': mv.get('studio_use','')[:60],
         'status': mv.get('status','active')}
        for mk, mv in prov.get('models', {}).items()
        if 'active' in mv.get('status','active')
    ]
    if models_active:
        registry_summary[prov_key] = {
            'name': prov.get('name', prov_key),
            'url': prov.get('url',''),
            'studio_connected': prov.get('studio_connected', False),
            'free_tier': prov.get('free_tier', False),
            'models': models_active
        }

now_iso     = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
today       = datetime.now().strftime('%Y-%m-%d')
intel_clean = intel.encode('ascii','replace').decode('ascii').replace('\\','\\\\').replace('`',"'")
briefing_clean = briefing.encode('ascii','replace').decode('ascii').replace('\\','\\\\').replace('`',"'").replace('</script>','<\\/script>')
data = json.dumps({
    'generated': now_iso, 'inbox': inbox, 'whiteboard': wb_top,
    'assets': sanitize(al.get('assets',[])),
    'services': sanitize(svc.get('categories',{})),    'servicesDate': svc.get('date', today),
    'intelSummary': intel_clean,
    'studioBriefing': briefing_clean,
    'lastDigest': sanitize(last_digest) if last_digest else None,
    'modelRegistry': sanitize(registry_summary),
    'modelRegistryDate': reg.get('last_updated', today),
    'reviewQueue': sanitize(rq_entries),
}, ensure_ascii=True)

# ── 4. Build the injected blocks ──────────────────────────────────────────
BOOT_ANIM_DATA = (
'<body>\n'
'<!-- Boot screen: pure HTML, renders before any script -->\n'
'<div id="boot-screen" style="position:fixed;inset:0;background:#0d1117;'
'display:flex;flex-direction:column;align-items:center;justify-content:center;'
'z-index:9999;font-family:\'Segoe UI\',Arial,sans-serif;">\n'
'  <div style="font-size:11px;letter-spacing:3px;color:#3fb950;text-transform:uppercase;margin-bottom:16px;">Studio Sidebar</div>\n'
'  <div style="width:120px;height:2px;background:#21262d;border-radius:2px;overflow:hidden;">\n'
'    <div id="boot-bar" style="height:100%;width:10%;background:#3fb950;border-radius:2px;transition:width 0.5s;"></div>\n'
'  </div>\n'
'  <div id="boot-msg" style="font-size:10px;color:#6e7681;margin-top:12px;">Loading...</div>\n'
'</div>\n'
'<script>\n'
'(function(){var p=10,m=["Parsing...","Initializing...","Almost ready..."];\n'
'var iv=setInterval(function(){p=Math.min(p+(p<50?8:p<80?3:1),90);\n'
'var b=document.getElementById("boot-bar"),t=document.getElementById("boot-msg");\n'
'if(b)b.style.width=p+"%";if(t)t.textContent=p<40?m[0]:p<70?m[1]:m[2];\n'
'if(p>=90)clearInterval(iv);},150);})();\n'
'</script>\n'
'<script>\n'
'// INJECTED STUDIO DATA - generated: ' + now_iso + '\n'
'const INJECTED = ' + data + ';\n'
'// END INJECTED DATA\n'
'</script>\n'
)

# ── 5. Assemble and write ──────────────────────────────────────────────────
result = before_body + BOOT_ANIM_DATA + after_tabbar

# Verify
lines    = result.split('\n')
boot_l   = result[:result.find('boot-screen')].count('\n') + 1
anim_l   = result[:result.find('Boot animation')].count('\n') + 1 if 'Boot animation' in result else 0
inj_l    = result[:result.find('const INJECTED')].count('\n') + 1
onl_l    = result[:result.find('window.onload')].count('\n') + 1
tabbar_l = result[:result.find(TABBAR_MARKER)].count('\n') + 1

import re as _re
assert len(_re.findall(r'id="boot-screen"', result)) == 1, 'DUPLICATE boot-screen div!'
assert result.count('const INJECTED') == 1, 'DUPLICATE INJECTED!'
assert boot_l < inj_l < tabbar_l < onl_l, 'ORDER WRONG: ' + str((boot_l, inj_l, tabbar_l, onl_l))

open(path, 'w', encoding='utf-8').write(result)

print('OK  inbox=' + str(len(inbox)) + ' wb=' + str(len(wb_top)) + ' size=' + str(len(result)))
print('    boot=' + str(boot_l) + ' injected=' + str(inj_l) + ' tabbar=' + str(tabbar_l) + ' onload=' + str(onl_l))
