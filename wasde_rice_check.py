import sys, json
sys.path.insert(0, "G:/My Drive/Projects/_studio")
import wasde_parser

wasde_parser.AGENT_CONFIG["source_url"] = "https://www.usda.gov/oce/commodity/wasde/wasde0326.pdf"
log = wasde_parser._setup_logging(wasde_parser.AGENT_CONFIG)
raw = wasde_parser.fetch_raw(wasde_parser.AGENT_CONFIG)
records = wasde_parser.parse_raw(raw, wasde_parser.AGENT_CONFIG)

# Show what Rice record looks like before normalization
rice = [r for r in records if r["commodity"] == "Rice"][0]
print("=== RICE RECORD ===")
print(json.dumps(rice, indent=2, ensure_ascii=False))
