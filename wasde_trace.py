import sys, json, traceback
sys.path.insert(0, "G:/My Drive/Projects/_studio")
import wasde_parser

wasde_parser.AGENT_CONFIG["source_url"] = "https://www.usda.gov/oce/commodity/wasde/wasde0326.pdf"

log = wasde_parser._setup_logging(wasde_parser.AGENT_CONFIG)
raw = wasde_parser.fetch_raw(wasde_parser.AGENT_CONFIG)
records = wasde_parser.parse_raw(raw, wasde_parser.AGENT_CONFIG)
normalized = wasde_parser._normalize_with_gemini(records, wasde_parser.AGENT_CONFIG, log)
print("normalized type:", type(normalized))
print("normalized[:200]:", normalized[:200])

try:
    synthesis = wasde_parser._synthesize_with_mistral(normalized, wasde_parser.AGENT_CONFIG, log)
    print("synthesis:", synthesis[:300])
except Exception as e:
    traceback.print_exc()
