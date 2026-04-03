"""
spec_auto_grader.py — Automated Character Spec Grader
=====================================================
Reads spec-queue-current.json, grades each ungraded spec via Gemini,
writes spec-grades.json and passing-specs.json.

Run order in pipeline:
  1. character-spec-generator.py  (3:00 AM) — generates 300 new specs
  2. spec_auto_grader.py          (3:30 AM) — grades specs, writes passing-specs.json
  3. character_batch_builder.py   (5:30 AM) — builds new passing specs into folders

SCHEDULER: \\AgencySpecGrader | 03:30 daily | TTL 1800s
"""

import json, os, sys, time, logging
from datetime import datetime
from pathlib import Path

sys.path.insert(0, "G:/My Drive/Projects/_studio")
from ai_gateway import call as gw_call

STUDIO       = "G:/My Drive/Projects/_studio"
AGENCY       = STUDIO + "/agency"
QUEUE_FILE   = AGENCY + "/spec-queue/spec-queue-current.json"
GRADES_FILE  = AGENCY + "/spec-queue/spec-grades.json"
PASSING_FILE = AGENCY + "/spec-queue/passing-specs.json"
SCHED_LOG    = STUDIO + "/scheduler/logs/overnight-agency-spec-grader.log"
HEARTBEAT    = STUDIO + "/heartbeat-log.json"
INBOX        = STUDIO + "/supervisor-inbox.json"
PASS_THRESHOLD = 8

GRADE_PROMPT = """You are a character development director for a solo AI content studio.
Grade this character spec on a 1-10 scale for potential as a social media / AI-driven content character.

Evaluate on:
- Distinctiveness (unique enough to stand out)
- Commercial appeal (relatable or aspirational to audiences)
- Narrative potential (rich conflict, arc, story hooks)

Character:
Name: {name}
Universe: {universe}
Archetype: {archetype}
Traits: {traits}
Voice: {voice}
Backstory: {backstory}
Age: {age}

Return only valid JSON with keys: grade (int 1-10), pass (bool true if grade>=8), distinctiveness (int 1-10), commercial_appeal (int 1-10), narrative_potential (int 1-10), reason (string under 100 chars). No markdown."""


