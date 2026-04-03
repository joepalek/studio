import sys, json
sys.path.insert(0, "G:/My Drive/Projects/_studio")
import wasde_parser

wasde_parser.AGENT_CONFIG["source_url"] = "https://www.usda.gov/oce/commodity/wasde/wasde0326.pdf"

log = wasde_parser._setup_logging(wasde_parser.AGENT_CONFIG)
raw = wasde_parser.fetch_raw(wasde_parser.AGENT_CONFIG)
records = wasde_parser.parse_raw(raw, wasde_parser.AGENT_CONFIG)
normalized = wasde_parser._normalize_with_gemini(records, wasde_parser.AGENT_CONFIG, log)
synthesis = wasde_parser._synthesize_with_mistral(normalized, wasde_parser.AGENT_CONFIG, log)
classification = wasde_parser._classify_with_ollama(normalized[:500], wasde_parser.AGENT_CONFIG, log)

print("=== SYNTHESIS ===")
print(synthesis)
print("\n=== CLASSIFICATION ===", classification)
