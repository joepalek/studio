"""
STUDIO TESTING & DEBUGGING UTILITIES
Integration tests, data generation, system validation.

Use for:
  - Verify system is working correctly
  - Generate test data
  - Simulate agent failures
  - Debug database issues
"""

import random
from datetime import datetime, timedelta
from studio_orchestrator import StudioOrchestrator
from agent_framework import StudioAgent


class StudioTestSuite:
    """
    Comprehensive testing utilities for studio system.
    """
    
    def __init__(self, db_path: str = "studio_projects.db"):
        self.db_path = db_path
        self.orch = StudioOrchestrator(db_path)
    
    # ========================================================================
    # DATABASE VALIDATION
    # ========================================================================
    
    def validate_database(self) -> dict:
        """
        Comprehensive database integrity check.
        
        Returns:
            {
                "status": "healthy" or "issues_found",
                "projects": int,
                "milestones": int,
                "production_records": int,
                "escalations": int,
                "integrity_checks": [
                    {"check": str, "result": bool, "details": str}
                ]
            }
        """
        checks = []
        
        # Count tables
        projects = self.orch.db.execute(
            "SELECT COUNT(*) FROM projects"
        ).fetchone()[0]
        
        milestones = self.orch.db.execute(
            "SELECT COUNT(*) FROM milestones"
        ).fetchone()[0]
        
        production = self.orch.db.execute(
            "SELECT COUNT(*) FROM production_log"
        ).fetchone()[0]
        
        escalations = self.orch.db.execute(
            "SELECT COUNT(*) FROM escalations"
        ).fetchone()[0]
        
        # Check 1: Foreign key integrity
        orphan_milestones = self.orch.db.execute("""
            SELECT COUNT(*) FROM milestones m
            WHERE NOT EXISTS (SELECT 1 FROM projects WHERE id = m.project_id)
        """).fetchone()[0]
        
        checks.append({
            "check": "Orphan milestones (FK integrity)",
            "result": orphan_milestones == 0,
            "details": f"{orphan_milestones} orphan milestones found" if orphan_milestones > 0 else "✓ No orphans"
        })
        
        # Check 2: Duplicate project names
        dupes = self.orch.db.execute("""
            SELECT name, COUNT(*) as count FROM projects
            GROUP BY name HAVING count > 1
        """).fetchall()
        
        checks.append({
            "check": "Duplicate project names",
            "result": len(dupes) == 0,
            "details": f"{len(dupes)} duplicate names" if dupes else "✓ No duplicates"
        })
        
        # Check 3: Invalid milestone statuses
        invalid_statuses = self.orch.db.execute("""
            SELECT COUNT(*) FROM milestones
            WHERE status NOT IN ('pending', 'in_progress', 'blocked', 'complete')
        """).fetchone()[0]
        
        checks.append({
            "check": "Invalid milestone statuses",
            "result": invalid_statuses == 0,
            "details": f"{invalid_statuses} invalid statuses" if invalid_statuses > 0 else "✓ All valid"
        })
        
        # Check 4: Projects with no milestones
        no_milestones = self.orch.db.execute("""
            SELECT COUNT(*) FROM projects p
            WHERE NOT EXISTS (SELECT 1 FROM milestones WHERE project_id = p.id)
        """).fetchone()[0]
        
        checks.append({
            "check": "Projects without milestones",
            "result": True,  # Not necessarily bad
            "details": f"{no_milestones} projects have no milestones"
        })
        
        # Summary
        all_pass = all(c["result"] for c in checks)
        
        return {
            "status": "healthy" if all_pass else "issues_found",
            "projects": projects,
            "milestones": milestones,
            "production_records": production,
            "escalations": escalations,
            "integrity_checks": checks
        }
    
    # ========================================================================
    # TEST DATA GENERATION
    # ========================================================================
    
    def generate_test_production_data(self, days: int = 30, records_per_day: int = 5):
        """
        Generate realistic test production data.
        
        Args:
            days: How many days back to generate
            records_per_day: Approx records per day
        """
        agents = ["ebay_agent", "game_archaeology_agent", "art_department", 
                  "job_discovery_agent", "ai_intel_agent"]
        asset_types = ["listings", "images", "digest_sent", "sources_found", 
                       "jobs_discovered"]
        
        start_date = datetime.now() - timedelta(days=days)
        
        for day in range(days):
            current_date = start_date + timedelta(days=day)
            
            for _ in range(records_per_day):
                self.orch.log_production(
                    agent=random.choice(agents),
                    project_id=random.randint(1, 17),
                    asset_type=random.choice(asset_types),
                    asset_count=random.randint(1, 50),
                    cost_usd=round(random.random() * 5, 2),
                    status=random.choice(["success", "partial"]),
                    details={"test_data": True}
                )
        
        print(f"✓ Generated {days * records_per_day} test production records")
    
    def generate_test_escalations(self, count: int = 10):
        """
        Generate test escalations for each severity.
        """
        for i in range(count):
            self.orch.create_escalation(
                project_id=random.randint(1, 17),
                escalation_type=random.choice(["blocked", "silent_fail", "deadline_miss"]),
                description=f"Test escalation #{i+1}",
                severity=random.choice(["low", "medium", "high"])
            )
        
        print(f"✓ Generated {count} test escalations")
    
    # ========================================================================
    # SIMULATION & FAILURE TESTING
    # ========================================================================
    
    def simulate_silent_failure(self, project_id: int):
        """
        Simulate agent running but producing 0 assets (silent failure).
        """
        # Create an in_progress milestone
        milestone_id = self.orch.db.execute(
            "SELECT id FROM milestones WHERE project_id = ? AND status IN ('pending', 'in_progress') LIMIT 1",
            (project_id,)
        ).fetchone()
        
        if milestone_id:
            # Health monitor will detect this as silent failure
            self.orch.create_escalation(
                project_id=project_id,
                milestone_id=milestone_id[0],
                escalation_type="silent_fail",
                description="Simulated silent failure (0 assets produced)",
                severity="medium"
            )
            print(f"✓ Simulated silent failure on project {project_id}")
    
    def simulate_deadline_miss(self, project_id: int):
        """
        Set a milestone's target date to the past (to trigger deadline miss).
        """
        past_date = (datetime.now() - timedelta(days=5)).isoformat()[:10]
        
        self.orch.db.execute(
            "UPDATE milestones SET target_date = ? WHERE project_id = ? LIMIT 1",
            (past_date, project_id)
        )
        self.orch.db.commit()
        
        print(f"✓ Simulated deadline miss on project {project_id} (target: {past_date})")
    
    # ========================================================================
    # SYSTEM DIAGNOSTICS
    # ========================================================================
    
    def run_diagnostics(self) -> str:
        """
        Run full system diagnostic and return report.
        """
        report = "\n" + "="*80 + "\n"
        report += "STUDIO SYSTEM DIAGNOSTICS\n"
        report += f"Timestamp: {datetime.now().isoformat()}\n"
        report += "="*80 + "\n"
        
        # Database validation
        report += "\n📊 DATABASE VALIDATION\n"
        validation = self.validate_database()
        report += f"Status: {validation['status']}\n"
        report += f"Projects: {validation['projects']}\n"
        report += f"Milestones: {validation['milestones']}\n"
        report += f"Production records: {validation['production_records']}\n"
        report += f"Escalations: {validation['escalations']}\n"
        
        report += "\nIntegrity checks:\n"
        for check in validation['integrity_checks']:
            status_icon = "✓" if check['result'] else "✗"
            report += f"  {status_icon} {check['check']}: {check['details']}\n"
        
        # Project status distribution
        report += "\n📂 PROJECT STATUS\n"
        status_dist = self.orch.db.execute("""
            SELECT status, COUNT(*) FROM projects GROUP BY status
        """).fetchall()
        
        for status, count in status_dist:
            report += f"  {status}: {count}\n"
        
        # Escalation summary
        report += "\n⛔ ESCALATIONS\n"
        escalations = self.orch.get_unresolved_escalations()
        report += f"Unresolved: {len(escalations)}\n"
        
        if escalations:
            severity_count = {}
            for e in escalations:
                sev = e['severity']
                severity_count[sev] = severity_count.get(sev, 0) + 1
            
            for severity, count in severity_count.items():
                report += f"  {severity}: {count}\n"
        
        # Recent production
        report += "\n🏭 RECENT PRODUCTION (last 24h)\n"
        cutoff = (datetime.now() - timedelta(hours=24)).isoformat()
        recent = self.orch.db.execute(f"""
            SELECT agent, SUM(asset_count) as total
            FROM production_log
            WHERE timestamp > '{cutoff}'
            GROUP BY agent
        """).fetchall()
        
        if recent:
            for agent, total in recent:
                report += f"  {agent}: {total} assets\n"
        else:
            report += "  (no production in last 24h)\n"
        
        report += "\n" + "="*80 + "\n"
        
        return report
    
    # ========================================================================
    # CLEANUP & RESET
    # ========================================================================
    
    def clear_test_data(self):
        """
        Remove all test/production data but keep projects.
        WARNING: This is destructive.
        """
        self.orch.db.execute("DELETE FROM production_log WHERE details LIKE '%test_data%'")
        self.orch.db.execute("DELETE FROM escalations WHERE description LIKE '%Test%'")
        self.orch.db.commit()
        print("✓ Cleared test data")
    
    def reset_database(self):
        """
        DANGEROUS: Reset entire database to initial state.
        Use only for testing!
        """
        import os
        db_path = Path(self.db_path)
        
        if db_path.exists():
            os.remove(db_path)
            print(f"✓ Deleted {db_path}")
        
        # Reinitialize
        from studio_orchestrator import bootstrap_studio
        bootstrap_studio(str(db_path))
        print("✓ Database reset to initial state")
    
    def close(self):
        """Close database connection."""
        self.orch.close()