def setup_log():
    Path(SCHED_LOG).parent.mkdir(parents=True, exist_ok=True)
    log = logging.getLogger("spec-grader")
    log.setLevel(logging.INFO)
    if not log.handlers:
        fh = logging.FileHandler(SCHED_LOG, encoding="utf-8")
        fh.setFormatter(logging.Formatter("[%(asctime)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
        log.addHandler(fh)
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(logging.Formatter("[%(asctime)s] %(message)s", datefmt="%H:%M:%S"))
        log.addHandler(ch)
    return log


def write_heartbeat(status, notes):
    try:
        try:
            data = json.loads(Path(HEARTBEAT).read_text(encoding="utf-8"))
        except:
            data = {"_schema": "1.0", "entries": []}
        data["entries"].append({"date": datetime.now().isoformat(), "agent": "agency-spec-grader", "status": status, "notes": notes})
        tmp = HEARTBEAT + ".tmp"
        Path(tmp).write_text(json.dumps(data, indent=2), encoding="utf-8")
        os.replace(tmp, HEARTBEAT)
    except Exception as e:
        print(f"WARNING: heartbeat write failed: {e}")


def push_inbox(item):
    try:
        raw = json.loads(Path(INBOX).read_text(encoding="utf-8"))
        items = raw.get("items", raw) if isinstance(raw, dict) else raw
        if item["id"] not in {i.get("id") for i in items}:
            items.append(item)
            tmp = INBOX + ".tmp"
            Path(tmp).write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")
            os.replace(tmp, INBOX)
    except Exception as e:
        print(f"WARNING: inbox push failed: {e}")


def grade_spec(spec, log):
    prompt = GRADE_PROMPT.format(
        name=spec.get("name","Unknown"), universe=spec.get("universe",""),
        archetype=spec.get("archetype",""), traits=", ".join(spec.get("personality_traits",[])),
        voice=spec.get("voice",""), backstory=spec.get("backstory",""), age=spec.get("age","")
    )
    # Provider priority: Cerebras (fast, generous rate limits) → Mistral → Groq
    # Gemini excluded — SSE streaming causes partial JSON reads via urllib
    for provider, model in [("cerebras", "llama3.1-8b"),
                             ("mistral",  "mistral-small-latest"),
                             ("groq",     "llama-3.3-70b-versatile")]:
        resp = gw_call(prompt, task_type="scoring", max_tokens=500,
                       force_provider=provider, force_model=model)
        if not resp.success:
            if "429" in str(resp.error):
                log.warning(f"429 on {provider} — sleeping 8s before fallback")
                time.sleep(8)
                continue
            log.warning(f"Grade call failed for {spec['id']}: {resp.error}")
            continue
        text = resp.text.strip()
        brace = text.find("{")
        if brace > 0:
            text = text[brace:]
        if "```" in text:
            text = text.split("```")[0].strip()
        try:
            result = json.loads(text)
            result["pass"] = result.get("grade", 0) >= PASS_THRESHOLD
            result["graded_date"] = datetime.now().isoformat()
            result["graded_by"] = f"{resp.provider}/{resp.model}"
            return result
        except Exception as e:
            log.warning(f"JSON parse failed for {spec['id']} via {provider}: {e} raw: {text[:60]}")
            continue
    return None


def save_grades(grades, log):
    data = {"last_updated": datetime.now().isoformat(), "total_graded": len(grades), "grades": grades}
    tmp = GRADES_FILE + ".tmp"
    Path(tmp).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, GRADES_FILE)
    log.info(f"Grades saved: {len(grades)} total")


def main():
    log = setup_log()
    log.info("=== spec-auto-grader START ===")
    t0 = time.time()

    try:
        specs = json.loads(Path(QUEUE_FILE).read_text(encoding="utf-8")).get("specs", [])
        log.info(f"Queue loaded: {len(specs)} specs")
    except Exception as e:
        log.error(f"Failed to load queue: {e}")
        write_heartbeat("flagged", f"queue load failed: {str(e)[:80]}")
        sys.exit(1)

    try:
        grades = json.loads(Path(GRADES_FILE).read_text(encoding="utf-8")).get("grades", {})
        log.info(f"Existing grades: {len(grades)}")
    except:
        grades = {}
        log.info("No existing grades — fresh run")

    ungraded = [s for s in specs if s.get("id") not in grades]
    log.info(f"Ungraded: {len(ungraded)} specs to grade")

    if not ungraded:
        log.info("All specs already graded — nothing to do")
        write_heartbeat("clean", f"idle — all {len(specs)} specs already graded")
        sys.exit(0)

    graded_count = 0
    failed_count = 0
    consecutive_429 = 0

    for i, spec in enumerate(ungraded):
        result = grade_spec(spec, log)
        if result:
            grades[spec.get("id", f"unknown-{i}")] = result
            graded_count += 1
            consecutive_429 = 0
        else:
            failed_count += 1
            # Check if last failure was 429 — back off longer
            consecutive_429 += 1
            if consecutive_429 >= 2:
                log.info(f"Rate limit backoff — sleeping 5s")
                time.sleep(5)
                consecutive_429 = 0
        if (i + 1) % 10 == 0:
            log.info(f"  Progress: {i+1}/{len(ungraded)} graded")
        if (i + 1) % 25 == 0:
            save_grades(grades, log)
        time.sleep(0.7)  # Cerebras is generous; 0.7s keeps us well under limits

    save_grades(grades, log)

    passing_ids = {sid for sid, g in grades.items() if g.get("pass")}
    passing_specs = [s for s in specs if s.get("id") in passing_ids]
    passing_data = {"generated": datetime.now().isoformat(), "total_passing": len(passing_specs), "pass_threshold": PASS_THRESHOLD, "specs": passing_specs}
    tmp = PASSING_FILE + ".tmp"
    Path(tmp).write_text(json.dumps(passing_data, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, PASSING_FILE)
    log.info(f"passing-specs.json: {len(passing_specs)} passing / {len(specs)} total")

    elapsed = int(time.time() - t0)
    pass_rate = f"{len(passing_specs)/len(specs)*100:.0f}%" if specs else "0%"
    summary = f"graded={graded_count} failed={failed_count} passing={len(passing_specs)} pass_rate={pass_rate} elapsed={elapsed}s"
    log.info(f"=== COMPLETE === {summary}")
    write_heartbeat("clean" if failed_count == 0 else "flagged", summary)

    if failed_count > 10:
        push_inbox({"id": f"spec-grader-warn-{datetime.now().strftime('%Y%m%d')}", "source": "agency-spec-grader",
                    "type": "agent_error", "urgency": "WARN", "title": f"Spec grader: {failed_count} grade failures",
                    "finding": summary, "status": "PENDING", "date": datetime.now().isoformat()})


if __name__ == "__main__":
    main()
