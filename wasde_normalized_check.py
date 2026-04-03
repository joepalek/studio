import sys, json
sys.path.insert(0, "G:/My Drive/Projects/_studio")
import wasde_parser

wasde_parser.AGENT_CONFIG["source_url"] = "https://www.usda.gov/oce/commodity/wasde/wasde0326.pdf"
log = wasde_parser._setup_logging(wasde_parser.AGENT_CONFIG)
raw = wasde_parser.fetch_raw(wasde_parser.AGENT_CONFIG)
records = wasde_parser.parse_raw(raw, wasde_parser.AGENT_CONFIG)
normalized = wasde_parser._normalize_with_gemini(records, wasde_parser.AGENT_CONFIG, log)

# Show what Mistral actually receives for Rice
try:
    data = json.loads(normalized)
    for r in data:
        if isinstance(r, dict) and r.get("commodity","").lower() == "rice":
            print("=== RICE IN NORMALIZED ===")
            print(json.dumps(r, indent=2, ensure_ascii=False))
except Exception as e:
    print("Parse error:", e)
    print("Raw normalized[:500]:", normalized[:500])
