"""
babbage_gate.py — Babbage Rule enforcement utility.

Extracted data must be schema-validated before downstream use.
Prevents garbage-in-garbage-out at the READ side of the pipeline.

Complements Hopper (write-time validation) and Codd (confidence gating).
Babbage operates at decision-read time — before data reaches any
reasoning, scoring, or output-generating function.

Named after Charles Babbage: data fed into a system must be correct
before computation begins. Garbage in = garbage out, always.

Rule: Any function that consumes extracted data for decisions MUST
      call babbage_validate() on the input before proceeding.

# EXPECTED_RUNTIME_SECONDS: 5
"""

import re
import json
import functools
from pathlib import Path
from datetime import datetime
from typing import Any, Optional, Union

import sys
sys.path.insert(0, str(Path(__file__).parent))
from constraint_gates import log_violation

STUDIO_ROOT = Path("G:/My Drive/Projects/_studio")

# ─────────────────────────────────────────────────────────────────
# SCHEMA DEFINITIONS — canonical shapes for common pipeline data
# Add new schemas here as pipelines grow
# ─────────────────────────────────────────────────────────────────

SCHEMAS = {

    "inbox_item": {
        "required": ["id", "source", "type", "urgency", "title", "finding", "status", "date"],
        "types": {
            "id": str, "source": str, "type": str, "urgency": str,
            "title": str, "finding": str, "status": str, "date": str,
        },
        "enums": {
            "urgency": {"low", "medium", "high", "critical",
                        "LOW", "MEDIUM", "HIGH", "CRITICAL", "WARN", "INFO"},  # legacy
            "status":  {"pending", "resolved", "expired", "escalated",
                        "PENDING", "RESOLVED", "EXPIRED"},              # legacy uppercase
        },
    },

    "legal_assessment": {
        "required": ["game_title", "risk_level", "confidence", "reasoning",
                     "tier_recommendation"],
        "types": {
            "game_title": str, "risk_level": str,
            "confidence": float, "reasoning": str, "tier_recommendation": str,
        },
        "enums": {
            "risk_level": {"GREEN", "YELLOW", "RED"},
        },
        "ranges": {
            "confidence": (0.0, 1.0),
        },
    },

    "job_listing": {
        "required": ["id", "title", "source"],
        "types": {"id": str, "title": str, "source": str},
        "optional_types": {
            "salary": (str, type(None)),
            "location": (str, type(None)),
            "date_posted": (str, type(None)),
        },
    },

    "extraction_result": {
        "required": ["value", "confidence", "source"],
        "types": {"confidence": float, "source": str},
        "ranges": {"confidence": (0.0, 1.0)},
    },

    "whiteboard_item": {
        "required": ["id", "title", "type"],
        "types": {"id": str, "title": str, "type": str},
    },

    "game_candidate": {
        "required": ["title", "source_url"],
        "types": {"title": str, "source_url": str},
        "optional_types": {
            "original_creator": (str, type(None)),
            "release_date": (str, type(None)),
            "has_source_code": bool,
        },
    },

    "source_registry_entry": {
        "required": ["url"],
        "types": {"url": str},
        "optional_types": {
            "name": str, "tier": (str, type(None)),
            "status": (str, type(None)),
        },
    },
}


# ─────────────────────────────────────────────────────────────────
# CORE VALIDATOR
# ─────────────────────────────────────────────────────────────────

def babbage_validate(
    data: Any,
    schema_name: str,
    agent: str = "unknown",
    raise_on_fail: bool = False
) -> dict:
    """
    Babbage Rule gate — validate extracted data against a named schema
    before it reaches any downstream decision function.

    Returns dict: {valid, schema, violations, data_preview}

    Usage:
        from babbage_gate import babbage_validate

        def score_game(candidate: dict):
            result = babbage_validate(candidate, "game_candidate", agent="whiteboard")
            if not result["valid"]:
                return None  # refuse to score corrupt input
            # safe to proceed
            ...
    """
    schema = SCHEMAS.get(schema_name)
    if schema is None:
        log_violation("BABBAGE", {
            "agent": agent,
            "error": f"unknown_schema:{schema_name}",
            "data_preview": str(data)[:100]
        })
        if raise_on_fail:
            raise ValueError(f"BABBAGE: unknown schema '{schema_name}'")
        return {"valid": False, "schema": schema_name,
                "violations": [f"unknown_schema:{schema_name}"], "data_preview": str(data)[:100]}

    violations = []

    # Handle list input — validate each item
    if isinstance(data, list):
        for i, item in enumerate(data[:20]):  # sample first 20
            result = _validate_item(item, schema, schema_name, agent)
            for v in result:
                violations.append(f"[{i}] {v}")
        if len(data) > 20:
            violations.append(f"note: only first 20 of {len(data)} items checked")
    elif isinstance(data, dict):
        violations = _validate_item(data, schema, schema_name, agent)
    else:
        violations = [f"unexpected_type:{type(data).__name__}"]

    valid = len([v for v in violations if not v.startswith("note:")]) == 0

    if not valid:
        log_violation("BABBAGE", {
            "agent":      agent,
            "schema":     schema_name,
            "violations": violations[:10],
            "data_preview": str(data)[:150]
        })
        if raise_on_fail:
            raise ValueError(
                f"BABBAGE VIOLATION: data fails '{schema_name}' schema — {violations[:3]}"
            )

    return {
        "valid":        valid,
        "schema":       schema_name,
        "violations":   violations,
        "data_preview": str(data)[:100]
    }


