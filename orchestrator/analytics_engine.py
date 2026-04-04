"""
STUDIO ANALYTICS ENGINE
Production metrics, ROI analysis, trend detection, forecasting.

Answers:
  - Which agents are most productive?
  - What's the cost per asset by division?
  - Are deadlines trending better or worse?
  - Which projects are blocked most?
  - What's the team velocity?
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from collections import defaultdict
import statistics
from studio_orchestrator import StudioOrchestrator

logger = None  # Can be set by caller


class StudioAnalytics:
    """Production metrics and insights."""
    
    def __init__(self, db_path: str = "studio_projects.db"):
        self.orch = StudioOrchestrator(db_path)
        self.db = self.orch.db
    
    # ========================================================================
    # PRODUCTION METRICS
    # ========================================================================
    
    def get_production_summary(self, days: int = 30) -> Dict:
        """
        Get overall production stats for period.
        
        Returns:
            {
                "total_runs": int,
                "total_assets": int,
                "total_cost": float,
                "avg_assets_per_run": float,
                "agents_active": int,
                "asset_types": {asset_type: count}
            }
        """
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        
        # Overall stats
        stats = self.db.execute(f"""
            SELECT 
                COUNT(*) as runs,
                SUM(asset_count) as assets,
                SUM(cost_usd) as cost,
                COUNT(DISTINCT agent) as agents,
                COUNT(DISTINCT asset_type) as asset_types
            FROM production_log
            WHERE timestamp > '{cutoff}'
        """).fetchone()
        
        runs, assets, cost, agents, types = stats
        assets = assets or 0
        cost = cost or 0.0
        
        # Asset breakdown
        asset_breakdown = self.db.execute(f"""
            SELECT asset_type, SUM(asset_count) as count
            FROM production_log
            WHERE timestamp > '{cutoff}'
            GROUP BY asset_type
            ORDER BY count DESC
        """).fetchall()
        
        return {
            "period_days": days,
            "total_runs": runs or 0,
            "total_assets": assets,
            "total_cost_usd": cost,
            "avg_assets_per_run": assets / (runs or 1),
            "agents_active": agents or 0,
            "asset_types_count": types or 0,
            "asset_breakdown": {
                row[0]: row[1] for row in asset_breakdown
            }
        }
    
    def get_agent_productivity(self, days: int = 30) -> List[Dict]:
        """
        Rank agents by productivity.
        
        Returns:
            [
                {
                    "agent": str,
                    "runs": int,
                    "assets": int,
                    "cost": float,
                    "roi": assets/cost,
                    "avg_per_run": int
                }
            ]
        """
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        
        rows = self.db.execute(f"""
            SELECT 
                agent,
                COUNT(*) as runs,
                SUM(asset_count) as assets,
                SUM(cost_usd) as cost
            FROM production_log
            WHERE timestamp > '{cutoff}'
            GROUP BY agent
            ORDER BY assets DESC
        """).fetchall()
        
        results = []
        for agent, runs, assets, cost in rows:
            assets = assets or 0
            cost = cost or 0.0
            
            results.append({
                "agent": agent,
                "runs": runs or 0,
                "assets": assets,
                "cost_usd": cost,
                "roi": assets / (cost or 1),  # assets per dollar
                "avg_assets_per_run": assets / (runs or 1)
            })
        
        return results
    
    def get_division_metrics(self, days: int = 30) -> Dict[str, Dict]:
        """
        Production metrics by division.
        
        Returns:
            {
                "Commerce": {
                    "projects": int,
                    "assets": int,
                    "cost": float,
                    "active_milestone_count": int
                }
            }
        """
        results = {}
        
        divisions = self.db.execute("""
            SELECT DISTINCT division FROM projects
        """).fetchall()
        
        for div_row in divisions:
            division = div_row[0]
            
            # Get project IDs for this division
            project_ids = self.db.execute("""
                SELECT id FROM projects WHERE division = ?
            """, (division,)).fetchall()
            
            project_ids = [p[0] for p in project_ids]
            
            if not project_ids:
                continue
            
            # Get production for these projects
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()
            prod = self.db.execute(f"""
                SELECT SUM(asset_count), SUM(cost_usd)
                FROM production_log
                WHERE project_id IN ({','.join(str(id) for id in project_ids)})
                AND timestamp > '{cutoff}'
            """).fetchone()
            
            assets, cost = prod
            assets = assets or 0
            cost = cost or 0.0
            
            # Count active milestones
            active_milestones = self.db.execute("""
                SELECT COUNT(*) FROM milestones
                WHERE project_id IN ({})
                AND status IN ('pending', 'in_progress')
            """.format(','.join(str(id) for id in project_ids))).fetchone()[0]
            
            results[division] = {
                "projects": len(project_ids),
                "total_assets": assets,
                "total_cost": cost,
                "roi": assets / (cost or 1),
                "active_milestones": active_milestones
            }
        
        return results
    
    # ========================================================================
    # DEADLINE ANALYSIS
    # ========================================================================
    
    def get_deadline_trends(self, days: int = 90) -> Dict:
        """
        Analyze milestone deadline performance over time.
        
        Returns:
            {
                "on_time": int,
                "overdue": int,
                "completion_rate": float,
                "avg_days_late": float,
                "trend": "improving", "stable", "declining"
            }
        """
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        
        # Completed milestones
        completed = self.db.execute(f"""
            SELECT target_date, completed_date
            FROM milestones
            WHERE status = 'complete'
            AND completed_date IS NOT NULL
            AND completed_date > '{cutoff}'
        """).fetchall()
        
        on_time = 0
        overdue = 0
        days_late_list = []
        
        for target, completed_date in completed:
            if target and completed_date:
                target_dt = datetime.fromisoformat(target)
                completed_dt = datetime.fromisoformat(completed_date)
                
                days_diff = (completed_dt - target_dt).days
                
                if days_diff <= 0:
                    on_time += 1
                else:
                    overdue += 1
                    days_late_list.append(days_diff)
        
        total = on_time + overdue
        
        return {
            "period_days": days,
            "completed_milestones": total,
            "on_time": on_time,
            "overdue": overdue,
            "completion_rate": on_time / (total or 1),
            "avg_days_late": statistics.mean(days_late_list) if days_late_list else 0,
            "max_days_late": max(days_late_list) if days_late_list else 0
        }
    
    def get_overdue_milestones(self) -> List[Dict]:
        """
        Get all milestones past their target date.
        
        Returns:
            [
                {
                    "project": str,
                    "milestone": str,
                    "target_date": str,
                    "days_overdue": int,
                    "assigned_agent": str
                }
            ]
        """
        today = datetime.now().isoformat()[:10]
        
        rows = self.db.execute(f"""
            SELECT p.name, m.title, m.target_date, m.assigned_agent
            FROM milestones m
            JOIN projects p ON m.project_id = p.id
            WHERE m.status IN ('pending', 'in_progress')
            AND m.target_date < '{today}'
            ORDER BY m.target_date ASC
        """).fetchall()
        
        results = []
        for proj, milestone, target, agent in rows:
            if target:
                target_dt = datetime.fromisoformat(target)
                today_dt = datetime.fromisoformat(today)
                days_late = (today_dt - target_dt).days
                
                results.append({
                    "project": proj,
                    "milestone": milestone,
                    "target_date": target,
                    "days_overdue": days_late,
                    "assigned_agent": agent
                })
        
        return results
    
    # ========================================================================
    # DEPENDENCY ANALYSIS
    # ========================================================================
    
    def get_blocking_statistics(self) -> Dict:
        """
        Analyze project blocking patterns.
        
        Returns:
            {
                "blocked_projects": int,
                "most_common_blockers": [(project_name, count)],
                "critical_path": [project_names]  # longest dependency chain
            }
        """
        # Blocked projects
        blocked = self.db.execute("""
            SELECT COUNT(DISTINCT downstream_project_id)
            FROM dependencies d
            JOIN projects p ON d.upstream_project_id = p.id
            WHERE p.status != 'complete'
        """).fetchone()[0]
        
        # Most common blockers
        blockers = self.db.execute("""
            SELECT p.name, COUNT(*) as count
            FROM dependencies d
            JOIN projects p ON d.upstream_project_id = p.id
            WHERE p.status != 'complete'
            GROUP BY p.name
            ORDER BY count DESC
            LIMIT 5
        """).fetchall()
        
        return {
            "blocked_projects": blocked or 0,
            "most_common_blockers": [
                {"project": row[0], "blocks_count": row[1]}
                for row in blockers
            ]
        }
    
    # ========================================================================
    # FORECASTING
    # ========================================================================
    
    def forecast_completion(self, project_id: int, days_ahead: int = 30) -> Dict:
        """
        Forecast project completion based on velocity.
        
        Uses: (incomplete milestones / avg milestones per day) = days to complete
        """
        # Get incomplete milestones
        incomplete = self.db.execute("""
            SELECT COUNT(*) FROM milestones
            WHERE project_id = ? AND status != 'complete'
        """, (project_id,)).fetchone()[0]
        
        # Get historical completion rate
        cutoff = (datetime.now() - timedelta(days=90)).isoformat()
        completed_90d = self.db.execute(f"""
            SELECT COUNT(*) FROM milestones
            WHERE project_id = ? AND status = 'complete'
            AND completed_date > '{cutoff}'
        """, (project_id,)).fetchone()[0]
        
        # Estimate days to completion
        if completed_90d > 0:
            milestones_per_day = completed_90d / 90
            days_to_complete = incomplete / milestones_per_day if milestones_per_day > 0 else 999
        else:
            days_to_complete = 999  # Unknown
        
        estimated_completion = datetime.now() + timedelta(days=days_to_complete)
        
        return {
            "project_id": project_id,
            "incomplete_milestones": incomplete,
            "historical_velocity": completed_90d / 90,
            "estimated_days_to_complete": round(days_to_complete, 1),
            "estimated_completion_date": estimated_completion.isoformat()[:10]
        }
    
    # ========================================================================
    # COST ANALYSIS
    # ========================================================================
    
    def get_cost_breakdown(self, days: int = 30) -> Dict:
        """
        Break down costs by agent, asset type, and division.
        """
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        
        # By agent
        by_agent = self.db.execute(f"""
            SELECT agent, SUM(cost_usd)
            FROM production_log
            WHERE timestamp > '{cutoff}'
            GROUP BY agent
            ORDER BY cost DESC
        """).fetchall()
        
        # By asset type
        by_type = self.db.execute(f"""
            SELECT asset_type, SUM(cost_usd)
            FROM production_log
            WHERE timestamp > '{cutoff}'
            GROUP BY asset_type
            ORDER BY cost DESC
        """).fetchall()
        
        # Total
        total_cost = self.db.execute(f"""
            SELECT SUM(cost_usd) FROM production_log
            WHERE timestamp > '{cutoff}'
        """).fetchone()[0] or 0.0
        
        return {
            "period_days": days,
            "total_cost": total_cost,
            "by_agent": [
                {"agent": row[0], "cost": row[1]} for row in by_agent
            ],
            "by_asset_type": [
                {"asset_type": row[0], "cost": row[1]} for row in by_type
            ]
        }
    
    def close(self):
        """Close database connection."""
        self.orch.close()


# ============================================================================
# REPORTING
# ============================================================================

def generate_insights_report(db_path: str = "studio_projects.db") -> str:
    """
    Generate comprehensive insights report.
    """
    analytics = StudioAnalytics(db_path)
    
    report = "\n" + "="*80 + "\n"
    report += "STUDIO ANALYTICS REPORT\n"
    report += f"Generated: {datetime.now().isoformat()}\n"
    report += "="*80 + "\n"
    
    # Production summary
    prod = analytics.get_production_summary(30)
    report += f"\n📊 PRODUCTION (30 days)\n"
    report += f"  Total runs: {prod['total_runs']}\n"
    report += f"  Total assets: {prod['total_assets']}\n"
    report += f"  Total cost: ${prod['total_cost_usd']:.2f}\n"
    report += f"  ROI: {prod['total_assets'] / (prod['total_cost_usd'] or 1):.1f} assets/dollar\n"
    
    # Agent productivity
    report += f"\n🤖 TOP AGENTS (by assets)\n"
    agents = analytics.get_agent_productivity(30)
    for agent in agents[:5]:
        report += f"  • {agent['agent']}: {agent['assets']} assets (${agent['cost_usd']:.2f}, ROI={agent['roi']:.1f})\n"
    
    # Division metrics
    report += f"\n📂 DIVISIONS\n"
    divisions = analytics.get_division_metrics(30)
    for div, metrics in divisions.items():
        report += f"  • {div}: {metrics['total_assets']} assets, ${metrics['total_cost']:.2f}\n"
    
    # Deadline trends
    trends = analytics.get_deadline_trends(30)
    report += f"\n📅 DEADLINE PERFORMANCE (30 days)\n"
    report += f"  On-time: {trends['on_time']} ({trends['completion_rate']*100:.0f}%)\n"
    report += f"  Overdue: {trends['overdue']}\n"
    if trends['overdue'] > 0:
        report += f"  Avg days late: {trends['avg_days_late']:.1f}\n"
    
    # Blocking analysis
    blocking = analytics.get_blocking_statistics()
    report += f"\n⛔ BLOCKING PROJECTS\n"
    report += f"  Projects blocked: {blocking['blocked_projects']}\n"
    if blocking['most_common_blockers']:
        for blocker in blocking['most_common_blockers'][:3]:
            report += f"    • {blocker['project']} (blocks {blocker['blocks_count']})\n"
    
    # Cost breakdown
    costs = analytics.get_cost_breakdown(30)
    report += f"\n💰 COSTS\n"
    report += f"  Total: ${costs['total_cost']:.2f}\n"
    
    analytics.close()
    
    return report


if __name__ == "__main__":
    print(generate_insights_report())
