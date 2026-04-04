"""
constraint_gates.py — Structural enforcement for all named studio constraints.

Implements: Shannon, Hamilton, Hopper, Kay, Codd, Lovelace, Compounding Failure
All violations write to: G:/My Drive/Projects/_studio/error-log.json

Import pattern:
    import sys
    sys.path.insert(0, 'G:/My Drive/Projects/_studio/utilities')
    from constraint_gates import (
        shannon_check, hopper_write, kay_validate,
        codd_gate, lovelace_start, lovelace_complete,
        compounding_guard, log_violation
    )
"""

import json
import re
import functools
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

STUDIO_ROOT = Path("G:/My Drive/Projects/_studio")
ERROR_LOG = STUDIO_ROOT / "error-log.json"
DECISION_LOG = STUDIO_ROOT / "decision-log.json"


def _get_constraint_version() -> str:
    """Get current constraint version without circular import."""
    try:
        from constraint_version import get_version
        return get_version()
    except Exception:
        return "unknown"


# ---------------------------------------------------------------------------
# SHARED: violation logger
# ---------------------------------------------------------------------------

def log_violation(rule: str, detail: dict) -> None:
    """Append one violation entry to error-log.json. Never raises."""
    entry = {
        "rule": rule,
        "ts": datetime.now().isoformat(),
        "constraint_version": _get_constraint_version(),
        **detail
    }
    try:
        ERROR_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(ERROR_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        print(f"[constraint_gates] WARNING: could not write to error-log.json: {e}")


# ---------------------------------------------------------------------------
# SHANNON RULE — handoff token gate
# ---------------------------------------------------------------------------

def _count_tokens(text: str) -> int:
    """Proxy token count: words * 1.3. Good enough for gate purposes."""
    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except ImportError:
        return int(len(text.split()) * 1.3)


def shannon_check(text: str, max_tokens: int = 200, source_file: str = "session-handoff.md") -> str:
    """
    Shannon Rule enforcement gate.
    Returns text if under limit. Truncates + logs violation if over.

    Usage:
        from constraint_gates import shannon_check
        safe_handoff = shannon_check(handoff_text)
        write(safe_handoff, "session-handoff.md")
    """
    token_count = _count_tokens(text)
    if token_count <= max_tokens:
        return text

    # Violation — truncate to first max_tokens worth of words
    words = text.split()
    budget = int(max_tokens / 1.3)
    truncated = " ".join(words[:budget])
    truncated += f"\n\n[SHANNON: truncated from ~{token_count}t to ~{max_tokens}t]"

    log_violation("SHANNON", {
        "file": source_file,
        "tokens_found": token_count,
        "tokens_limit": max_tokens,
        "action": "blocked_truncated"
    })
    print(f"[SHANNON] VIOLATION: {source_file} was ~{token_count} tokens. Truncated to {max_tokens}.")
    return truncated


# ---------------------------------------------------------------------------
# HOPPER RULE — inbox schema validation
# ---------------------------------------------------------------------------

INBOX_REQUIRED_FIELDS = {"id", "source", "type", "urgency", "title", "finding", "status", "date"}
INBOX_URGENCY_VALUES  = {"low", "medium", "high", "critical"}
INBOX_STATUS_VALUES   = {"pending", "resolved", "expired", "escalated"}


def hopper_validate(item: dict, inbox_path: str = "unknown-inbox.json") -> dict:
    """
    Hopper Rule enforcement gate.
    Validates inbox item schema before any write.
    Raises ValueError on violation (and logs it).

    Usage:
        from constraint_gates import hopper_validate
        validated = hopper_validate(item_dict, "supervisor-inbox.json")
        append_to_inbox(inbox_path, validated)
    """
    errors = []

    # Required fields
    for field in INBOX_REQUIRED_FIELDS:
        if field not in item:
            errors.append(f"missing_field:{field}")

    # Enum validation
    if "urgency" in item and item["urgency"] not in INBOX_URGENCY_VALUES:
        errors.append(f"invalid_urgency:{item['urgency']}")
    if "status" in item and item["status"] not in INBOX_STATUS_VALUES:
        errors.append(f"invalid_status:{item['status']}")

    # Date format check
    if "date" in item:
        try:
            datetime.fromisoformat(item["date"].replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            errors.append(f"invalid_date_format:{item.get('date')}")

    if errors:
        log_violation("HOPPER", {
            "inbox": inbox_path,
            "errors": errors,
            "rejected_item_id": item.get("id", "UNKNOWN"),
            "rejected_item_title": item.get("title", "")[:80]
        })
        raise ValueError(f"HOPPER VIOLATION: inbox write rejected — {errors}")

    return item


def hopper_append(inbox_path: str, item: dict) -> None:
    """
    Validated append to any *-inbox.json file.
    Always call this instead of writing inbox files directly.

    Usage:
        from constraint_gates import hopper_append
        hopper_append("G:/My Drive/Projects/_studio/supervisor-inbox.json", item)
    """
    validated = hopper_validate(item, inbox_path)
    path = Path(inbox_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    items = []
    if path.exists():
        try:
            with open(path, encoding="utf-8") as f:
                items = json.load(f)
        except Exception:
            items = []

    items.append(validated)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# KAY RULE — supervisor directive validator
# ---------------------------------------------------------------------------

KAY_FORBIDDEN = [
    r'\bthen\b',
    r'\bnext[,\s]',
    r'\bstep\s+\d',
    r'\bdo the following\b',
    r'\brun\s+\S+\.py\b',
    r'\bexecute\b',
    r'\bfollow these steps\b',
    r'\bfirst.*then.*then\b',
]
KAY_REQUIRED = ["GOAL:", "SCOPE:", "SUCCESS_CRITERIA:"]


def kay_validate(directive: str, agent_name: str = "unknown") -> bool:
    """
    Kay Rule enforcement gate.
    Validates supervisor directive before dispatch.
    Raises ValueError if directive is scripted (not goal-oriented).

    Usage:
        from constraint_gates import kay_validate
        kay_validate(directive_text, "vintage-agent")
        send_to_agent(directive_text)  # only reaches here if valid
    """
    violations = []

    for pattern in KAY_FORBIDDEN:
        if re.search(pattern, directive, re.IGNORECASE):
            violations.append(f"forbidden_pattern:{pattern}")

    for field in KAY_REQUIRED:
        if field not in directive:
            violations.append(f"missing_field:{field}")

    if violations:
        log_violation("KAY", {
            "agent": agent_name,
            "violations": violations,
            "directive_preview": directive[:200]
        })
        raise ValueError(
            f"KAY VIOLATION: directive to '{agent_name}' blocked.\n"
            f"Violations: {violations}\n"
            f"Rewrite as goal-oriented directive with GOAL: SCOPE: SUCCESS_CRITERIA:"
        )
    return True


# ---------------------------------------------------------------------------
# CODD EXTRACTION RULE — confidence gate decorator
# ---------------------------------------------------------------------------

CODD_CONFIDENCE_THRESHOLD = 0.95


def codd_gate(func):
    """
    Codd Rule enforcement decorator.
    Wraps extraction functions. Nulls any field with confidence < 0.95
    unless override_by_human is set. Logs all blocked fields.

    Each field in the returned dict must follow this shape:
        { "value": any, "confidence": float, "source": str, "evidence": str }

    Usage:
        from constraint_gates import codd_gate

        @codd_gate
        def extract_listing(html: str) -> dict:
            return {
                "price": {"value": "$14.99", "confidence": 0.97, "source": "title", "evidence": "$14.99 listed in h1"},
                "condition": {"value": "VG", "confidence": 0.80, "source": "desc", "evidence": "described as good"},
            }
        # condition.value will be None after gate — confidence too low
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        if not isinstance(result, dict):
            return result

        blocked = []
        for field, data in result.items():
            if not isinstance(data, dict):
                continue
            confidence = data.get("confidence", 1.0)
            override   = data.get("override_by_human", False)
            if confidence < CODD_CONFIDENCE_THRESHOLD and not override:
                blocked.append({
                    "field": field,
                    "confidence": confidence,
                    "original_value": data.get("value")
                })
                data["value"] = None
                data["codd_blocked"] = True
                data["reason"] = f"confidence {confidence:.2f} < {CODD_CONFIDENCE_THRESHOLD} threshold"

        if blocked:
            log_violation("CODD", {
                "function": func.__name__,
                "blocked_fields": blocked,
                "count": len(blocked)
            })

        return result
    return wrapper


def codd_check(field_name: str, value: Any, confidence: float,
               source: str = "", evidence: str = "",
               override_by_human: bool = False) -> Optional[Any]:
    """
    Inline Codd check for use without the decorator.
    Returns value if confidence >= threshold, None otherwise.

    Usage:
        from constraint_gates import codd_check
        price = codd_check("price", "$14.99", confidence=0.97, source="title", evidence="h1 text")
    """
    if confidence >= CODD_CONFIDENCE_THRESHOLD or override_by_human:
        return value
    log_violation("CODD", {
        "function": "codd_check",
        "blocked_fields": [{"field": field_name, "confidence": confidence, "original_value": value}],
        "count": 1
    })
    return None


# ---------------------------------------------------------------------------
# LOVELACE RULE — savepoint / variant test gate
# ---------------------------------------------------------------------------

LOVELACE_LOG = STUDIO_ROOT / "lovelace-log.json"


def lovelace_start(baseline_ref: str, variant_description: str,
                   success_criteria: str, agent: str = "unknown") -> dict:
    """
    Lovelace Rule — open a variant test record.
    Must be called BEFORE any variant test begins.
    Returns the record dict (pass to lovelace_complete when done).

    Usage:
        from constraint_gates import lovelace_start, lovelace_complete

        record = lovelace_start(
            baseline_ref="git:abc1234",
            variant_description="Testing new Gemini model for scoring",
            success_criteria="Score variance < 5% vs baseline on 20-item test set",
        )
        # ... run variant ...
        lovelace_complete(record, outcome="variance was 3.2%", decision="adopt")
    """
    if not baseline_ref or not baseline_ref.strip():
        log_violation("LOVELACE", {
            "error": "test_started_without_baseline_ref",
            "variant_description": variant_description[:200],
            "agent": agent
        })
        raise ValueError(
            "LOVELACE VIOLATION: variant test blocked — no baseline_ref provided.\n"
            "Save current state first, then call lovelace_start(baseline_ref=...)"
        )

    record = {
        "rule": "LOVELACE",
        "id": f"LOV-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        "agent": agent,
        "baseline_ref": baseline_ref,
        "variant_description": variant_description,
        "success_criteria": success_criteria,
        "started_at": datetime.now().isoformat(),
        "outcome": None,
        "decision": None,
        "completed_at": None
    }

    _lovelace_append(record)
    print(f"[LOVELACE] Variant test opened: {record['id']} | baseline: {baseline_ref}")
    return record


def lovelace_complete(record: dict, outcome: str,
                      decision: str) -> dict:
    """
    Close a Lovelace variant test record.
    decision must be one of: 'adopt', 'restore', 'iterate'
    'restore' and 'iterate' both mean: return to baseline_ref.

    Usage:
        lovelace_complete(record, outcome="variance 3.2% — within criteria", decision="adopt")
    """
    valid_decisions = {"adopt", "restore", "iterate"}
    if decision not in valid_decisions:
        raise ValueError(f"LOVELACE: decision must be one of {valid_decisions}, got '{decision}'")

    record["outcome"] = outcome
    record["decision"] = decision
    record["completed_at"] = datetime.now().isoformat()

    if decision in ("restore", "iterate"):
        print(f"[LOVELACE] {record['id']}: decision='{decision}' — restore from {record['baseline_ref']}")
    else:
        print(f"[LOVELACE] {record['id']}: decision='adopt' — variant accepted")

    _lovelace_update(record)

    # Mirror adopted decisions to decision-log.json
    if decision == "adopt":
        _write_decision_log(record)

    return record


def _lovelace_append(record: dict) -> None:
    records = []
    if LOVELACE_LOG.exists():
        try:
            with open(LOVELACE_LOG, encoding="utf-8") as f:
                records = json.load(f)
        except Exception:
            records = []
    records.append(record)
    with open(LOVELACE_LOG, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)


def _lovelace_update(record: dict) -> None:
    records = []
    if LOVELACE_LOG.exists():
        try:
            with open(LOVELACE_LOG, encoding="utf-8") as f:
                records = json.load(f)
        except Exception:
            records = []
    for i, r in enumerate(records):
        if r.get("id") == record["id"]:
            records[i] = record
            break
    with open(LOVELACE_LOG, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)


def _write_decision_log(record: dict) -> None:
    decisions = []
    if DECISION_LOG.exists():
        try:
            with open(DECISION_LOG, encoding="utf-8") as f:
                decisions = json.load(f)
        except Exception:
            decisions = []
    decisions.append({
        "id": record["id"],
        "date": datetime.now().strftime("%Y-%m-%d"),
        "decision": f"Adopted variant: {record['variant_description'][:100]}",
        "reason": record["outcome"],
        "permanence": "revisable",
        "status": "active",
        "lovelace_ref": record["baseline_ref"]
    })
    with open(DECISION_LOG, "w", encoding="utf-8") as f:
        json.dump(decisions, f, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# HAMILTON RULE — TTL watchdog (Windows-compatible threading approach)
# ---------------------------------------------------------------------------

def hamilton_watchdog(task_name: str, expected_seconds: int):
    """
    Hamilton Rule — TTL watchdog decorator factory.
    Aborts task if it exceeds expected_seconds * 1.5.
    Uses threading.Timer for Windows compatibility (no SIGALRM on Windows).

    Usage:
        from constraint_gates import hamilton_watchdog

        @hamilton_watchdog("job-harvest-daily", expected_seconds=300)
        def run_harvest():
            ...  # your agent main logic here
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            ttl = int(expected_seconds * 1.5)
            abort_flag = threading.Event()
            result_holder = [None]
            error_holder  = [None]

            def _run():
                try:
                    result_holder[0] = func(*args, **kwargs)
                except Exception as e:
                    error_holder[0] = e

            def _on_timeout():
                abort_flag.set()
                log_violation("HAMILTON", {
                    "task": task_name,
                    "expected_s": expected_seconds,
                    "ttl_s": ttl,
                    "action": "aborted_timeout"
                })
                print(f"[HAMILTON] ABORT: '{task_name}' exceeded TTL of {ttl}s ({expected_seconds}s + 50% grace)")

            timer  = threading.Timer(ttl, _on_timeout)
            thread = threading.Thread(target=_run, daemon=True)
            timer.start()
            thread.start()
            thread.join(timeout=ttl + 5)
            timer.cancel()

            if abort_flag.is_set():
                raise SystemExit(f"[HAMILTON] '{task_name}' killed by TTL watchdog after {ttl}s")
            if error_holder[0]:
                raise error_holder[0]
            return result_holder[0]
        return wrapper
    return decorator


# ---------------------------------------------------------------------------
# COMPOUNDING FAILURE RULE — attempt counter guard
# ---------------------------------------------------------------------------

_attempt_registry: dict[str, int] = {}


def compounding_guard(operation_key: str, max_attempts: int = 3) -> None:
    """
    Compounding Failure Rule — blocks repeated attempts without new information.
    Call at the top of each retry attempt with a consistent operation_key.
    Raises RuntimeError and escalates after max_attempts.

    Usage:
        from constraint_gates import compounding_guard, compounding_reset

        for attempt in range(10):
            compounding_guard("fetch_career_page")  # blocks at attempt 4+
            try:
                result = fetch(url)
                compounding_reset("fetch_career_page")
                break
            except Exception as e:
                print(f"Attempt failed: {e}")
    """
    count = _attempt_registry.get(operation_key, 0) + 1
    _attempt_registry[operation_key] = count

    if count > max_attempts:
        log_violation("COMPOUNDING_FAILURE", {
            "operation": operation_key,
            "attempts": count,
            "max_allowed": max_attempts,
            "action": "blocked_escalated"
        })
        # Escalate to supervisor inbox
        try:
            hopper_append(
                str(STUDIO_ROOT / "supervisor-inbox.json"),
                {
                    "id": f"CF-{operation_key[:20]}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    "source": "constraint_gates",
                    "type": "compounding_failure",
                    "urgency": "high",
                    "title": f"Compounding failure: {operation_key}",
                    "finding": f"Operation '{operation_key}' attempted {count}x without new information. Blocked.",
                    "status": "pending",
                    "date": datetime.now().isoformat()
                }
            )
        except Exception:
            pass  # escalation failure shouldn't mask the guard
        raise RuntimeError(
            f"COMPOUNDING FAILURE: '{operation_key}' blocked after {count} attempts.\n"
            f"State what failed and what new information is needed before retrying."
        )


def compounding_reset(operation_key: str) -> None:
    """Reset attempt counter after a successful operation."""
    _attempt_registry.pop(operation_key, None)

