"""
test_fallback.py — Prove the fallback chain works
Simulates Mistral Large being unavailable and shows gateway falling to #2
"""
import sys, json, time
sys.path.insert(0, "G:/My Drive/Projects/_studio")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import ai_gateway as gw

# Patch at the module level where call() looks it up
def fake_mistral(cfg, model, prompt, max_tokens):
    raise Exception("HTTP Error 429: Too Many Requests — monthly quota exhausted")

gw.PROVIDER_CALLERS["mistral"] = fake_mistral

print("=== FALLBACK CHAIN TEST ===")
print("Mistral Large patched to FAIL (simulating quota exhausted)")
print()

r = gw.call(
    prompt="What are 2 risks of building an AI business in 2026? Be very brief.",
    task_type="reasoning",
    max_tokens=150,
    fallback=True
)

print(f"Provider used:  {r.provider}")
print(f"Model used:     {r.model}")
print(f"Cost tier:      {r.cost_tier}")
print(f"Latency:        {r.latency_ms}ms")
print(f"Success:        {r.success}")
print(f"Response:       {r.text[:200]}")
print()
print("=== CHECK GATEWAY LOG (last 3 lines) ===")
with open("G:/My Drive/Projects/_studio/gateway-log.txt",
          encoding="utf-8", errors="replace") as f:
    lines = f.readlines()
for line in lines[-3:]:
    print(line.strip())
