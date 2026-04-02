"""
Coordinator Agent - Core Loop
Maintains scrape registry, detects anomalies, suggests optimizations, escalates to Supervisor.

Status: PHASE 1 BUILD
Output files:
  - scrape-registry.json (source of truth)
  - scrape-audit-daily.json (daily health report)
  - scrape-log.json (historical records)
  - coordinator-inbox.json (escalations)
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path

# CONFIG
STUDIO_PATH = Path("G:/My Drive/Projects/_studio")
REGISTRY_FILE = STUDIO_PATH / "scrape-registry.json"
AUDIT_FILE = STUDIO_PATH / "scrape-audit-daily.json"
LOG_FILE = STUDIO_PATH / "scrape-log.json"
INBOX_FILE = STUDIO_PATH / "coordinator-inbox.json"

def load_json(filepath):
    """Load JSON safely; return empty structure if missing."""
    if not filepath.exists():
        return {}
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_json(filepath, data):
    """Save JSON with formatting."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def initialize_registry():
    """Create or load scrape registry."""
    if REGISTRY_FILE.exists():
        return load_json(REGISTRY_FILE)
    
    # Initialize empty registry
    registry = {
        "last_updated": datetime.utcnow().isoformat(),
        "total_scrapes": 0,
        "scrapes": []
    }
    save_json(REGISTRY_FILE, registry)
    return registry

def add_scrape_to_registry(scrape_def):
    """
    Add or update scrape definition in registry.
    
    scrape_def should contain:
    - id, agent_owner, type, target_description
    - frequency, status, cost_tier, provider
    - schedule, output, downstream_consumers, health, optimization
    """
    registry = load_json(REGISTRY_FILE)
    
    # Check if already exists
    existing_idx = next((i for i, s in enumerate(registry.get("scrapes", [])) 
                        if s["id"] == scrape_def["id"]), None)
    
    if existing_idx is not None:
        registry["scrapes"][existing_idx] = scrape_def
    else:
        registry["scrapes"].append(scrape_def)
    
    registry["total_scrapes"] = len(registry["scrapes"])
    registry["last_updated"] = datetime.utcnow().isoformat()
    save_json(REGISTRY_FILE, registry)

def check_scrape_health(scrape):
    """
    Check health of a scrape:
    - Does output file exist?
    - Is it recent (not stale)?
    - Does it have records?
    """
    health = {
        "status": "HEALTHY",
        "last_check": datetime.utcnow().isoformat(),
        "issues": [],
        "uptime_percent_7d": 100
    }
    
    output_path = scrape.get("output", {}).get("file_location")
    if not output_path:
        health["status"] = "WARNING"
        health["issues"].append("No output file location defined")
        return health
    
    try:
        filepath = Path(output_path)
        if not filepath.exists():
            health["status"] = "WARNING"
            health["issues"].append(f"Output file missing: {output_path}")
            return health
        
        # Check recency
        mod_time = datetime.fromtimestamp(filepath.stat().st_mtime)
        age = datetime.utcnow() - mod_time
        expected_interval = scrape.get("schedule", {}).get("expected_interval_hours", 24)
        
        if age > timedelta(hours=expected_interval * 2):
            health["status"] = "WARNING"
            health["issues"].append(f"Data is stale ({age.days}d old, expected <{expected_interval * 2}h)")
        
        # Update record count from file
        scrape["output"]["size_mb"] = round(filepath.stat().st_size / (1024 * 1024), 2)
        scrape["output"]["last_modified"] = mod_time.isoformat()
        
    except Exception as e:
        health["status"] = "WARNING"
        health["issues"].append(f"Health check error: {str(e)}")
    
    return health

def detect_anomalies(registry):
    """Scan all scrapes for anomalies."""
    anomalies = []
    
    for scrape in registry.get("scrapes", []):
        health = check_scrape_health(scrape)
        
        # Log health check
        if health["status"] != "HEALTHY":
            for issue in health["issues"]:
                anomalies.append({
                    "scrape_id": scrape["id"],
                    "type": "STALE" if "stale" in issue.lower() else "MISSING" if "missing" in issue.lower() else "OTHER",
                    "detected_at": datetime.utcnow().isoformat(),
                    "severity": "WARNING",
                    "details": issue,
                    "suggested_action": f"Check {scrape['agent_owner']} agent logs; may need manual trigger",
                    "escalation_level": "SUPERVISOR_REVIEW"
                })
    
    return anomalies

