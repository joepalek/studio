"""
EMAIL SERVICE
Sends daily digests, weekly reports, and escalation alerts to joedealsonline@gmail.com
"""

import smtplib
import json
from datetime import datetime
from typing import List, Dict
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from studio_orchestrator import StudioOrchestrator

# Configuration (move to .env or config file)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "studio-orchestrator@anthropic.test"  # Or use your actual email
RECIPIENT_EMAIL = "joedealsonline@gmail.com"
SMTP_PASSWORD = None  # Set via environment variable or OAuth

# For development/testing: use a mock email service


def send_escalation_email(issues: List[Dict]):
    """
    Send high-priority escalation email for blocks, silent failures, deadline misses.
    """
    if not issues:
        return
    
    # Group by severity
    high = [i for i in issues if i.get("severity") == "high"]
    medium = [i for i in issues if i.get("severity") == "medium"]
    low = [i for i in issues if i.get("severity") == "low"]
    
    body = """
🚨 STUDIO ESCALATION ALERT 🚨

Your studio has detected active issues that need attention.

"""
    
    if high:
        body += f"\n⛔ HIGH PRIORITY ({len(high)})\n"
        body += "-" * 60 + "\n"
        for issue in high:
            if issue["type"] == "blocked":
                body += f"  • {issue['project']} is BLOCKED by: {issue['blockers']}\n"
            elif issue["type"] == "deadline_miss":
                body += f"  • {issue['project']} → {issue['milestone']}\n"
                body += f"    {issue['days_overdue']} days overdue (assigned: {issue.get('agent', '?')})\n"
    
    if medium:
        body += f"\n⚠️  MEDIUM PRIORITY ({len(medium)})\n"
        body += "-" * 60 + "\n"
        for issue in medium:
            if issue["type"] == "silent_fail":
                body += f"  • {issue['project']} → {issue.get('milestone', 'unknown')}\n"
                body += f"    Ran but produced 0 assets in 24h (agent: {issue.get('agent', '?')})\n"
            elif issue["type"] == "deadline_miss":
                body += f"  • {issue['project']} → {issue['milestone']}\n"
                body += f"    {issue['days_overdue']} days overdue\n"
    
    if low:
        body += f"\n💬 LOW PRIORITY ({len(low)})\n"
        body += "-" * 60 + "\n"
        for issue in low:
            if issue["type"] == "stalled":
                body += f"  • {issue['project']} has no activity for {issue['days_stalled']} days\n"
    
    body += """

NEXT STEPS:
1. Review each escalation in your sidebar project ticker
2. For blocked projects: check upstream dependencies
3. For silent failures: verify agent configuration and logs
4. For overdue milestones: adjust timeline or reassign work

Monitor dashboard: http://localhost:8765/ (sidebar)
Full report: Check studio_projects.db for detailed history

---
Studio Orchestrator v2
"""
    
    _send_email(
        recipient=RECIPIENT_EMAIL,
        subject=f"🚨 STUDIO ESCALATION ({len(high)} HIGH, {len(medium)} MEDIUM)",
        body=body
    )


def send_daily_digest():
    """
    Send daily status digest to Joe.
    Shows: active projects, due this week, production today, escalations.
    """
    orch = StudioOrchestrator()
    status = orch.get_daily_status()
    
    body = """
📊 STUDIO DAILY DIGEST
""" + status["as_of"] + """

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PROJECTS STATUS
  Active: """ + str(status["projects_active"]) + """
  Blocked: """ + str(status["projects_blocked"]) + """
  Complete: """ + str(status["projects_complete"]) + """

TODAY'S PRODUCTION
  Runs: """ + str(status["production_runs_today"]) + """
  Assets: """ + str(status["assets_produced_today"]) + """
  Cost: $""" + f"{status['cost_today_usd']:.2f}" + """

THIS WEEK
  Milestones due: """ + str(status["milestones_due_week"]) + """

ALERTS
  Escalations: """ + str(status["unresolved_escalations"]) + """
  Intake queue: """ + str(status["intake_pending"]) + """

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

View full status: http://localhost:8765/
Database: studio_projects.db

"""
    
    orch.close()
    
    _send_email(
        recipient=RECIPIENT_EMAIL,
        subject="📊 Studio Daily Digest",
        body=body
    )


