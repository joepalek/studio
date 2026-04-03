import sys, json
sys.path.insert(0, "G:/My Drive/Projects/_studio")
import wasde_parser

wasde_parser.AGENT_CONFIG["source_url"] = "https://www.usda.gov/oce/commodity/wasde/wasde0326.pdf"
raw = wasde_parser.fetch_raw(wasde_parser.AGENT_CONFIG)
records = wasde_parser.parse_raw(raw, wasde_parser.AGENT_CONFIG)
for r in records:
    print("---", r["commodity"])
    print("narrative:", r.get("narrative","")[:500])
    print()
