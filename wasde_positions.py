import sys, json
sys.path.insert(0, "G:/My Drive/Projects/_studio")
import wasde_parser

wasde_parser.AGENT_CONFIG["source_url"] = "https://www.usda.gov/oce/commodity/wasde/wasde0326.pdf"
raw = wasde_parser.fetch_raw(wasde_parser.AGENT_CONFIG)
bundle = json.loads(raw)
text = bundle["text"]
upper = text.upper()

# Find all occurrences of each problem commodity
for term in ["RICE:", "RICE ", "SOYBEAN"]:
    print(f"\n=== '{term}' occurrences ===")
    start = 0
    count = 0
    while count < 6:
        idx = upper.find(term, start)
        if idx == -1:
            break
        print(f"  pos {idx:6d}: ...{repr(text[max(0,idx-30):idx+60])}...")
        start = idx + 1
        count += 1
