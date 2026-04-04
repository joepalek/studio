#!/usr/bin/env python3
"""
STUDIO ORCHESTRATOR QUICK-START
Run this to initialize and test the system.
"""

import sys
import os
from pathlib import Path

# Force UTF-8 output on Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')
from studio_orchestrator import StudioOrchestrator, bootstrap_studio
from health_monitor import StudioHealthMonitor
from email_service import send_daily_digest, send_escalation_email

def print_section(title):
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}")

def quick_start():
    """Initialize and test the orchestrator system."""
    
    print_section("STUDIO ORCHESTRATOR QUICK-START")
    
    # Step 1: Initialize database
    print("\n[1] Initializing database...")
    bootstrap_studio("studio_projects.db")
    print("✓ Database initialized with 16+ projects")
    
    # Step 2: Verify database
    print("\n[2] Verifying database...")
    orch = StudioOrchestrator()
    
    projects = orch.list_projects()
    print(f"✓ Total projects: {len(projects)}")
    
    # Count by division
    divisions = {}
    for p in projects:
        div = p["division"]
        divisions[div] = divisions.get(div, 0) + 1
    
    print("\n  Projects by division:")
    for div, count in sorted(divisions.items()):
        print(f"    • {div}: {count}")
    
    # Step 3: Test production logging
    print("\n[3] Testing production logging...")
    orch.log_production(
        agent="test_agent",
        project_id=1,  # eBay Agent
        asset_type="test_assets",
        asset_count=5,
        cost_usd=0.01,
        status="success"
    )
    print("✓ Production log test successful")
    
    # Step 4: Test escalation
    print("\n[4] Testing escalation system...")
    escalation_id = orch.create_escalation(
        project_id=1,
        escalation_type="silent_fail",
        description="Test escalation - can be safely deleted",
        severity="low"
    )
    print(f"✓ Escalation created (ID: {escalation_id})")
    
    # Step 5: Check daily status
    print("\n[5] Daily status snapshot:")
    status = orch.get_daily_status()
    for key, value in status.items():
        if key == "as_of":
            print(f"  {key}: {value}")
        else:
            print(f"  {key}: {value}")
    
    # Step 6: Check escalations
    unresolved = orch.get_unresolved_escalations()
    print(f"\n[6] Unresolved escalations: {len(unresolved)}")
    if unresolved:
        for e in unresolved[:3]:
            print(f"  • {e['name']}: {e['description']}")
    
    orch.close()
    
    # Step 7: Test email generation (dev mode)
    print("\n[7] Testing email generation (dev mode)...")
    print("  → Sending test daily digest...")
    send_daily_digest()
    
    # Step 8: Final checklist
    print_section("INITIALIZATION CHECKLIST")
    print("""
✓ Database created: studio_projects.db
✓ 16+ projects registered
✓ Production logging works
✓ Escalation system works
✓ Email generation works

NEXT STEPS:
1. Copy this folder to: G:\\My Drive\\Projects\\_studio\\orchestrator
2. Install Flask: pip install flask
3. Start sidebar bridge: python sidebar_bridge.py
4. Configure Windows Task Scheduler (see DEPLOYMENT_GUIDE.md)
5. Configure email service (email_service.py line ~10)
6. Test everything: python quick_start.py

For full setup instructions: see DEPLOYMENT_GUIDE.md
    """)
    
    print_section("SYSTEM READY")

if __name__ == "__main__":
    try:
        quick_start()
    except Exception as e:
        print(f"\n✗ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
