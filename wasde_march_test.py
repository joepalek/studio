"""Temporary test runner — runs wasde_parser against March 2026 PDF (dry run)."""
import sys
sys.path.insert(0, "G:/My Drive/Projects/_studio")
import wasde_parser

wasde_parser.AGENT_CONFIG["source_url"] = "https://www.usda.gov/oce/commodity/wasde/wasde0326.pdf"
import traceback
try:
    result = wasde_parser.run(wasde_parser.AGENT_CONFIG, dry=True)
    print("RESULT:", result)
except Exception as e:
    traceback.print_exc()
