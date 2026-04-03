import sys, json
sys.path.insert(0, "G:/My Drive/Projects/_studio")
from ai_gateway import call as gw_call

records = [{"commodity": "Wheat", "production": "0.5", "ending_stocks": "350"}]
prompt = (
    "Normalize this WASDE commodity data to clean JSON. "
    "Return ONLY valid JSON array, no markdown, no backticks:\n\n"
    f"{json.dumps(records)}"
)
resp = gw_call(prompt, task_type="batch", max_tokens=500)
print("success:", resp.success)
print("provider:", resp.provider)
print("error:", resp.error)
print("text repr:", repr(resp.text[:200]))
