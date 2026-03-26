"""
auto_answer_gemini.py — Inbox Triage via Gemini Flash
Replaces Claude-based overnight-auto-answer.bat.
Reads mobile-inbox.json, applies standing-rules.json, uses
Gemini Flash for remaining items. Writes results back to inbox.
"""

import json, os, urllib.request, urllib.error
from datetime import datetime

STUDIO = "G:/My Drive/Projects/_studio"
INBOX_PATH   = os.path.join(STUDIO, "mobile-inbox.json")
RULES_PATH   = os.path.join(STUDIO, "standing-rules.json")
MEM_PATH     = os.path.join(STUDIO, "answers-memory.json")
CONFIG_PATH  = os.path.join(STUDIO, "studio-config.json")
STATUS_PATH  = os.path.join(STUDIO, "claude-status.txt")
HB_PATH      = os.path.join(STUDIO, "heartbeat-log.json")


def load_json(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def save_json(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, path)


def gemini_call(key, prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={key}"
    payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode()
    req = urllib.request.Request(url, data=payload,
                                  headers={"Content-Type": "application/json"})
    r = urllib.request.urlopen(req, timeout=20)
    return json.loads(r.read())["candidates"][0]["content"]["parts"][0]["text"].strip()


def match_rule(item, rules):
    """Return first matching rule or None."""
    item_text = " ".join([
        item.get("title", ""),
        item.get("question", ""),
        item.get("category", ""),
        " ".join(item.get("tags", [])),
        item.get("description", ""),
    ]).lower()
    for rule in rules:
        trigger = rule.get("trigger", "").lower()
        if trigger and trigger in item_text:
            return rule
    return None


def write_status(msg):
    ts = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    with open(STATUS_PATH, "a", encoding="utf-8") as f:
        f.write(f"{ts} [AUTO-ANSWER] {msg}\n")


def write_heartbeat(status, notes):
    data = load_json(HB_PATH)
    if not isinstance(data, dict) or "entries" not in data:
        data = {"_schema": "1.0", "entries": []}
    data["entries"].append({
        "date": datetime.now().isoformat(),
        "agent": "auto-answer-gemini",
        "status": status,
        "notes": notes
    })
    save_json(HB_PATH, data)


def main():
    config = load_json(CONFIG_PATH, {})
    gemini_key = config.get("gemini_api_key", "")
    if not gemini_key:
        print("[auto-answer] ERROR: no gemini_api_key in studio-config.json")
        write_status("ERROR: no gemini_api_key — triage aborted")
        write_heartbeat("flagged", "[auto-answer] gemini_api_key missing — aborted")
        return

    # Load knowledge bases
    rules = load_json(RULES_PATH, {}).get("rules", [])
    memory = load_json(MEM_PATH, {}).get("answers", [])
    inbox = load_json(INBOX_PATH, [])
    if isinstance(inbox, dict):
        inbox = inbox.get("items", inbox.get("questions", []))

    pending = [i for i in inbox if isinstance(i, dict) and i.get("status") in ("pending", "active", None)]
    print(f"[auto-answer] Inbox: {len(inbox)} total, {len(pending)} pending")
    print(f"[auto-answer] Rules: {len(rules)} | Memory: {len(memory)} entries")

    auto_resolved = 0
    escalated = 0

    for item in pending:
        # Pass 1 — rule match
        rule = match_rule(item, rules)
        if rule:
            item["status"] = "auto-resolved"
            item["auto_answer"] = rule.get("action", "resolved by rule")
            item["resolved_by"] = f"rule:{rule.get('id','?')}"
            item["resolved_at"] = datetime.now().isoformat()
            auto_resolved += 1
            print(f"  [RULE] {item.get('question','?')[:60]} → {rule.get('action','?')[:40]}")
            continue

        # Pass 2 — Gemini triage (only for non-whiteboard, non-log items)
        item_type = item.get("type", "")
        if item_type in ("whiteboard_top10", "sidebar_log"):
            escalated += 1
            continue

        question = item.get("question", item.get("title", ""))
        if not question:
            escalated += 1
            continue

        try:
            prompt = f"""You are an inbox triage assistant for a solo developer's AI studio.
Assess this inbox item and decide: AUTO-RESOLVE (you are confident) or ESCALATE (needs human).

Item type: {item_type}
Question: {question}
Context: {item.get('context', item.get('description', ''))[:300]}

Recent relevant decisions from memory:
{json.dumps(memory[-5:], indent=2)[:400] if memory else '(none)'}

Reply with ONLY valid JSON:
{{
  "decision": "AUTO-RESOLVE" or "ESCALATE",
  "answer": "brief answer if AUTO-RESOLVE, else empty string",
  "confidence": "HIGH" or "MEDIUM" or "LOW",
  "reason": "one sentence"
}}"""
            result_text = gemini_call(gemini_key, prompt)
            result_text = result_text.replace("```json", "").replace("```", "").strip()
            result = json.loads(result_text)
            if result.get("decision") == "AUTO-RESOLVE" and result.get("confidence") == "HIGH":
                item["status"] = "auto-resolved"
                item["auto_answer"] = result.get("answer", "")
                item["resolved_by"] = "gemini-flash"
                item["resolved_at"] = datetime.now().isoformat()
                auto_resolved += 1
                print(f"  [GEMINI] {question[:55]} → {result.get('answer','')[:40]}")
            else:
                escalated += 1
        except Exception as e:
            print(f"  [ERROR] {question[:50]}: {str(e)[:60]}")
            escalated += 1

    save_json(INBOX_PATH, inbox)

    summary = f"auto-resolved {auto_resolved}, escalated {escalated} of {len(pending)} pending"
    print(f"\n[auto-answer] {summary}")
    write_status(summary)
    write_heartbeat("clean", f"[auto-answer] {summary}")


if __name__ == "__main__":
    main()