def detect_opportunities(registry):
    """Identify optimization opportunities."""
    opportunities = []
    
    # Flag pending builds with high downstream value
    for scrape in registry.get("scrapes", []):
        if scrape.get("status") == "PENDING_BUILD":
            consumers = scrape.get("downstream_consumers", [])
            if len(consumers) > 0:
                opportunities.append({
                    "opportunity_type": "NEW_SCRAPE",
                    "suggested_scrape_id": scrape["id"],
                    "description": f"{scrape['id']} is pending build and feeds {len(consumers)} projects",
                    "feeds_projects": [c["project"] for c in consumers],
                    "estimated_effort": "MEDIUM",
                    "estimated_value": "HIGH",
                    "priority_score": 8,
                    "approval_status": "PENDING_SUPERVISOR"
                })
    
    return opportunities

def generate_audit():
    """Run full audit cycle."""
    registry = load_json(REGISTRY_FILE)
    
    if not registry.get("scrapes"):
        registry = initialize_registry()
    
    anomalies = detect_anomalies(registry)
    opportunities = detect_opportunities(registry)
    
    # Count health status
    healthy_count = sum(1 for s in registry.get("scrapes", []) 
                       if check_scrape_health(s)["status"] == "HEALTHY")
    
    audit = {
        "audit_date": datetime.utcnow().strftime("%Y-%m-%d"),
        "audit_timestamp": datetime.utcnow().isoformat(),
        "summary": {
            "total_scrapes_active": len([s for s in registry.get("scrapes", []) 
                                        if s.get("status") == "ACTIVE"]),
            "healthy": healthy_count,
            "warnings": len([a for a in anomalies if a["severity"] == "WARNING"]),
            "failures": len([a for a in anomalies if a["severity"] == "CRITICAL"]),
            "total_data_volume_gb": sum(s.get("output", {}).get("size_mb", 0) 
                                       for s in registry.get("scrapes", [])) / 1024,
            "free_quota_consumed_percent": 0,  # TODO: calculate from providers
            "paid_spend_today": "$0.00"
        },
        "anomalies": anomalies,
        "opportunities": opportunities,
        "efficiency_notes": []
    }
    
    save_json(AUDIT_FILE, audit)
    save_json(REGISTRY_FILE, registry)  # Update registry with health checks
    
    return audit

def log_scrape_run(scrape_id, status, records_count, duration_sec, errors=None):
    """Log a scrape execution."""
    log_data = load_json(LOG_FILE)
    if "entries" not in log_data:
        log_data["entries"] = []
    
    log_data["entries"].append({
        "timestamp": datetime.utcnow().isoformat(),
        "scrape_id": scrape_id,
        "run_status": status,
        "records_retrieved": records_count,
        "records_new": 0,  # TODO: calculate from dedup
        "duration_seconds": duration_sec,
        "data_size_mb": 0,  # TODO: calculate from output
        "errors": errors or [],
        "notes": ""
    })
    
    # Keep last 1000 entries
    if len(log_data["entries"]) > 1000:
        log_data["entries"] = log_data["entries"][-1000:]
    
    save_json(LOG_FILE, log_data)

def escalate_to_supervisor(anomaly):
    """Escalate critical issues to Supervisor inbox."""
    inbox = load_json(INBOX_FILE)
    if "entries" not in inbox:
        inbox["entries"] = []
    
    inbox["entries"].append({
        "id": f"coord-{datetime.utcnow().timestamp()}",
        "timestamp": datetime.utcnow().isoformat(),
        "scrape_id": anomaly.get("scrape_id"),
        "message_type": "CRITICAL_FAILURE" if anomaly["severity"] == "CRITICAL" else "WARNING",
        "message": f"[{anomaly['scrape_id']}] {anomaly['details']}",
        "proposed_action": anomaly.get("suggested_action"),
        "urgency": "NOW" if anomaly["severity"] == "CRITICAL" else "TODAY",
        "requires_approval": False,
        "approved": False,
        "approval_timestamp": None
    })
    
    save_json(INBOX_FILE, inbox)

def run_audit_cycle():
    """Main audit cycle."""
    print("[COORDINATOR] Starting audit cycle...")
    
    # Initialize if needed
    initialize_registry()
    
    # Run audit
    audit = generate_audit()
    
    # Escalate critical issues
    critical = [a for a in audit.get("anomalies", []) if a["severity"] == "CRITICAL"]
    for anomaly in critical:
        escalate_to_supervisor(anomaly)
    
    print(f"[COORDINATOR] Audit complete.")
    print(f"  - Active scrapes: {audit['summary']['total_scrapes_active']}")
    print(f"  - Healthy: {audit['summary']['healthy']}")
    print(f"  - Warnings: {audit['summary']['warnings']}")
    print(f"  - Opportunities: {len(audit['opportunities'])}")
    
    return audit

if __name__ == "__main__":
    run_audit_cycle()
