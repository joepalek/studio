import json
from datetime import datetime

NOW = datetime.now().isoformat()[:19]

lo_path = "G:/My Drive/Projects/listing-optimizer/listing-optimizer-state.json"
d = json.load(open(lo_path, encoding='utf-8', errors='replace'))

# decision_001 — personal first (already written, skip if answered)
# decision_002 — input format — leave pending
# proactive_001 — SKU conventions
# proactive_002 — categories
# proactive_003 — price suggestions (already written, skip if answered)

pq_answers = {
    "proactive_001": "Location-based codes (e.g. BOX-01, BIN-A3). Optimizer must preserve existing SKU values exactly — do not modify or reformat them.",
    "proactive_002": "PARTIAL — confirmed: vintage clothing, electronics, books/media, home decor. Full category breakdown requires pulling eBay report — categories shift over time. Build optimization rules for these four first; add more after report review.",
}

for item in d.get('proactive_questions', []):
    if item.get('id') in pq_answers and not item.get('answer'):
        item['answer'] = pq_answers[item['id']]
        item['answered_date'] = NOW
        print(f"  answered: {item['id']}")
    elif item.get('id') in pq_answers:
        print(f"  already answered: {item['id']} — skipping")

json.dump(d, open(lo_path, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
print("listing-optimizer state.json saved")
