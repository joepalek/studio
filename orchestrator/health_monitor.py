"""
STUDIO HEALTH MONITOR & ESCALATION ENGINE
Runs daily to detect and escalate issues:
- Silent failures (task ran, 0 assets produced)
- Blocked milestones (upstream dependencies not met)
- Missed deadlines
- Stuck projects (no progress in N days)
"""

import logging
from datetime import datetime, timedelta
from studio_orchestrator import StudioOrchestrator
from email_service import send_escalation_email

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


class StudioHealthMonitor:
    """Detect and escalate project health issues."""
    
    def __init__(self, db_path: str = "studio_projects.db"):
        self.orch = StudioOrchestrator(db_path)
    
    def run_daily_checks(self):
        """Execute all health checks and escalate issues."""
        logger.info("=== DAILY HEALTH CHECK ===")
        
        issues = []
        
        # 1. Check for silent failures
        issues.extend(self.check_silent_failures())
        
        # 2. Check for blocked projects
        issues.extend(self.check_blocked_projects())
        
        # 3. Check for missed deadlines
        issues.extend(self.check_missed_deadlines())
        
        # 4. Check for stalled projects
        issues.extend(self.check_stalled_projects())
        
        # 5. Auto-process intake queue
        self.process_new_projects()
        
        # 6. Send escalations if any
        if issues:
            logger.warning(f"Found {len(issues)} issues to escalate")
            for issue in issues:
                escalation_id = issue["escalation_id"]
                self.orch.mark_escalation_emailed(escalation_id)
            
            send_escalation_email(issues)
        else:
            logger.info("No issues found — all systems nominal")
        
        self.orch.close()
    
    def check_silent_failures(self) -> list:
        """
        Detect projects that ran but produced 0 assets in last 24h.
        Indicates tasks running but doing nothing.
        """
        issues = []
        cutoff = (datetime.now() - timedelta(hours=24)).isoformat()
        
        # Get all in-progress milestones
        milestones = self.orch.db.execute("""
            SELECT m.id, m.project_id, p.name, m.title, m.assigned_agent
            FROM milestones m
            JOIN projects p ON m.project_id = p.id
            WHERE m.status IN ('in_progress', 'pending')
            AND p.status = 'active'
        """).fetchall()
        
        for milestone in milestones:
            milestone_id, project_id, proj_name, milestone_title, agent = milestone
            
            # Check if any production logged for this project in last 24h
            production = self.orch.db.execute("""
                SELECT SUM(asset_count) FROM production_log
                WHERE project_id = ? AND timestamp > ?
            """, (project_id, cutoff)).fetchone()
            
            asset_count = production[0] or 0
            
            if asset_count == 0:
                # Check if the agent actually ran (via logs or task scheduler)
                # For now, flag any milestone with 0 production
                escalation_id = self.orch.create_escalation(
                    project_id=project_id,
                    milestone_id=milestone_id,
                    escalation_type="silent_fail",
                    description=f"Milestone '{milestone_title}' (agent: {agent}) ran but produced 0 assets in 24h",
                    severity="medium"
                )
                
                issues.append({
                    "escalation_id": escalation_id,
                    "type": "silent_fail",
                    "project": proj_name,
                    "milestone": milestone_title,
                    "agent": agent,
                    "severity": "medium"
                })
                
                logger.warning(f"Silent failure: {proj_name} → {milestone_title}")
        
        return issues
    
    def check_blocked_projects(self) -> list:
        """
        Detect projects blocked by upstream dependencies.
        """
        issues = []
        
        projects = self.orch.list_projects({"status": "active"})
        
        for project in projects:
            project_id = project["id"]
            
            # Get blocking projects
            blockers = self.orch.get_blocking_projects(project_id)
            
            if blockers and any(b["status"] != "complete" for b in blockers):
                # This project is blocked
                blocker_names = ", ".join(b["name"] for b in blockers if b["status"] != "complete")
                
                escalation_id = self.orch.create_escalation(
                    project_id=project_id,
                    escalation_type="blocked",
                    description=f"Project blocked by: {blocker_names}",
                    severity="high"
                )
                
                issues.append({
                    "escalation_id": escalation_id,
                    "type": "blocked",
                    "project": project["name"],
                    "blockers": blocker_names,
                    "severity": "high"
                })
                
                logger.warning(f"Blocked: {project['name']} (blocked by {blocker_names})")
        
        return issues
    
    def check_missed_deadlines(self) -> list:
        """
        Detect milestones with past target dates that aren't complete.
        """
        issues = []
        today = datetime.now().isoformat()[:10]
        
        past_due = self.orch.db.execute("""
            SELECT m.id, m.project_id, p.name, m.title, m.target_date, m.assigned_agent
            FROM milestones m
            JOIN projects p ON m.project_id = p.id
            WHERE m.status IN ('pending', 'in_progress')
            AND m.target_date < ?
            AND p.status = 'active'
        """, (today,)).fetchall()
        
        for milestone in past_due:
            milestone_id, project_id, proj_name, milestone_title, target_date, agent = milestone
            
            days_overdue = (datetime.now() - datetime.fromisoformat(target_date)).days
            
            escalation_id = self.orch.create_escalation(
                project_id=project_id,
                milestone_id=milestone_id,
                escalation_type="deadline_miss",
                description=f"Milestone '{milestone_title}' {days_overdue} days overdue (target: {target_date})",
                severity="high" if days_overdue > 7 else "medium"
            )
            
            issues.append({
                "escalation_id": escalation_id,
                "type": "deadline_miss",
                "project": proj_name,
                "milestone": milestone_title,
                "days_overdue": days_overdue,
                "agent": agent,
                "severity": "high" if days_overdue > 7 else "medium"
            })
            
            logger.warning(f"Overdue: {proj_name} → {milestone_title} ({days_overdue} days)")
        
        return issues
    
    def check_stalled_projects(self, days: int = 14) -> list:
        """
        Detect projects with no production activity for N days.
        """
        issues = []
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        
        projects = self.orch.list_projects({"status": "active"})
        
        for project in projects:
            project_id = project["id"]
            
            # Check for any production in last N days
            production = self.orch.db.execute("""
                SELECT COUNT(*) FROM production_log
                WHERE project_id = ? AND timestamp > ?
            """, (project_id, cutoff)).fetchone()[0]
            
            if production == 0:
                escalation_id = self.orch.create_escalation(
                    project_id=project_id,
                    escalation_type="silent_fail",  # Reuse type for stalled
                    description=f"No production activity in {days} days",
                    severity="low"
                )
                
                issues.append({
                    "escalation_id": escalation_id,
                    "type": "stalled",
                    "project": project["name"],
                    "days_stalled": days,
                    "severity": "low"
                })
                
                logger.info(f"Stalled: {project['name']} (no activity {days}d)")
        
        return issues
    
    def process_new_projects(self):
        """
        Auto-process intake queue items into projects.
        (Can be manual approval gate if needed)
        """
        queue = self.orch.get_intake_queue()
        
        if not queue:
            logger.info("No items in intake queue")
            return
        
        logger.info(f"Processing {len(queue)} intake items...")
        
        for item in queue:
            # Create project from intake item
            project_id = self.orch.add_project(
                name=item["title"],
                division=item["division"] or "Research",
                description=item["description"],
                priority=3,
                owner_agent="orchestrator",
                milestones=[
                    {
                        "title": "Project initialized",
                        "target_date": (datetime.now() + timedelta(days=7)).isoformat()[:10],
                        "agent": "orchestrator"
                    }
                ]
            )
            
            if project_id > 0:
                self.orch.process_intake(item["id"], project_id)
                logger.info(f"Intake → Project: {item['title']} (id={project_id})")


def main():
    """Run health check as standalone service."""
    monitor = StudioHealthMonitor()
    monitor.run_daily_checks()


if __name__ == "__main__":
    main()