def send_weekly_report():
    """
    Send comprehensive weekly accountability report.
    """
    orch = StudioOrchestrator()
    weekly = orch.get_weekly_status()
    
    body = """
📈 STUDIO WEEKLY ACCOUNTABILITY REPORT
""" + weekly["period"] + """

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PROJECT SNAPSHOT
  Active: """ + str(weekly["projects_active"]) + """
  Blocked: """ + str(weekly["projects_blocked"]) + """

"""
    
    if weekly["blocked_details"]:
        body += "\nBLOCKED PROJECTS:\n"
        for p in weekly["blocked_details"]:
            body += f"  • {p['name']} ({p['status']})\n"
    
    body += "\nMILESTONES DUE THIS WEEK:\n"
    if weekly["milestones_due_this_week"]:
        for m in weekly["milestones_due_this_week"]:
            body += f"  • {m['project']} → {m['milestone']}\n"
            body += f"    Due: {m['date']} | Agent: {m['agent']}\n"
    else:
        body += "  (none)\n"
    
    body += "\nPRODUCTION SUMMARY:\n"
    if weekly["production_summary"]:
        for p in weekly["production_summary"]:
            body += f"  • {p['agent']} {p['asset_type']}: {p['total']} assets (${p['cost']:.2f})\n"
    else:
        body += "  (no production this week)\n"
    
    if weekly["escalations_unresolved"]:
        body += f"\nACTIVE ESCALATIONS ({len(weekly['escalations_unresolved'])}):\n"
        for e in weekly["escalations_unresolved"]:
            body += f"  • [{e['escalation_type']}] {e['name']}: {e['description']}\n"
    
    body += """

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Database: studio_projects.db
Dashboard: http://localhost:8765/

"""
    
    orch.close()
    
    _send_email(
        recipient=RECIPIENT_EMAIL,
        subject="📈 Studio Weekly Accountability Report",
        body=body
    )


def _send_email(recipient: str, subject: str, body: str):
    """
    Internal helper to send email.
    
    For development: logs to console instead of sending.
    For production: use SMTP to send via Gmail.
    """
    
    # DEV MODE: Print to console
    print("\n" + "="*80)
    print(f"EMAIL TO: {recipient}")
    print(f"SUBJECT: {subject}")
    print("="*80)
    print(body)
    print("="*80 + "\n")
    
    # PROD MODE: Uncomment below and set SMTP_PASSWORD
    # try:
    #     msg = MIMEMultipart()
    #     msg["From"] = SENDER_EMAIL
    #     msg["To"] = recipient
    #     msg["Subject"] = subject
    #     msg.attach(MIMEText(body, "plain"))
    #     
    #     with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
    #         server.starttls()
    #         server.login(SENDER_EMAIL, SMTP_PASSWORD)
    #         server.send_message(msg)
    #     
    #     print(f"✓ Email sent to {recipient}")
    # except Exception as e:
    #     print(f"✗ Failed to send email: {e}")


if __name__ == "__main__":
    # Test email generation
    print("\n--- TESTING EMAIL GENERATION ---\n")
    send_daily_digest()
    send_weekly_report()
    
    # Test escalation email
    test_issues = [
        {
            "escalation_id": 1,
            "type": "blocked",
            "project": "Sentinel Viewer",
            "blockers": "Sentinel Core, API schema",
            "severity": "high"
        },
        {
            "escalation_id": 2,
            "type": "silent_fail",
            "project": "Game Archaeology",
            "milestone": "Weekly crawler operational",
            "agent": "game_archaeology_agent",
            "severity": "medium"
        },
        {
            "escalation_id": 3,
            "type": "deadline_miss",
            "project": "eBay Agent",
            "milestone": "Push 40 listings",
            "days_overdue": 5,
            "agent": "ebay_agent",
            "severity": "high"
        }
    ]
    
    send_escalation_email(test_issues)
