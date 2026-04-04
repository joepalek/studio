"""
AGENT INTEGRATION FRAMEWORK
Standardized wrapper for all studio agents.
Provides: logging, error handling, cost tracking, timeout management, health checks.

Usage:
  1. Inherit from StudioAgent in your agent
  2. Implement run() method
  3. Call self.log_production() when done
  4. Orchestrator handles DB updates automatically
"""

import logging
import json
import time
from datetime import datetime
from typing import Dict, Optional, List
from pathlib import Path
from studio_orchestrator import StudioOrchestrator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s'
)


class StudioAgent:
    """
    Base class for all studio agents.
    Handles: logging, error recovery, cost tracking, health checks.
    """
    
    def __init__(
        self,
        agent_name: str,
        project_id: int,
        db_path: str = "studio_projects.db",
        log_dir: str = "logs"
    ):
        """
        Initialize agent.
        
        Args:
            agent_name: Unique identifier (e.g., "ebay_agent")
            project_id: Studio project ID (from database)
            db_path: Path to studio_projects.db
            log_dir: Directory for agent logs
        """
        self.agent_name = agent_name
        self.project_id = project_id
        self.db_path = db_path
        
        # Setup logging
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.logger = self._setup_logger()
        
        # Initialize orchestrator
        self.orch = StudioOrchestrator(db_path)
        
        # Track production
        self.production = {}  # {asset_type: count}
        self.cost_usd = 0.0
        self.start_time = None
        self.end_time = None
        
        self.logger.info(f"Agent initialized: {agent_name} (project_id={project_id})")
    
    def _setup_logger(self) -> logging.Logger:
        """Configure logger with file + console output."""
        logger = logging.getLogger(self.agent_name)
        
        # File handler
        log_file = self.log_dir / f"{self.agent_name}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s'
        ))
        logger.addHandler(file_handler)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s [%(agent_name)s] %(levelname)s: %(message)s',
            defaults={'agent_name': self.agent_name}
        ))
        logger.addHandler(console_handler)
        
        return logger
    
    def run(self):
        """
        Override this method in subclass.
        Must call self.log_production() to log work.
        """
        raise NotImplementedError("Subclass must implement run()")
    
    def log_production(self, asset_type: str, count: int, cost_usd: float = 0.0):
        """
        Log assets produced by this agent.
        
        Args:
            asset_type: What was created (e.g., "listings", "images", "digest_sent")
            count: How many
            cost_usd: API costs for this batch
        """
        self.production[asset_type] = self.production.get(asset_type, 0) + count
        self.cost_usd += cost_usd
        self.logger.info(f"Produced: {asset_type}={count} (cost=${cost_usd:.4f})")
    
    def execute(self, timeout_seconds: int = 3600):
        """
        Execute agent with error handling and logging.
        
        Args:
            timeout_seconds: Max runtime before forced termination
        """
        self.start_time = time.time()
        status = "success"
        error_msg = None
        
        try:
            self.logger.info(f"Starting execution (timeout={timeout_seconds}s)")
            
            # Run agent (subclass implements this)
            self.run()
            
            self.end_time = time.time()
            duration = self.end_time - self.start_time
            
            # Log results
            if self.production:
                self.logger.info(f"✓ Execution complete ({duration:.1f}s)")
                for asset_type, count in self.production.items():
                    self.logger.info(f"  → {asset_type}: {count} assets")
            else:
                self.logger.warning(f"⚠ Execution complete but 0 assets produced ({duration:.1f}s)")
                status = "partial"
        
        except TimeoutError as e:
            self.logger.error(f"✗ Timeout after {timeout_seconds}s: {e}")
            status = "failed"
            error_msg = f"Timeout: {str(e)}"
            self._create_escalation("timeout", error_msg)
        
        except Exception as e:
            self.logger.error(f"✗ Error: {e}", exc_info=True)
            status = "failed"
            error_msg = str(e)
            self._create_escalation("error", error_msg)
        
        finally:
            # Log to database
            self._log_to_database(status, error_msg)
            self.orch.close()
            self.logger.info(f"Agent shutdown: {self.agent_name}")
    
    def _log_to_database(self, status: str, error_msg: Optional[str] = None):
        """Log production to studio database."""
        if not self.production:
            # Silent failure: agent ran but produced nothing
            self.orch.create_escalation(
                project_id=self.project_id,
                escalation_type="silent_fail",
                description=f"{self.agent_name} ran but produced 0 assets",
                severity="medium"
            )
        
        for asset_type, count in self.production.items():
            self.orch.log_production(
                agent=self.agent_name,
                project_id=self.project_id,
                asset_type=asset_type,
                asset_count=count,
                cost_usd=self.cost_usd,
                status=status,
                details={
                    "duration_seconds": self.end_time - self.start_time if self.end_time else 0,
                    "error": error_msg
                }
            )
    
    def _create_escalation(self, escalation_type: str, description: str):
        """Create escalation for critical issues."""
        self.orch.create_escalation(
            project_id=self.project_id,
            escalation_type=escalation_type,
            description=f"{self.agent_name}: {description}",
            severity="high" if escalation_type == "error" else "medium"
        )
    
    def health_check(self) -> Dict:
        """
        Verify agent configuration and dependencies.
        Override if agent has specific checks.
        
        Returns:
            {"status": "healthy" or "degraded", "issues": []}
        """
        issues = []
        
        # Check database connectivity
        try:
            project = self.orch.db.execute(
                "SELECT name FROM projects WHERE id = ?",
                (self.project_id,)
            ).fetchone()
            if not project:
                issues.append(f"Project ID {self.project_id} not found in database")
        except Exception as e:
            issues.append(f"Database error: {e}")
        
        return {
            "status": "degraded" if issues else "healthy",
            "agent": self.agent_name,
            "project_id": self.project_id,
            "issues": issues
        }


