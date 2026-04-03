import sys, json
sys.path.insert(0, "G:/My Drive/Projects/_studio")
import wasde_parser

wasde_parser.AGENT_CONFIG["source_url"] = "https://www.usda.gov/oce/commodity/wasde/wasde0326.pdf"

raw = wasde_parser.fetch_raw(wasde_parser.AGENT_CONFIG)
bundle = json.loads(raw)
print(f"Tables found: {len(bundle['tables'])}")
print(f"Text chars:   {len(bundle['text']):,}")
print()

records = wasde_parser.parse_raw(raw, wasde_parser.AGENT_CONFIG)
print(f"Parsed {len(records)} commodities\n")
for r in records:
    flags = r.get("parse_flags", [])
    print(f"  {r['commodity']:10} | conf={r['confidence']:6} | src={r.get('data_source','?'):5} | "
          f"prod={r['production']:>10} | stocks={r['ending_stocks']:>10} | "
          f"dom_use={r['domestic_use']:>10} | unit={r['unit']}")
    if flags:
        print(f"             FLAGGED: {flags}")
