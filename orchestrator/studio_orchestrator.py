"""
STUDIO ORCHESTRATOR v2
Single source of truth for all studio projects, milestones, dependencies, and production tracking.
Replaces manual project tracking with automated, queryable state.
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


class StudioOrchestrator:
    """Central project registry and orchestration engine."""
    
    def __init__(self, db_path: str = "studio_projects.db"):
        self.db_path = db_path
        self.db = sqlite3.connect(db_path)
        self.db.row_factory = sqlite3.Row
        self.create_schema()
        logger.info(f"Orchestrator initialized: {db_path}")
    
    def create_schema(self):
        """Create all tables for project tracking."""
        self.db.executescript("""
        -- Projects: top-level containers
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            division TEXT NOT NULL,
            description TEXT,
            phase TEXT CHECK(phase IN ('ideation', 'development', 'production', 'maintenance', 'complete')),
            priority INTEGER DEFAULT 3,
            owner_agent TEXT,
            created_date TEXT DEFAULT CURRENT_TIMESTAMP,
            target_completion TEXT,
            status TEXT CHECK(status IN ('active', 'paused', 'blocked', 'complete')) DEFAULT 'active',
            tags TEXT,  -- JSON array: ["revenue", "infrastructure", "content"]
            metadata TEXT  -- JSON: custom fields per project
        );
        
        -- Milestones: measurable goals within projects
        CREATE TABLE IF NOT EXISTS milestones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            target_date TEXT,
            status TEXT CHECK(status IN ('pending', 'in_progress', 'blocked', 'complete')) DEFAULT 'pending',
            assigned_agent TEXT,
            completed_date TEXT,
            FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
        );
        
        -- Dependencies: which project blocks/feeds which
        CREATE TABLE IF NOT EXISTS dependencies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            upstream_project_id INTEGER NOT NULL,
            downstream_project_id INTEGER NOT NULL,
            relationship TEXT CHECK(relationship IN ('requires_output', 'blocks', 'feeds_into')),
            created_date TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(upstream_project_id) REFERENCES projects(id),
            FOREIGN KEY(downstream_project_id) REFERENCES projects(id),
            UNIQUE(upstream_project_id, downstream_project_id)
        );
        
        -- Production log: asset tracking per agent/project
        CREATE TABLE IF NOT EXISTS production_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent TEXT NOT NULL,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            project_id INTEGER,
            asset_type TEXT NOT NULL,
            asset_count INTEGER,
            cost_usd REAL DEFAULT 0,
            status TEXT CHECK(status IN ('success', 'partial', 'failed')) DEFAULT 'success',
            details TEXT,  -- JSON for extra context
            FOREIGN KEY(project_id) REFERENCES projects(id)
        );
        
        -- Escalations: blocks and alerts
        CREATE TABLE IF NOT EXISTS escalations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_date TEXT DEFAULT CURRENT_TIMESTAMP,
            resolved_date TEXT,
            project_id INTEGER NOT NULL,
            milestone_id INTEGER,
            escalation_type TEXT CHECK(escalation_type IN ('blocked', 'silent_fail', 'deadline_miss')),
            description TEXT,
            severity TEXT CHECK(severity IN ('low', 'medium', 'high')) DEFAULT 'medium',
            emailed BOOLEAN DEFAULT 0,
            FOREIGN KEY(project_id) REFERENCES projects(id),
            FOREIGN KEY(milestone_id) REFERENCES milestones(id)
        );
        
        -- Auto-intake: new projects discovered from GitHub, folders, etc.
        CREATE TABLE IF NOT EXISTS intake_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            discovered_date TEXT DEFAULT CURRENT_TIMESTAMP,
            source TEXT,  -- "github_issue", "folder_created", "manual"
            source_id TEXT UNIQUE,
            title TEXT NOT NULL,
            description TEXT,
            division TEXT,
            processed BOOLEAN DEFAULT 0,
            project_id INTEGER,
            FOREIGN KEY(project_id) REFERENCES projects(id)
        );
        
        -- Create indices for common queries
        CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
        CREATE INDEX IF NOT EXISTS idx_projects_division ON projects(division);
        CREATE INDEX IF NOT EXISTS idx_milestones_project ON milestones(project_id);
        CREATE INDEX IF NOT EXISTS idx_milestones_status ON milestones(status);
        CREATE INDEX IF NOT EXISTS idx_production_log_project ON production_log(project_id);
        CREATE INDEX IF NOT EXISTS idx_production_log_timestamp ON production_log(timestamp);
        CREATE INDEX IF NOT EXISTS idx_escalations_resolved ON escalations(resolved_date);
        """)
        self.db.commit()
        logger.info("Database schema verified")
    
    # ============================================================================
    # PROJECT MANAGEMENT
    # ============================================================================
    
    def add_project(
        self,
        name: str,
        division: str,
        milestones: List[Dict],
        description: str = "",
        priority: int = 3,
        target_date: Optional[str] = None,
        owner_agent: str = "orchestrator",
        tags: List[str] = None
    ) -> int:
        """
        Register a new project with milestones.
        
        Args:
            name: Project name (unique)
            division: "Commerce", "Content", "Infrastructure", "Research", "Sentinel Suite"
            milestones: List of {"title": str, "target_date": str, "agent": str, "description": str}
            description: Full project description
            priority: 1-5 (1=urgent, 5=backlog)
            target_date: ISO date string
            owner_agent: Which agent owns this
            tags: ["revenue", "infrastructure", "content", "ml"]
        
        Returns:
            project_id
        """
        tags = tags or []
        try:
            cursor = self.db.execute(
                """INSERT INTO projects 
                (name, division, description, phase, priority, owner_agent, target_completion, tags, status)
                VALUES (?, ?, ?, 'development', ?, ?, ?, ?, 'active')""",
                (name, division, description, priority, owner_agent, target_date, json.dumps(tags))
            )
            project_id = cursor.lastrowid
            
            # Add milestones
            for milestone in milestones:
                self.db.execute(
                    """INSERT INTO milestones 
                    (project_id, title, description, target_date, status, assigned_agent)
                    VALUES (?, ?, ?, ?, 'pending', ?)""",
                    (
                        project_id,
                        milestone.get("title"),
                        milestone.get("description", ""),
                        milestone.get("target_date"),
                        milestone.get("agent", owner_agent)
                    )
                )
            
            self.db.commit()
            logger.info(f"Project added: {name} (id={project_id})")
            return project_id
        
        except sqlite3.IntegrityError as e:
            logger.error(f"Project '{name}' already exists: {e}")
            return -1
    
    def update_project_status(self, project_id: int, status: str):
        """Update project status: active, paused, blocked, complete."""
        self.db.execute("UPDATE projects SET status = ? WHERE id = ?", (status, project_id))
        self.db.commit()
        logger.info(f"Project {project_id} status → {status}")
    
    def list_projects(self, filters: Optional[Dict] = None) -> List[Dict]:
        """
        List all projects with optional filters.
        
        filters: {"status": "active", "division": "Commerce", "priority_max": 2}
        """
        query = "SELECT * FROM projects WHERE 1=1"
        params = []
        
        if filters:
            if "status" in filters:
                query += " AND status = ?"
                params.append(filters["status"])
            if "division" in filters:
                query += " AND division = ?"
                params.append(filters["division"])
            if "priority_max" in filters:
                query += " AND priority <= ?"
                params.append(filters["priority_max"])
        
        rows = self.db.execute(query + " ORDER BY priority ASC, created_date DESC", params).fetchall()
        return [dict(row) for row in rows]
    
    # ============================================================================
    # DEPENDENCIES
    # ============================================================================
    
    def add_dependency(self, upstream_id: int, downstream_id: int, relationship: str = "requires_output"):
        """
        Define dependency: downstream_id needs output from upstream_id.
        
        relationship: "requires_output", "blocks", "feeds_into"
        """
        try:
            self.db.execute(
                """INSERT INTO dependencies (upstream_project_id, downstream_project_id, relationship)
                VALUES (?, ?, ?)""",
                (upstream_id, downstream_id, relationship)
            )
            self.db.commit()
            logger.info(f"Dependency: {upstream_id} {relationship} → {downstream_id}")
        except sqlite3.IntegrityError:
            logger.warning(f"Dependency already exists: {upstream_id} → {downstream_id}")
    
    def get_blocking_projects(self, project_id: int) -> List[Dict]:
        """Which projects are blocking this one?"""
        rows = self.db.execute("""
            SELECT p.id, p.name, p.division, p.status
            FROM projects p
            JOIN dependencies d ON p.id = d.upstream_project_id
            WHERE d.downstream_project_id = ?
            AND p.status != 'complete'
        """, (project_id,)).fetchall()
        return [dict(row) for row in rows]
    
    def get_dependent_projects(self, project_id: int) -> List[Dict]:
        """What projects depend on this one's output?"""
        rows = self.db.execute("""
            SELECT p.id, p.name, p.division, p.status
            FROM projects p
            JOIN dependencies d ON p.id = d.downstream_project_id
            WHERE d.upstream_project_id = ?
        """, (project_id,)).fetchall()
        return [dict(row) for row in rows]
    
    # ============================================================================
    # PRODUCTION TRACKING
    # ============================================================================
    
    def log_production(
        self,
        agent: str,
        project_id: int,
        asset_type: str,
        asset_count: int = 1,
        cost_usd: float = 0.0,
        status: str = "success",
        details: Optional[Dict] = None
    ):
        """
        Agent publishes work. Automatically:
        - Records asset production
        - Marks milestone progress
        - Unblocks dependent projects
        """
        self.db.execute(
            """INSERT INTO production_log 
            (agent, project_id, asset_type, asset_count, cost_usd, status, details)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (agent, project_id, asset_type, asset_count, cost_usd, status, json.dumps(details or {}))
        )
        
        # If assets produced, mark next milestone as in_progress
        if asset_count > 0 and status in ("success", "partial"):
            next_milestone = self.db.execute(
                """SELECT id FROM milestones 
                WHERE project_id = ? AND status = 'pending'
                ORDER BY target_date ASC LIMIT 1""",
                (project_id,)
            ).fetchone()
            
            if next_milestone:
                self.db.execute(
                    "UPDATE milestones SET status = 'in_progress' WHERE id = ?",
                    (next_milestone[0],)
                )
        
        self.db.commit()
        logger.info(f"Production logged: {agent} → {project_id} (+{asset_count} {asset_type})")
    
    def get_project_production(self, project_id: int, days: int = 30) -> List[Dict]:
        """Get all production for a project in last N days."""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        rows = self.db.execute(
            """SELECT agent, asset_type, SUM(asset_count) as total_count, 
                      SUM(cost_usd) as total_cost, COUNT(*) as runs
               FROM production_log
               WHERE project_id = ? AND timestamp > ?
               GROUP BY agent, asset_type""",
            (project_id, cutoff)
        ).fetchall()
        return [dict(row) for row in rows]
    
    def check_silent_failures(self) -> List[int]:
        """
        Identify projects that ran but produced zero assets in last 24h.
        Returns list of project IDs.
        """
        cutoff = (datetime.now() - timedelta(hours=24)).isoformat()
        
        silent_projects = self.db.execute("""
            SELECT DISTINCT m.project_id
            FROM milestones m
            WHERE m.status IN ('in_progress', 'pending')
            AND NOT EXISTS (
                SELECT 1 FROM production_log
                WHERE project_id = m.project_id
                AND timestamp > ?
                AND asset_count > 0
            )
        """, (cutoff,)).fetchall()
        
        return [row[0] for row in silent_projects]
    
    # ============================================================================
    # ESCALATIONS
    # ============================================================================
    
    def create_escalation(
        self,
        project_id: int,
        escalation_type: str,
        description: str,
        milestone_id: Optional[int] = None,
        severity: str = "medium"
    ) -> int:
        """
        Create escalation for: blocked, silent_fail, deadline_miss
        
        Returns: escalation_id
        """
        cursor = self.db.execute(
            """INSERT INTO escalations 
            (project_id, milestone_id, escalation_type, description, severity)
            VALUES (?, ?, ?, ?, ?)""",
            (project_id, milestone_id, escalation_type, description, severity)
        )
        self.db.commit()
        escalation_id = cursor.lastrowid
        logger.warning(f"Escalation created ({severity}): {escalation_type} on project {project_id}")
        return escalation_id
    
    def get_unresolved_escalations(self) -> List[Dict]:
        """Get all active escalations."""
        rows = self.db.execute("""
            SELECT e.*, p.name, p.division, m.title
            FROM escalations e
            JOIN projects p ON e.project_id = p.id
            LEFT JOIN milestones m ON e.milestone_id = m.id
            WHERE e.resolved_date IS NULL
            ORDER BY e.severity DESC, e.created_date ASC
        """).fetchall()
        return [dict(row) for row in rows]
    
    def resolve_escalation(self, escalation_id: int):
        """Mark escalation as resolved."""
        self.db.execute(
            "UPDATE escalations SET resolved_date = CURRENT_TIMESTAMP WHERE id = ?",
            (escalation_id,)
        )
        self.db.commit()
        logger.info(f"Escalation {escalation_id} resolved")
    
    def mark_escalation_emailed(self, escalation_id: int):
        """Mark that we've notified Joe about this escalation."""
        self.db.execute(
            "UPDATE escalations SET emailed = 1 WHERE id = ?",
            (escalation_id,)
        )
        self.db.commit()
    
    # ============================================================================
    # AUTO-INTAKE
    # ============================================================================
    
    def queue_intake(
        self,
        title: str,
        source: str,
        source_id: str,
        description: str = "",
        division: str = "Research"
    ) -> int:
        """
        Queue a new project for intake (from GitHub issue, folder creation, etc).
        
        source: "github_issue", "folder_created", "manual"
        """
        try:
            cursor = self.db.execute(
                """INSERT INTO intake_queue 
                (title, source, source_id, description, division)
                VALUES (?, ?, ?, ?, ?)""",
                (title, source, source_id, description, division)
            )
            self.db.commit()
            logger.info(f"Intake queued: {title} (source={source})")
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            logger.warning(f"Intake already exists: {source_id}")
            return -1
    
    def get_intake_queue(self) -> List[Dict]:
        """Get all unprocessed intake items."""
        rows = self.db.execute(
            "SELECT * FROM intake_queue WHERE processed = 0 ORDER BY discovered_date ASC"
        ).fetchall()
        return [dict(row) for row in rows]
    
    def process_intake(self, intake_id: int, project_id: int):
        """Convert intake item to project."""
        self.db.execute(
            "UPDATE intake_queue SET processed = 1, project_id = ? WHERE id = ?",
            (project_id, intake_id)
        )
        self.db.commit()
        logger.info(f"Intake {intake_id} processed → project {project_id}")
    
    # ============================================================================
    # REPORTING
    # ============================================================================
    
    def get_daily_status(self) -> Dict:
        """Generate today's project status snapshot."""
        today = datetime.now().isoformat()[:10]
        
        projects_active = self.db.execute(
            "SELECT COUNT(*) FROM projects WHERE status = 'active'"
        ).fetchone()[0]
        
        projects_blocked = self.db.execute(
            "SELECT COUNT(*) FROM projects WHERE status = 'blocked'"
        ).fetchone()[0]
        
        # Note: projects table doesn't have completed_date field yet
        projects_complete = self.db.execute(
            "SELECT COUNT(*) FROM projects WHERE status = 'complete'"
        ).fetchone()[0]
        
        milestones_due = self.db.execute(
            """SELECT COUNT(*) FROM milestones 
            WHERE status IN ('pending', 'in_progress') 
            AND target_date BETWEEN ? AND ?""",
            (today, (datetime.now() + timedelta(days=7)).isoformat()[:10])
        ).fetchone()[0]
        
        production_today = self.db.execute(
            """SELECT COUNT(*) as runs, SUM(asset_count) as assets, SUM(cost_usd) as cost
            FROM production_log
            WHERE DATE(timestamp) = ?""",
            (today,)
        ).fetchone()
        
        return {
            "as_of": datetime.now().isoformat(),
            "projects_active": projects_active,
            "projects_blocked": projects_blocked,
            "projects_complete": projects_complete,
            "milestones_due_week": milestones_due,
            "production_runs_today": production_today[0] or 0,
            "assets_produced_today": production_today[1] or 0,
            "cost_today_usd": production_today[2] or 0.0,
            "unresolved_escalations": len(self.get_unresolved_escalations()),
            "intake_pending": len(self.get_intake_queue())
        }
    
    def get_weekly_status(self) -> Dict:
        """Generate weekly accountability report."""
        week_start = (datetime.now() - timedelta(days=7)).isoformat()[:10]
        week_end = datetime.now().isoformat()[:10]
        
        # Projects
        active = self.list_projects({"status": "active"})
        blocked = self.list_projects({"status": "blocked"})
        
        # Milestones due this week
        due_this_week = self.db.execute(
            """SELECT p.name, m.title, m.target_date, m.assigned_agent
            FROM milestones m
            JOIN projects p ON m.project_id = p.id
            WHERE m.status IN ('pending', 'in_progress')
            AND m.target_date BETWEEN ? AND ?
            ORDER BY m.target_date ASC""",
            (week_start, week_end)
        ).fetchall()
        
        # Production stats
        production_stats = self.db.execute(
            """SELECT agent, asset_type, SUM(asset_count) as total, SUM(cost_usd) as cost
            FROM production_log
            WHERE timestamp > ?
            GROUP BY agent, asset_type
            ORDER BY total DESC""",
            (week_start,)
        ).fetchall()
        
        return {
            "period": f"{week_start} to {week_end}",
            "projects_active": len(active),
            "projects_blocked": len(blocked),
            "blocked_details": [{"name": p["name"], "status": p["status"]} for p in blocked],
            "milestones_due_this_week": [
                {"project": row[0], "milestone": row[1], "date": row[2], "agent": row[3]}
                for row in due_this_week
            ],
            "production_summary": [
                {"agent": row[0], "asset_type": row[1], "total": row[2], "cost": row[3]}
                for row in production_stats
            ],
            "escalations_unresolved": self.get_unresolved_escalations()
        }
    
    def close(self):
        """Close database connection."""
        self.db.close()


# ============================================================================
# STANDALONE UTILITIES
# ============================================================================

def bootstrap_studio(db_path: str = "studio_projects.db"):
    """
    Initialize studio with all existing projects, agents, and divisions.
    Call this once to set up the system.
    """
    orch = StudioOrchestrator(db_path)
    
    # Clear existing data (optional)
    # orch.db.execute("DELETE FROM projects")
    # orch.db.commit()
    
    logger.info("=== BOOTSTRAPPING STUDIO ===")
    
    # DIVISION 1: COMMERCE
    ebay_id = orch.add_project(
        name="eBay Agent",
        division="Commerce",
        description="Identify, list, and manage inventory across eBay",
        priority=1,
        owner_agent="ebay_agent",
        tags=["revenue", "commerce"],
        milestones=[
            {"title": "Identify 50 items from backlog", "target_date": "2026-04-10", "agent": "ebay_agent"},
            {"title": "Push 40 listings to eBay", "target_date": "2026-04-12", "agent": "ebay_agent"},
            {"title": "Monitor and optimize pricing", "target_date": "2026-04-20", "agent": "ebay_agent"}
        ]
    )
    
    # DIVISION 2: CONTENT
    game_arch_id = orch.add_project(
        name="Game Archaeology",
        division="Content",
        description="Weekly digest of abandoned/indie games from Wayback Machine, itch.io, GitHub",
        priority=2,
        owner_agent="game_archaeology_agent",
        tags=["revenue", "content"],
        target_date="2026-06-01",
        milestones=[
            {"title": "Weekly crawler operational", "target_date": "2026-04-07", "agent": "game_archaeology_agent"},
            {"title": "Digest sent to 5 subscribers", "target_date": "2026-04-15", "agent": "game_archaeology_agent"},
            {"title": "Phase 1 revenue ($500)", "target_date": "2026-05-15", "agent": "game_archaeology_agent"}
        ]
    )
    
    ghost_book_id = orch.add_project(
        name="Ghost Book Division",
        division="Content",
        description="Salvage and grade out-of-print books, create digital archives",
        priority=3,
        owner_agent="ghost_book_agent",
        tags=["content"],
        milestones=[
            {"title": "Grade A/B/C triage system live", "target_date": "2026-04-15", "agent": "ghost_book_agent"},
            {"title": "100 books cataloged", "target_date": "2026-05-01", "agent": "ghost_book_agent"}
        ]
    )
    
    # DIVISION 3: INFRASTRUCTURE
    ai_intel_id = orch.add_project(
        name="AI Intel Agent",
        division="Infrastructure",
        description="Two-layer source discovery and deep-scraping for ML research trends",
        priority=2,
        owner_agent="ai_intel_agent",
        tags=["infrastructure"],
        milestones=[
            {"title": "Layer 1 discovery (Tavily, YouTube, sitemaps)", "target_date": "2026-04-10", "agent": "ai_intel_agent"},
            {"title": "Layer 2 deep-scrape + scoring", "target_date": "2026-04-20", "agent": "ai_intel_agent"}
        ]
    )
    
    job_discovery_id = orch.add_project(
        name="Job Discovery System",
        division="Infrastructure",
        description="Discover 250K-400K jobs from 10 free sources, Phase 1 SQLite + Flask API",
        priority=1,
        owner_agent="job_discovery_agent",
        tags=["infrastructure"],
        target_date="2026-05-01",
        milestones=[
            {"title": "542 sources validated", "target_date": "2026-04-05", "agent": "job_discovery_agent"},
            {"title": "SQLite schema complete", "target_date": "2026-04-08", "agent": "job_discovery_agent"},
            {"title": "Flask API live", "target_date": "2026-04-15", "agent": "job_discovery_agent"}
        ]
    )
    
    studio_sidebar_id = orch.add_project(
        name="Studio Sidebar v2",
        division="Infrastructure",
        description="Live project ticker, asset tracker, escalation alerts via HTTP sidebar",
        priority=2,
        owner_agent="sidebar_agent",
        tags=["infrastructure"],
        milestones=[
            {"title": "ChromaDB RAG (595 chunks) live", "target_date": "2026-04-07", "agent": "sidebar_agent"},
            {"title": "Project ticker rendering", "target_date": "2026-04-10", "agent": "sidebar_agent"},
            {"title": "Daily asset ticker update", "target_date": "2026-04-15", "agent": "sidebar_agent"}
        ]
    )
    
    # DIVISION 4: RESEARCH & CHARACTERS
    char_test_id = orch.add_project(
        name="Character Test Workbench",
        division="Research",
        description="Platform for testing AI character profiles (Mara, Vesper, Josie, Céleste)",
        priority=2,
        owner_agent="art_department",
        tags=["content"],
        milestones=[
            {"title": "Multi-provider API dropdown", "target_date": "2026-04-08", "agent": "art_department"},
            {"title": "Stress test battery complete", "target_date": "2026-04-12", "agent": "art_department"},
            {"title": "4 character profiles scored", "target_date": "2026-04-18", "agent": "art_department"}
        ]
    )
    
    gs_pipeline_id = orch.add_project(
        name="Gaussian Splatting Pipeline",
        division="Research",
        description="3D asset generation for historical figures (Tesla, da Vinci)",
        priority=4,
        owner_agent="art_department",
        tags=["content"],
        milestones=[
            {"title": "RTX 3060 upgrade ordered", "target_date": "2026-04-20", "agent": "art_department"},
            {"title": "Tesla asset proof-of-concept", "target_date": "2026-05-15", "agent": "art_department"}
        ]
    )
    
    # DIVISION 5: SENTINEL SUITE (NEW)
    sentinel_perf_id = orch.add_project(
        name="Sentinel Performer",
        division="Sentinel Suite",
        description="Real-time marketplace intelligence + alert system",
        priority=1,
        owner_agent="sentinel_performer",
        tags=["revenue", "infrastructure"],
        target_date="2026-06-01",
        milestones=[
            {"title": "Market data API schema", "target_date": "2026-04-15", "agent": "sentinel_performer"},
            {"title": "Alert engine MVP", "target_date": "2026-04-25", "agent": "sentinel_performer"},
            {"title": "Live with 3 markets", "target_date": "2026-05-15", "agent": "sentinel_performer"}
        ]
    )
    
    sentinel_core_id = orch.add_project(
        name="Sentinel Core",
        division="Sentinel Suite",
        description="Foundational scoring engine and data aggregation",
        priority=2,
        owner_agent="workflow_intelligence",
        tags=["infrastructure"],
        milestones=[
            {"title": "Data aggregation architecture", "target_date": "2026-04-12", "agent": "workflow_intelligence"},
            {"title": "Scoring algorithm v1", "target_date": "2026-04-20", "agent": "workflow_intelligence"}
        ]
    )
    
    sentinel_viewer_id = orch.add_project(
        name="Sentinel Viewer",
        division="Sentinel Suite",
        description="Dashboard frontend for market intelligence",
        priority=2,
        owner_agent="art_department",
        tags=["content"],
        milestones=[
            {"title": "API schema finalized", "target_date": "2026-04-15", "agent": "workflow_intelligence"},
            {"title": "Frontend mockup", "target_date": "2026-04-25", "agent": "art_department"},
            {"title": "First integration test", "target_date": "2026-05-01", "agent": "art_department"}
        ]
    )
    
    # DIVISION 6: ART DEPARTMENT
    art_dept_id = orch.add_project(
        name="Art Department",
        division="Content",
        description="Daily free-tier image generation with human review gates",
        priority=3,
        owner_agent="art_department",
        tags=["content"],
        milestones=[
            {"title": "Daily quota tracker", "target_date": "2026-04-08", "agent": "art_department"},
            {"title": "100 images reviewed and graded", "target_date": "2026-04-30", "agent": "art_department"}
        ]
    )
    
    # OTHER CORE AGENTS
    inbox_mgr_id = orch.add_project(
        name="Inbox Manager",
        division="Infrastructure",
        description="Enforce Hopper schema, route tasks to correct agents",
        priority=2,
        owner_agent="inbox_manager",
        tags=["infrastructure"],
        milestones=[
            {"title": "Schema validation live", "target_date": "2026-04-07", "agent": "inbox_manager"},
            {"title": "Daily routing report", "target_date": "2026-04-15", "agent": "inbox_manager"}
        ]
    )
    
    supervisor_id = orch.add_project(
        name="Supervisor Agent",
        division="Infrastructure",
        description="Goal-setting and work prioritization (NOT script provision)",
        priority=1,
        owner_agent="supervisor",
        tags=["infrastructure"],
        target_date="2026-04-30",
        milestones=[
            {"title": "Goal schema defined", "target_date": "2026-04-10", "agent": "supervisor"},
            {"title": "Daily goal briefing generated", "target_date": "2026-04-20", "agent": "supervisor"}
        ]
    )
    
    whiteboard_id = orch.add_project(
        name="Whiteboard Agent",
        division="Infrastructure",
        description="Track ideas, experiments, and backlog items",
        priority=2,
        owner_agent="whiteboard_agent",
        tags=["infrastructure"],
        milestones=[
            {"title": "Whiteboard state schema", "target_date": "2026-04-08", "agent": "whiteboard_agent"},
            {"title": "Weekly idea summary", "target_date": "2026-04-20", "agent": "whiteboard_agent"}
        ]
    )
    
    # FUTURE/PENDING PROJECTS
    truth_gate_id = orch.add_project(
        name="Truth Gate (Horde Shooter)",
        division="Content",
        description="Original indie game — awaiting game dev and artist",
        priority=5,
        owner_agent="manual",
        tags=["content"],
        target_date="2026-09-01",
        milestones=[
            {"title": "Game design doc", "target_date": "2026-05-01", "agent": "manual"},
            {"title": "Prototype build", "target_date": "2026-07-01", "agent": "manual"}
        ]
    )
    
    acuscan_id = orch.add_project(
        name="AcuScan AR",
        division="Research",
        description="AR wellness tool for acupressure point scanning",
        priority=4,
        owner_agent="manual",
        tags=["content"],
        milestones=[
            {"title": "MVP scope finalized", "target_date": "2026-05-15", "agent": "manual"}
        ]
    )
    
    # DEPENDENCIES
    logger.info("Adding dependencies...")
    
    # Sentinel suite interdependencies
    orch.add_dependency(sentinel_core_id, sentinel_perf_id, "feeds_into")
    orch.add_dependency(sentinel_core_id, sentinel_viewer_id, "feeds_into")
    
    # Art dept feeds character workbench
    orch.add_dependency(art_dept_id, char_test_id, "feeds_into")
    
    # Character workbench needs sidebar for display
    orch.add_dependency(studio_sidebar_id, char_test_id, "feeds_into")
    
    # Job discovery feeds supervisor
    orch.add_dependency(job_discovery_id, supervisor_id, "feeds_into")
    
    logger.info("=== BOOTSTRAP COMPLETE ===")
    orch.close()


if __name__ == "__main__":
    # Initialize database
    bootstrap_studio()
    
    # Quick test
    orch = StudioOrchestrator()
    print("\n" + "="*80)
    print("STUDIO ORCHESTRATOR - DAILY STATUS")
    print("="*80)
    status = orch.get_daily_status()
    for k, v in status.items():
        print(f"{k}: {v}")
    print("="*80)
    orch.close()
