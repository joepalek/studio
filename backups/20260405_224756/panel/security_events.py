"""
Security event logging and rate limiting for failed authentication attempts.

Option C Panel Architecture v3.0 - Security Hardening
"""

import json
import os
import hashlib
import hmac
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Optional, Tuple, List

STUDIO = os.environ.get("STUDIO_PATH", "G:/My Drive/Projects/_studio")
SECURITY_LOG = os.path.join(STUDIO, "logs/security-events.jsonl")
RATE_LIMIT_WINDOW = 600  # 10 minutes
MAX_FAILURES = 5

# In-memory rate limit tracking
_failure_counts: dict[str, list] = defaultdict(list)


def log_security_event(
    event_type: str,
    agent_id: str,
    details: dict,
    severity: str = "warning"
) -> None:
    """
    Log a security event to the security events file.
    
    Event types:
    - signature_failure: Invalid HMAC signature
    - replay_attempt: Sequence number replay
    - unknown_agent: Check-in from unregistered agent
    - rate_limit_exceeded: Too many failures
    - secret_rotated: Agent secret was rotated
    - command_blocked: Blocked command execution attempt
    - path_violation: Attempted access outside allowed paths
    """
    event = {
        "timestamp": datetime.now().isoformat(),
        "event_type": event_type,
        "agent_id": agent_id,
        "severity": severity,
        "details": details
    }
    
    os.makedirs(os.path.dirname(SECURITY_LOG), exist_ok=True)
    
    with open(SECURITY_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")


def check_rate_limit(identifier: str) -> Tuple[bool, Optional[str]]:
    """
    Check if identifier has exceeded failure rate limit.
    Returns (is_blocked, reason).
    """
    global _failure_counts
    
    now = datetime.now()
    cutoff = now - timedelta(seconds=RATE_LIMIT_WINDOW)
    
    # Clean old entries
    _failure_counts[identifier] = [
        t for t in _failure_counts[identifier] if t > cutoff
    ]
    
    if len(_failure_counts[identifier]) >= MAX_FAILURES:
        return True, f"Rate limit exceeded: {len(_failure_counts[identifier])} failures in {RATE_LIMIT_WINDOW}s"
    
    return False, None


def record_failure(identifier: str, failure_type: str, details: dict) -> bool:
    """
    Record an authentication failure.
    Returns True if identifier is now rate-limited.
    """
    global _failure_counts
    
    _failure_counts[identifier].append(datetime.now())
    
    log_security_event(
        event_type=failure_type,
        agent_id=identifier,
        details=details,
        severity="warning"
    )
    
    is_blocked, reason = check_rate_limit(identifier)
    if is_blocked:
        log_security_event(
            event_type="rate_limit_exceeded",
            agent_id=identifier,
            details={"reason": reason, "failures": len(_failure_counts[identifier])},
            severity="critical"
        )
    
    return is_blocked


def clear_failures(identifier: str) -> None:
    """Clear failure count for an identifier after successful auth."""
    global _failure_counts
    if identifier in _failure_counts:
        del _failure_counts[identifier]


def get_recent_events(hours: int = 24, event_type: Optional[str] = None) -> List[dict]:
    """Get recent security events for dashboard."""
    events = []
    cutoff = datetime.now() - timedelta(hours=hours)
    
    if not os.path.exists(SECURITY_LOG):
        return []
    
    with open(SECURITY_LOG, "r", encoding="utf-8") as f:
        for line in f:
            try:
                event = json.loads(line.strip())
                event_time = datetime.fromisoformat(event["timestamp"])
                if event_time > cutoff:
                    if event_type is None or event["event_type"] == event_type:
                        events.append(event)
            except:
                continue
    
    return events


def get_security_summary(hours: int = 24) -> dict:
    """Get summary of security events for dashboard."""
    events = get_recent_events(hours)
    
    summary = {
        "period_hours": hours,
        "total_events": len(events),
        "by_type": {},
        "by_severity": {"critical": 0, "warning": 0, "info": 0},
        "rate_limited_identifiers": set(),
        "recent_critical": []
    }
    
    for event in events:
        event_type = event.get("event_type", "unknown")
        severity = event.get("severity", "info")
        
        summary["by_type"][event_type] = summary["by_type"].get(event_type, 0) + 1
        summary["by_severity"][severity] = summary["by_severity"].get(severity, 0) + 1
        
        if event_type == "rate_limit_exceeded":
            summary["rate_limited_identifiers"].add(event.get("agent_id", "unknown"))
        
        if severity == "critical":
            summary["recent_critical"].append({
                "timestamp": event["timestamp"],
                "type": event_type,
                "agent_id": event.get("agent_id")
            })
    
    summary["rate_limited_identifiers"] = list(summary["rate_limited_identifiers"])
    summary["recent_critical"] = summary["recent_critical"][-10:]  # Last 10
    
    return summary


# HMAC signature validation
def validate_signature(
    payload: bytes,
    signature: str,
    secret: str
) -> Tuple[bool, Optional[str]]:
    """
    Validate HMAC-SHA256 signature.
    Returns (is_valid, error_message).
    """
    try:
        expected = hmac.new(
            secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        if hmac.compare_digest(signature, expected):
            return True, None
        else:
            return False, "Signature mismatch"
    except Exception as e:
        return False, f"Signature validation error: {e}"


def generate_signature(payload: bytes, secret: str) -> str:
    """Generate HMAC-SHA256 signature for payload."""
    return hmac.new(
        secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python security_events.py summary [hours]")
        print("  python security_events.py recent [hours] [event_type]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "summary":
        hours = int(sys.argv[2]) if len(sys.argv) > 2 else 24
        result = get_security_summary(hours)
        print(json.dumps(result, indent=2, default=str))
    
    elif command == "recent":
        hours = int(sys.argv[2]) if len(sys.argv) > 2 else 24
        event_type = sys.argv[3] if len(sys.argv) > 3 else None
        events = get_recent_events(hours, event_type)
        for event in events[-20:]:  # Last 20
            print(json.dumps(event))
