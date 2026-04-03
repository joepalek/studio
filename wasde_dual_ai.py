"""
wasde_dual_ai.py
================
Dual AI consensus check for WASDE synthesis signals.
Runs Gemini and Mistral independently on same normalized data.
Compares directional calls — tags consensus vs divergent.

Consensus  = both models agree on direction → higher confidence
Divergent  = models disagree → force NEUTRAL, push to human review
Single     = one model failed → use surviving model, tag as single

Applies to all Tier 1 pools, not just WASDE.
Imported by wasde_parser.py and any future pool agent.

Usage:
    from wasde_dual_ai import dual_synthesize
    result = dual_synthesize(normalized_json, cfg, log)
    synthesis  = result["synthesis"]
    confidence = result["confidence"]  # consensus | divergent | single
"""
import json, sys
sys.path.insert(0, "G:/My Drive/Projects/_studio")
from ai_gateway import call as gw_call

# Labels to extract from synthesis output
DIRECTION_LABELS = ["BULLISH", "BEARISH", "NEUTRAL", "MIXED"]

def extract_overall_direction(text: str) -> str:
    """Parse the Overall: line from synthesis output."""
    for line in text.upper().split("\n"):
        if "OVERALL" in line:
            for label in DIRECTION_LABELS:
                if label in line:
                    return label
    # Fallback: count commodity-level labels
    counts = {l: text.upper().count(l) for l in DIRECTION_LABELS}
    return max(counts, key=counts.get) if any(counts.values()) else "UNKNOWN"

def dual_synthesize(normalized: str, cfg: dict, log) -> dict:
    """
    Run synthesis prompt through two models independently.
    Returns consensus-tagged result.

    Args:
        normalized: JSON string of normalized commodity records
        cfg: agent config (must have synthesis_prompt, synthesize_max_tokens)
        log: logger

    Returns dict:
        synthesis:        final synthesis text (consensus or best available)
        confidence:       "consensus" | "divergent" | "single" | "failed"
        model_a_text:     Mistral output
        model_b_text:     Gemini output
        model_a_direction: overall direction from model A
        model_b_direction: overall direction from model B
        agreement:        True/False
        override_applied: True if signal override was run
    """
    # Use str.replace() instead of .format() to avoid KeyError when normalized
    # JSON contains keys like "Commodity" that Python misreads as format placeholders.
    safe_data = normalized[:3000]
    prompt = cfg["synthesis_prompt"].replace("{data}", safe_data)
    max_tokens = cfg.get("synthesize_max_tokens", 400)

    # Model A: Mistral Large (reasoning)
    resp_a = gw_call(prompt, task_type="reasoning", max_tokens=max_tokens)
    text_a = resp_a.text if resp_a.success else ""
    dir_a  = extract_overall_direction(text_a) if text_a else "FAILED"
    if resp_a.success:
        log.info(f"Dual AI Model A (Mistral): {dir_a} via {resp_a.provider}/{resp_a.model}")
    else:
        log.warning(f"Dual AI Model A failed: {resp_a.error}")

    # Model B: Gemini (scoring/batch — maps to Gemini Flash free)
    resp_b = gw_call(prompt, task_type="scoring", max_tokens=max_tokens)
    text_b = resp_b.text if resp_b.success else ""
    dir_b  = extract_overall_direction(text_b) if text_b else "FAILED"
    if resp_b.success:
        log.info(f"Dual AI Model B (Gemini): {dir_b} via {resp_b.provider}/{resp_b.model}")
    else:
        log.warning(f"Dual AI Model B failed: {resp_b.error}")

    # Determine confidence
    both_ok = resp_a.success and resp_b.success
    agreement = (dir_a == dir_b) and both_ok

    if not resp_a.success and not resp_b.success:
        confidence = "failed"
        synthesis  = "Synthesis unavailable — both models failed."
    elif not resp_b.success:
        confidence = "single"
        synthesis  = text_a
        log.info("Dual AI: Model B failed — single model result (Mistral)")
    elif not resp_a.success:
        confidence = "single"
        synthesis  = text_b
        log.info("Dual AI: Model A failed — single model result (Gemini)")
    elif agreement:
        confidence = "consensus"
        # Use Mistral output (more detailed) when both agree
        synthesis  = text_a
        log.info(f"Dual AI CONSENSUS: both models agree — {dir_a}")
    else:
        # Models disagree — force NEUTRAL overall, flag for human review
        confidence = "divergent"
        synthesis  = text_a  # keep Mistral lines, override overall
        # Replace Overall line with NEUTRAL + divergence note
        lines = synthesis.split("\n")
        new_lines = []
        for line in lines:
            if "OVERALL" in line.upper():
                new_lines.append(
                    f"Overall: NEUTRAL -- Models disagree (Mistral={dir_a}, "
                    f"Gemini={dir_b}) — human review required."
                )
            else:
                new_lines.append(line)
        synthesis = "\n".join(new_lines)
        log.warning(f"Dual AI DIVERGENT: Mistral={dir_a} vs Gemini={dir_b} — forced NEUTRAL")

    return {
        "synthesis":         synthesis,
        "confidence":        confidence,
        "model_a_text":      text_a,
        "model_b_text":      text_b,
        "model_a_direction": dir_a,
        "model_b_direction": dir_b,
        "agreement":         agreement,
        "override_applied":  False,  # set True by caller if signal override runs
    }
