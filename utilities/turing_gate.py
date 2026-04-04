"""
turing_gate.py — Turing Rule enforcement utility.

Every agent output must cite information sources inline using [source_id] notation.
Outputs without citations are flagged, scored, and logged.

Named after Alan Turing: outputs must be verifiable, not just plausible.

Rule: Agent output must include at least one [source_id] citation per factual claim.
Gate: Scan output text for citation markers. Score citation density. Log below threshold.

Import pattern:
    from turing_gate import turing_check, turing_wrap, TURING_MIN_DENSITY

# EXPECTED_RUNTIME_SECONDS: 5
"""

import re
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent))
from constraint_gates import log_violation

STUDIO_ROOT = Path("G:/My Drive/Projects/_studio")

# Minimum citation density: at least 1 citation per N sentences
TURING_MIN_DENSITY = 3   # 1 citation per 3 sentences minimum
TURING_MIN_CITATIONS = 1  # at least 1 citation in any output > 2 sentences

# Citation patterns accepted
CITATION_PATTERNS = [
    r'\[[\w\-_\.]+\]',          # [source_id], [game_title], [url_ref]
    r'\[source[:\s]\w+\]',       # [source: wayback], [source:ga]
    r'\(source:[^\)]+\)',        # (source: internet_archive)
    r'Source:\s*\w',             # Source: wayback_machine
    r'Evidence:\s*\w',           # Evidence: title field
    r'Extracted from\s+\w',      # Extracted from listing
    r'\[confidence:\s*[\d\.]+\]', # [confidence: 0.97]
]

COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in CITATION_PATTERNS]

def _count_sentences(text: str) -> int:
    """Rough sentence count."""
    return max(1, len(re.split(r'[.!?]+', text)))


def _count_citations(text: str) -> int:
    """Count total citation markers in text."""
    total = 0
    for pattern in COMPILED_PATTERNS:
        total += len(pattern.findall(text))
    return total


def turing_check(
    output: str,
    agent_name: str = "unknown",
    min_citations: int = TURING_MIN_CITATIONS,
    min_density: int = TURING_MIN_DENSITY,
    raise_on_fail: bool = False
) -> dict:
    """
    Turing Rule gate — check agent output for source citations.

    Returns dict with: compliant, citations_found, sentences, density, issues

    Usage:
        from turing_gate import turing_check
        result = turing_check(agent_output, agent_name="game-archaeology")
        if not result["compliant"]:
            print(f"Turing violation: {result['issues']}")
    """
    sentences = _count_sentences(output)
    citations = _count_citations(output)
    density   = sentences / max(citations, 1)  # sentences per citation

    issues = []
    compliant = True

    # Only apply to outputs with meaningful length (> 2 sentences)
    if sentences > 2:
        if citations < min_citations:
            issues.append(f"no_citations: {citations} found, {min_citations} required")
            compliant = False
        if citations > 0 and density > min_density:
            issues.append(
                f"low_density: 1 citation per {density:.1f} sentences "
                f"(limit: 1 per {min_density})"
            )
            # Low density is a warning, not a hard fail
    result = {
        "compliant":       compliant,
        "citations_found": citations,
        "sentences":       sentences,
        "density":         round(density, 2),
        "issues":          issues,
        "agent":           agent_name,
        "ts":              datetime.now().isoformat()
    }

    if not compliant:
        log_violation("TURING", {
            "agent":           agent_name,
            "citations_found": citations,
            "sentences":       sentences,
            "density":         density,
            "issues":          issues,
            "output_preview":  output[:200]
        })
        if raise_on_fail:
            raise ValueError(
                f"TURING VIOLATION: agent '{agent_name}' output has {citations} citations "
                f"across {sentences} sentences. Add [source_id] markers to factual claims."
            )

    return result


def turing_wrap(func):
    """
    Turing Rule decorator — auto-checks return value of agent functions
    that return string output.

    Usage:
        from turing_gate import turing_wrap

        @turing_wrap
        def generate_legal_assessment(game: dict) -> str:
            ...  # must include [source_id] in returned text
    """
    import functools

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        if isinstance(result, str):
            turing_check(result, agent_name=func.__name__)
        elif isinstance(result, dict) and "reasoning" in result:
            turing_check(str(result["reasoning"]), agent_name=func.__name__)
        return result
    return wrapper


def turing_annotate(
    value: str,
    source_id: str,
    confidence: Optional[float] = None
) -> str:
    """
    Helper: append a citation marker to an extracted value.

    Usage:
        title = turing_annotate("Hellmaze", source_id="ia:web20060601")
        # Returns: "Hellmaze [ia:web20060601]"

        title = turing_annotate("Hellmaze", source_id="ia:web20060601", confidence=0.97)
        # Returns: "Hellmaze [ia:web20060601][confidence:0.97]"
    """
    annotation = f"[{source_id}]"
    if confidence is not None:
        annotation += f"[confidence:{confidence:.2f}]"
    return f"{value} {annotation}"


def turing_report(outputs: list[dict]) -> dict:
    """
    Batch Turing audit — run turing_check across multiple agent outputs.
    Returns summary stats.

    Usage:
        results = turing_report([
            {"text": agent_output_1, "agent": "game-archaeology"},
            {"text": agent_output_2, "agent": "legal-agent"},
        ])
    """
    checks = []
    for item in outputs:
        check = turing_check(
            item.get("text", ""),
            agent_name=item.get("agent", "unknown"),
            raise_on_fail=False
        )
        checks.append(check)

    total = len(checks)
    compliant = sum(1 for c in checks if c["compliant"])
    avg_density = sum(c["density"] for c in checks) / max(total, 1)

    return {
        "total":          total,
        "compliant":      compliant,
        "violations":     total - compliant,
        "compliance_pct": round(compliant / max(total, 1) * 100, 1),
        "avg_density":    round(avg_density, 2),
        "details":        checks
    }