# ============================================================================
# COMMAND-LINE INTERFACE
# ============================================================================

def main():
    """Run diagnostics and tests."""
    import sys
    
    if len(sys.argv) < 2:
        print("""
STUDIO TEST SUITE

Usage:
  python test_suite.py validate          # Validate database integrity
  python test_suite.py diagnostics       # Full system diagnostics
  python test_suite.py generate [days]   # Generate test production data
  python test_suite.py simulate_failure <project_id>  # Simulate silent failure
  python test_suite.py simulate_deadline <project_id> # Simulate deadline miss
  python test_suite.py clear_tests       # Clear test data (keep projects)
  python test_suite.py reset             # DANGEROUS: Reset entire DB
        """)
        sys.exit(1)
    
    command = sys.argv[1]
    suite = StudioTestSuite()
    
    if command == "validate":
        result = suite.validate_database()
        print(f"\n✓ Status: {result['status']}")
        for check in result['integrity_checks']:
            icon = "✓" if check['result'] else "✗"
            print(f"{icon} {check['check']}: {check['details']}")
    
    elif command == "diagnostics":
        print(suite.run_diagnostics())
    
    elif command == "generate":
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        suite.generate_test_production_data(days)
        suite.generate_test_escalations(5)
    
    elif command == "simulate_failure":
        if len(sys.argv) < 3:
            print("Usage: python test_suite.py simulate_failure <project_id>")
            sys.exit(1)
        suite.simulate_silent_failure(int(sys.argv[2]))
    
    elif command == "simulate_deadline":
        if len(sys.argv) < 3:
            print("Usage: python test_suite.py simulate_deadline <project_id>")
            sys.exit(1)
        suite.simulate_deadline_miss(int(sys.argv[2]))
    
    elif command == "clear_tests":
        suite.clear_test_data()
    
    elif command == "reset":
        response = input("WARNING: This will reset the entire database. Continue? (yes/no): ")
        if response.lower() == "yes":
            suite.reset_database()
        else:
            print("Cancelled.")
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
    
    suite.close()


from pathlib import Path

if __name__ == "__main__":
    main()
