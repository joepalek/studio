import json, sys

def show_pending(path, project):
    try:
        d = json.load(open(path, encoding='utf-8', errors='replace'))
    except Exception as e:
        print(f"{project}: ERROR {e}")
        return
    items = d.get('decisions', []) + d.get('proactive_questions', [])
    pending = [i for i in items if not i.get('answer') and i.get('answer') is not False]
    print(f"\n=== {project} ({len(pending)} pending) ===")
    for i in pending:
        print(f"  [{i.get('id','')}] {i.get('question','')}")
        opts = i.get('options', [])
        if opts:
            for o in opts:
                print(f"    - {o}")
        rec = i.get('recommendation','')
        if rec:
            print(f"    REC: {rec}")

show_pending("G:/My Drive/Projects/job-match/state.json", "job-match")
show_pending("G:/My Drive/Projects/listing-optimizer/listing-optimizer-state.json", "listing-optimizer")
show_pending("G:/My Drive/Projects/CTW/state.json", "CTW")
