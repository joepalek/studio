"""
workflow_hook.py -- Post-task efficiency check for all agents.

Call check_efficiency() at the end of any agent script to auto-detect
workflow improvements and push them to whiteboard.json as type:workflow.

Usage:
    import sys
    sys.path.insert(0, 'G:/My Drive/Projects/_studio/utilities')
    from workflow_hook import check_efficiency

    check_efficiency(
        agent_name='ghost-book-pass2',
        steps_taken=['load candidates', 'gemini validate', 'save results'],
        manual_interventions=0,   # number of times script needed human fix
        time_seconds=840,         # actual runtime
        errors_hit=[],            # list of error type strings encountered
    )
"""
import json, os, time
from datetime import datetime

STUDIO = 'G:/My Drive/Projects/_studio'
BOARD  = STUDIO + '/whiteboard.json'
RULES  = STUDIO + '/standing-rules.json'


def check_efficiency(
    agent_name: str,
    steps_taken: list = None,
    manual_interventions: int = 0,
    time_seconds: float = 0,
    errors_hit: list = None,
    notes: str = '',
):
    """
    Check if the completed task had avoidable friction, then push findings
    to whiteboard.json with type: workflow.

    Args:
        agent_name:            Name of the script/agent that just ran
        steps_taken:           List of step descriptions
        manual_interventions:  How many times a human had to intervene/fix
        time_seconds:          How long the task took
        errors_hit:            List of error type strings (UnicodeEncodeError, etc.)
        notes:                 Free-form observation about this run
    """
    steps_taken  = steps_taken or []
    errors_hit   = errors_hit  or []
    proposals    = []
    now_str      = datetime.now().isoformat()[:10]

    # ── Check 1: Manual interventions ────────────────────────────────────────
    if manual_interventions >= 2:
        proposals.append({
            'title': f'[WORKFLOW] {agent_name}: {manual_interventions} manual fixes needed — automate',
            'description': (f'{agent_name} required {manual_interventions} human interventions. '
                            f'Each intervention is a standing-rule candidate. '
                            f'Notes: {notes}'),
            'effort': 'low',
            'time_saved': '15-30 min/week',
        })

    # ── Check 2: Known error patterns without a utility ───────────────────────
    KNOWN_UTILITIES = {
        'UnicodeEncodeError': 'unicode_safe.py → safe_str()',
        'charmap codec':      'unicode_safe.py → safe_print()',
        'list.*attribute':    'unicode_safe.py → to_str()',
        'HTTP Error 403':     'scraper_utils.py → fetch() with retry',
        'HTTP Error 429':     'scraper_utils.py → exponential backoff',
        'JSONDecodeError':    'unicode_safe.py → safe_json_load()',
    }
    import re
    for err in errors_hit:
        for pattern, fix in KNOWN_UTILITIES.items():
            if re.search(pattern, err, re.IGNORECASE):
                util_path = os.path.join(STUDIO, 'utilities',
                                         fix.split('→')[0].strip().split('.')[-2] + '.py')
                util_exists = os.path.exists(util_path)
                if not util_exists:
                    proposals.append({
                        'title': f'[WORKFLOW] {agent_name}: build missing utility for {err}',
                        'description': f'Error "{err}" hit in {agent_name}. Fix: {fix}',
                        'effort': 'low',
                        'time_saved': '5-15 min per occurrence',
                    })
                else:
                    # Utility exists but agent isn't using it
                    proposals.append({
                        'title': f'[WORKFLOW] {agent_name}: migrate to existing {fix}',
                        'description': (f'{agent_name} hit "{err}" but utility already exists. '
                                        f'Add import from utilities/{fix.split("→")[0].strip()}'),
                        'effort': 'low',
                        'time_saved': '5 min/occurrence',
                    })
                break

    # ── Check 3: Long runtime with repetitive steps ───────────────────────────
    if time_seconds > 600 and len(steps_taken) > 0:
        # Check if any steps look parallelizable
        parallel_signals = ['load', 'fetch', 'validate', 'check', 'ping']
        parallelizable = [s for s in steps_taken
                          if any(sig in s.lower() for sig in parallel_signals)]
        if len(parallelizable) >= 3:
            proposals.append({
                'title': f'[WORKFLOW] {agent_name}: parallelize {len(parallelizable)} sequential fetch steps',
                'description': (f'{agent_name} ran {int(time_seconds/60)} min with sequential steps: '
                                 f'{", ".join(parallelizable[:3])}. '
                                 f'Batch or thread these for 2-5x speedup.'),
                'effort': 'medium',
                'time_saved': f'{int(time_seconds/60/3)}-{int(time_seconds/60/2)} min/run',
            })

    # ── Check 4: Cross-reference standing rules ───────────────────────────────
    if os.path.exists(RULES):
        rules_data = json.load(open(RULES, encoding='utf-8'))
        for rule in rules_data.get('rules', []):
            for err in errors_hit:
                if any(kw in err.lower() for kw in rule['trigger'].lower().split()[:3]):
                    # This error has a standing rule — was it followed?
                    proposals.append({
                        'title': f'[WORKFLOW] {agent_name}: standing rule {rule["id"]} may not be applied',
                        'description': (f'Error "{err}" matches standing rule {rule["id"]}: '
                                        f'"{rule["trigger"]}". Verify agent implements this rule.'),
                        'effort': 'low',
                        'time_saved': 'prevents future failures',
                    })

    # ── Push proposals to whiteboard ──────────────────────────────────────────
    if not proposals:
        return  # nothing to flag

    wb = json.load(open(BOARD, encoding='utf-8')) if os.path.exists(BOARD) else {'items': []}
    items = wb.get('items', wb.get('ideas', []))
    existing_titles = {i.get('title', '') for i in items}

    added = 0
    for prop in proposals:
        if prop['title'] in existing_titles:
            continue
        items.append({
            'id': f'wb-workflow-{agent_name}-{int(time.time())}',
            'title': prop['title'],
            'type': 'workflow',
            'source_agent': 'workflow-hook',
            'triggered_by': agent_name,
            'description': prop.get('description', ''),
            'tags': ['workflow', 'automation', 'efficiency'],
            'effort': prop.get('effort', 'low'),
            'time_saved': prop.get('time_saved', ''),
            'status': 'pending_review',
            'created': now_str,
        })
        added += 1

    if added > 0:
        wb['items'] = items
        wb['last_updated'] = datetime.now().isoformat()
        json.dump(wb, open(BOARD, 'w'), indent=2, ensure_ascii=False)
        print(f'[workflow_hook] {added} efficiency proposal(s) added to whiteboard')