def _validate_item(item: dict, schema: dict, schema_name: str, agent: str) -> list:
    """Validate one dict item against a schema. Returns list of violation strings."""
    violations = []

    if not isinstance(item, dict):
        return [f"expected_dict_got:{type(item).__name__}"]

    # Required fields
    for field in schema.get("required", []):
        if field not in item:
            violations.append(f"missing_required:{field}")
        elif item[field] is None:
            violations.append(f"null_required:{field}")

    # Type checks
    for field, expected_type in schema.get("types", {}).items():
        if field in item and item[field] is not None:
            if not isinstance(item[field], expected_type):
                violations.append(
                    f"wrong_type:{field}={type(item[field]).__name__}"
                    f"(expected {expected_type.__name__})"
                )

    # Optional type checks (allow None)
    for field, expected_types in schema.get("optional_types", {}).items():
        if field in item and item[field] is not None:
            if not isinstance(item[field], expected_types):
                violations.append(f"wrong_optional_type:{field}")

    # Enum checks
    for field, valid_values in schema.get("enums", {}).items():
        if field in item and item[field] is not None:
            if item[field] not in valid_values:
                violations.append(
                    f"invalid_enum:{field}={item[field]!r}"
                    f"(allowed:{sorted(valid_values)})"
                )

    # Range checks
    for field, (lo, hi) in schema.get("ranges", {}).items():
        if field in item and item[field] is not None:
            try:
                val = float(item[field])
                if not (lo <= val <= hi):
                    violations.append(f"out_of_range:{field}={val}(allowed:{lo}-{hi})")
            except (TypeError, ValueError):
                violations.append(f"non_numeric:{field}={item[field]!r}")

    return violations


# ─────────────────────────────────────────────────────────────────
# DECORATOR + FILE LOADER
# ─────────────────────────────────────────────────────────────────

def babbage_guard(schema_name: str, arg_index: int = 0, raise_on_fail: bool = False):
    """
    Babbage Rule decorator factory.
    Validates the specified argument before the function runs.
    Blocks execution on schema failure (returns None by default).

    Usage:
        from babbage_gate import babbage_guard

        @babbage_guard("legal_assessment")
        def score_assessment(assessment: dict) -> float:
            # only runs if assessment passes schema
            return assessment["confidence"] * 10

        @babbage_guard("game_candidate", arg_index=1)
        def process_game(config: dict, game: dict):
            ...
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if arg_index < len(args):
                data = args[arg_index]
            else:
                data = None

            if data is not None:
                result = babbage_validate(
                    data, schema_name,
                    agent=func.__name__,
                    raise_on_fail=raise_on_fail
                )
                if not result["valid"]:
                    print(
                        f"[BABBAGE] {func.__name__} blocked — "
                        f"input fails '{schema_name}' schema: {result['violations'][:2]}"
                    )
                    return None
            return func(*args, **kwargs)
        return wrapper
    return decorator


def babbage_load(
    path: Union[str, Path],
    schema_name: str,
    agent: str = "unknown",
    strict: bool = False
) -> Optional[Any]:
    """
    Babbage Rule file loader — load JSON and validate before returning.
    Drop-in replacement for json.load() on pipeline data files.

    Returns validated data or None on failure.

    Usage:
        from babbage_gate import babbage_load

        # Instead of: data = json.load(open(path))
        data = babbage_load(path, schema_name="legal_assessment", agent="scorer")
        if data is None:
            return  # schema check failed, logged
    """
    path = Path(path)
    if not path.exists():
        log_violation("BABBAGE", {
            "agent": agent, "schema": schema_name,
            "error": f"file_not_found:{path}"
        })
        return None

    try:
        data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except json.JSONDecodeError as e:
        log_violation("BABBAGE", {
            "agent": agent, "schema": schema_name,
            "error": f"json_parse_error:{e}"
        })
        return None

    result = babbage_validate(data, schema_name, agent=agent, raise_on_fail=strict)
    if not result["valid"]:
        print(
            f"[BABBAGE] {path.name} fails '{schema_name}' schema — "
            f"{len(result['violations'])} violations. Data may be corrupt."
        )
        if strict:
            return None
        # Non-strict: return data anyway but violations are logged
    return data


def babbage_report(paths_and_schemas: list[tuple]) -> dict:
    """
    Batch Babbage audit — validate multiple data files at once.
    Returns summary of schema compliance across the pipeline.

    Usage:
        from babbage_gate import babbage_report
        report = babbage_report([
            ("game_archaeology_legal_results.json", "legal_assessment"),
            ("game_candidates.json",                "game_candidate"),
            ("supervisor-inbox.json",               "inbox_item"),
        ])
        print(report["compliance_pct"])
    """
    results = []
    for path_str, schema_name in paths_and_schemas:
        path = STUDIO_ROOT / path_str if not Path(path_str).is_absolute() else Path(path_str)
        data = babbage_load(path, schema_name, agent="babbage_report", strict=False)
        if data is None:
            results.append({
                "file": path_str, "schema": schema_name,
                "valid": False, "violations": ["load_failed"],
                "items": 0
            })
            continue

        items = data if isinstance(data, list) else [data]
        result = babbage_validate(items, schema_name, agent="babbage_report")
        results.append({
            "file":       path_str,
            "schema":     schema_name,
            "valid":      result["valid"],
            "violations": result["violations"][:5],
            "items":      len(items)
        })

    total     = len(results)
    compliant = sum(1 for r in results if r["valid"])
    return {
        "total":          total,
        "compliant":      compliant,
        "violations":     total - compliant,
        "compliance_pct": round(compliant / max(total, 1) * 100, 1),
        "details":        results
    }
