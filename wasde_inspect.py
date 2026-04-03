import sys, json
sys.path.insert(0, "G:/My Drive/Projects/_studio")
import wasde_parser

wasde_parser.AGENT_CONFIG["source_url"] = "https://www.usda.gov/oce/commodity/wasde/wasde0326.pdf"
raw = wasde_parser.fetch_raw(wasde_parser.AGENT_CONFIG)
bundle = json.loads(raw)

print("=== TABLES ===")
for i, t in enumerate(bundle["tables"]):
    print(f"\n-- Table {i} ({len(t)} rows) --")
    for row in t[:5]:
        print(row)

print("\n=== TEXT SAMPLE around WHEAT ===")
text = bundle["text"]
idx = text.upper().find("WHEAT")
if idx >= 0:
    print(text[idx:idx+800])