class AgentRegistry:
    """
    Central registry for all studio agents.
    Provides: health check, statistics, execution coordination.
    """
    
    def __init__(self, db_path: str = "studio_projects.db"):
        self.db_path = db_path
        self.agents: Dict[str, type] = {}  # name -> class
        self.config = {}  # name -> config dict
    
    def register(self, agent_class: type, project_id: int, config: Optional[Dict] = None):
        """
        Register an agent.
        
        Args:
            agent_class: Class inheriting from StudioAgent
            project_id: Studio project ID
            config: Optional configuration dict
        """
        agent_name = agent_class.__name__
        self.agents[agent_name] = agent_class
        self.config[agent_name] = {
            "project_id": project_id,
            "config": config or {}
        }
    
    def get_agent(self, agent_name: str) -> Optional[StudioAgent]:
        """Instantiate and return an agent."""
        if agent_name not in self.agents:
            return None
        
        agent_class = self.agents[agent_name]
        cfg = self.config[agent_name]
        
        return agent_class(
            agent_name=agent_name,
            project_id=cfg["project_id"],
            db_path=self.db_path
        )
    
    def health_check_all(self) -> List[Dict]:
        """Run health checks on all registered agents."""
        results = []
        for agent_name in self.agents.keys():
            agent = self.get_agent(agent_name)
            if agent:
                results.append(agent.health_check())
                agent.orch.close()
        return results
    
    def list_agents(self) -> List[str]:
        """Get all registered agent names."""
        return list(self.agents.keys())


# ============================================================================
# EXAMPLE AGENT IMPLEMENTATIONS
# ============================================================================

class EBayAgent(StudioAgent):
    """Example: eBay listing agent."""
    
    def __init__(self, project_id: int = 1):
        super().__init__("ebay_agent", project_id)
    
    def run(self):
        """Identify items and push listings."""
        self.logger.info("Starting eBay scan...")
        
        # Simulated work
        items_identified = 15
        listings_pushed = 12
        
        self.logger.info(f"Identified {items_identified} items from backlog")
        self.log_production("items_identified", items_identified, cost_usd=0.01)
        
        time.sleep(1)  # Simulate API calls
        
        self.logger.info(f"Pushed {listings_pushed} to eBay")
        self.log_production("listings_pushed", listings_pushed, cost_usd=0.02)


class GameArchaeologyAgent(StudioAgent):
    """Example: Game Archaeology digest agent."""
    
    def __init__(self, project_id: int = 2):
        super().__init__("game_archaeology_agent", project_id)
    
    def run(self):
        """Crawl and generate digest."""
        self.logger.info("Scanning Wayback Machine...")
        
        sources_found = 42
        digest_generated = 1
        
        self.log_production("sources_found", sources_found, cost_usd=0.60)
        self.log_production("digest_sent", digest_generated, cost_usd=0.00)
        
        self.logger.info(f"Generated digest with {sources_found} sources")


class ArtDepartmentAgent(StudioAgent):
    """Example: Art Department image generation."""
    
    def __init__(self, project_id: int = 12):
        super().__init__("art_department", project_id)
    
    def run(self):
        """Generate daily free-tier images."""
        self.logger.info("Generating images with free quota...")
        
        images_generated = 5
        
        self.log_production("images_generated", images_generated, cost_usd=0.00)
        
        self.logger.info(f"Used daily free quota: {images_generated} images")


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    # Register agents
    registry = AgentRegistry()
    registry.register(EBayAgent, project_id=1)
    registry.register(GameArchaeologyAgent, project_id=2)
    registry.register(ArtDepartmentAgent, project_id=12)
    
    # Run health checks
    print("\n=== AGENT HEALTH CHECK ===")
    health = registry.health_check_all()
    for check in health:
        status_icon = "✓" if check["status"] == "healthy" else "⚠"
        print(f"{status_icon} {check['agent']}: {check['status']}")
        if check['issues']:
            for issue in check['issues']:
                print(f"  - {issue}")
    
    # Execute an agent
    print("\n=== EXECUTING EBAY AGENT ===")
    agent = registry.get_agent("EBayAgent")
    agent.execute()
    
    # Verify it logged
    print("\n=== VERIFYING PRODUCTION LOG ===")
    orch = StudioOrchestrator()
    prod = orch.get_project_production(1, days=1)
    for p in prod:
        print(f"{p['agent']} → {p['asset_type']}: {p['total_count']} (${p['total_cost']:.2f})")
    orch.close()
