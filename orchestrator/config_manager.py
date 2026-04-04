"""
STUDIO CONFIGURATION MANAGEMENT
Centralized config for agents, divisions, email, task scheduling.

Format: YAML (human-readable)
Schema: JSON (validates config)
Hot-reload: Watches for changes and reloads automatically
"""

import yaml
import json
from pathlib import Path
from typing import Dict, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class StudioConfig:
    """
    Centralized configuration management for the entire studio.
    
    Config structure:
    
    studio:
      name: "Joe's AI Studio"
      db_path: "G:/My Drive/Projects/_studio/orchestrator/studio_projects.db"
      
    email:
      mode: "dev" or "production"
      smtp_server: "smtp.gmail.com"
      sender: "studio-orchestrator@yourmail.com"
      recipient: "joedealsonline@gmail.com"
      
    services:
      sidebar_bridge:
        port: 11436
        update_interval: 60
      health_monitor:
        schedule: "6:00 AM"
        timeout: 3600
        
    agents:
      ebay_agent:
        project_id: 1
        schedule: "3:00 PM daily"
        timeout: 1800
        enabled: true
        
      game_archaeology_agent:
        project_id: 2
        schedule: "6:00 PM daily"
        timeout: 3600
        enabled: true
    """
    
    def __init__(self, config_path: str = "studio_config.yaml"):
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        self.last_modified = None
        self.load()
    
    def load(self):
        """Load config from YAML file."""
        if not self.config_path.exists():
            logger.warning(f"Config file not found: {self.config_path}")
            self._create_default_config()
            return
        
        try:
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f) or {}
            
            self.last_modified = self.config_path.stat().st_mtime
            logger.info(f"Config loaded: {self.config_path}")
        
        except yaml.YAMLError as e:
            logger.error(f"YAML parse error: {e}")
            self._create_default_config()
    
    def reload_if_changed(self) -> bool:
        """Check if config has changed on disk and reload."""
        if not self.config_path.exists():
            return False
        
        current_mtime = self.config_path.stat().st_mtime
        if current_mtime > self.last_modified:
            logger.info("Config file changed, reloading...")
            self.load()
            return True
        
        return False
    
    def _create_default_config(self):
        """Create default config if none exists."""
        self.config = {
            "studio": {
                "name": "Joe's AI Studio",
                "db_path": "G:/My Drive/Projects/_studio/orchestrator/studio_projects.db",
                "log_dir": "logs"
            },
            "email": {
                "mode": "dev",  # "dev" or "production"
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "sender_email": "studio-orchestrator@anthropic.test",
                "recipient_email": "joedealsonline@gmail.com",
                "smtp_password": "${GMAIL_APP_PASSWORD}"  # Set via environment
            },
            "services": {
                "sidebar_bridge": {
                    "host": "127.0.0.1",
                    "port": 11436,
                    "update_interval_sec": 60,
                    "auto_restart": True
                },
                "health_monitor": {
                    "enabled": True,
                    "schedule": "6:00 AM",
                    "timeout_sec": 3600
                }
            },
            "agents": {
                "ebay_agent": {
                    "project_id": 1,
                    "schedule": "3:00 PM daily",
                    "timeout_sec": 1800,
                    "enabled": True
                },
                "game_archaeology_agent": {
                    "project_id": 2,
                    "schedule": "6:00 PM daily",
                    "timeout_sec": 3600,
                    "enabled": True
                }
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s [%(name)s] %(levelname)s: %(message)s"
            }
        }
        
        self.save()
        logger.info(f"Created default config: {self.config_path}")
    
    def save(self):
        """Write config to YAML file."""
        try:
            with open(self.config_path, 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False, sort_keys=False)
            
            self.last_modified = self.config_path.stat().st_mtime
            logger.info(f"Config saved: {self.config_path}")
        
        except IOError as e:
            logger.error(f"Failed to save config: {e}")
    
    def get(self, path: str, default: Any = None) -> Any:
        """
        Get config value by dot-notation path.
        
        Args:
            path: "email.mode" or "agents.ebay_agent.enabled"
            default: Return if not found
        
        Returns:
            Config value or default
        """
        keys = path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, path: str, value: Any):
        """Set config value by dot-notation path."""
        keys = path.split('.')
        cfg = self.config
        
        for key in keys[:-1]:
            if key not in cfg:
                cfg[key] = {}
            cfg = cfg[key]
        
        cfg[keys[-1]] = value
        self.save()
    
    def get_agent_config(self, agent_name: str) -> Optional[Dict]:
        """Get config for specific agent."""
        agents = self.get("agents", {})
        return agents.get(agent_name)
    
    def get_enabled_agents(self) -> Dict[str, Dict]:
        """Get all enabled agents."""
        agents = self.get("agents", {})
        return {
            name: cfg
            for name, cfg in agents.items()
            if cfg.get("enabled", True)
        }
    
    def validate(self) -> tuple[bool, list]:
        """
        Validate config against schema.
        
        Returns:
            (is_valid, list of errors)
        """
        errors = []
        
        # Required top-level keys
        for key in ["studio", "email", "services", "agents"]:
            if key not in self.config:
                errors.append(f"Missing required section: {key}")
        
        # Validate email config
        if self.get("email.mode") not in ["dev", "production"]:
            errors.append("email.mode must be 'dev' or 'production'")
        
        # Validate agents
        agents = self.get("agents", {})
        for agent_name, agent_cfg in agents.items():
            if "project_id" not in agent_cfg:
                errors.append(f"Agent '{agent_name}' missing project_id")
        
        return len(errors) == 0, errors
    
    def to_dict(self) -> Dict:
        """Export config as dictionary."""
        return self.config.copy()
    
    def to_json(self, pretty: bool = True) -> str:
        """Export config as JSON string."""
        return json.dumps(self.config, indent=2 if pretty else None)


# ============================================================================
# PRESET CONFIGURATIONS
# ============================================================================

class ConfigPresets:
    """Pre-built configurations for different scenarios."""
    
    @staticmethod
    def development() -> StudioConfig:
        """Development setup (email to console, frequent checks)."""
        cfg = StudioConfig()
        cfg.set("email.mode", "dev")
        cfg.set("services.health_monitor.schedule", "5:00 AM")  # Earlier for testing
        cfg.set("logging.level", "DEBUG")
        return cfg
    
    @staticmethod
    def production() -> StudioConfig:
        """Production setup (email via SMTP, standard schedule)."""
        cfg = StudioConfig()
        cfg.set("email.mode", "production")
        cfg.set("services.health_monitor.schedule", "6:00 AM")
        cfg.set("logging.level", "INFO")
        return cfg
    
    @staticmethod
    def minimal() -> StudioConfig:
        """Minimal setup (sidebar only, no email)."""
        cfg = StudioConfig()
        cfg.set("services.health_monitor.enabled", False)
        cfg.set("email.mode", "none")
        return cfg


# ============================================================================
# EXAMPLE: studio_config.yaml
# ============================================================================

EXAMPLE_CONFIG = """
# STUDIO CONFIGURATION
# This file defines all agents, services, and settings for Joe's AI Studio

studio:
  name: "Joe's AI Studio"
  db_path: "G:/My Drive/Projects/_studio/orchestrator/studio_projects.db"
  log_dir: "logs"

# Email Configuration
email:
  mode: "dev"  # "dev" = console, "production" = SMTP
  smtp_server: "smtp.gmail.com"
  smtp_port: 587
  sender_email: "studio-orchestrator@anthropic.test"
  recipient_email: "joedealsonline@gmail.com"
  smtp_password: "${GMAIL_APP_PASSWORD}"  # Set via environment variable

# Services Configuration
services:
  sidebar_bridge:
    host: "127.0.0.1"
    port: 11436
    update_interval_sec: 60  # Sidebar refreshes every 60 seconds
    auto_restart: true
  
  health_monitor:
    enabled: true
    schedule: "6:00 AM"  # Daily health check
    timeout_sec: 3600

# Agent Configuration (16+ agents)
agents:
  ebay_agent:
    project_id: 1
    schedule: "3:00 PM daily"
    timeout_sec: 1800
    enabled: true
  
  game_archaeology_agent:
    project_id: 2
    schedule: "6:00 PM daily"
    timeout_sec: 3600
    enabled: true
  
  ghost_book_agent:
    project_id: 3
    schedule: "7:00 AM daily"
    timeout_sec: 3600
    enabled: true
  
  ai_intel_agent:
    project_id: 4
    schedule: "9:00 PM daily"
    timeout_sec: 7200
    enabled: true
  
  job_discovery_agent:
    project_id: 5
    schedule: "10:00 PM daily"
    timeout_sec: 7200
    enabled: true
  
  art_department:
    project_id: 12
    schedule: "8:00 AM daily"
    timeout_sec: 1800
    enabled: true
  
  sentinel_performer:
    project_id: 9
    schedule: "5:00 AM daily"
    timeout_sec: 3600
    enabled: false  # Not yet active

# Logging Configuration
logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
  format: "%(asctime)s [%(name)s] %(levelname)s: %(message)s"
  file_dir: "logs"
"""


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    # Load config
    cfg = StudioConfig("studio_config.yaml")
    
    # Validate
    is_valid, errors = cfg.validate()
    if not is_valid:
        print("Config validation errors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("✓ Config valid")
    
    # Query config
    print(f"\nStudio: {cfg.get('studio.name')}")
    print(f"Email mode: {cfg.get('email.mode')}")
    print(f"Sidebar port: {cfg.get('services.sidebar_bridge.port')}")
    
    # Get enabled agents
    print("\nEnabled agents:")
    for agent_name, agent_cfg in cfg.get_enabled_agents().items():
        print(f"  • {agent_name} (project_id={agent_cfg['project_id']})")
    
    # Export config
    print("\nConfig as JSON:")
    print(cfg.to_json())
    
    # Write example config
    with open("studio_config.example.yaml", "w") as f:
        f.write(EXAMPLE_CONFIG)
    print("\nExample config written to: studio_config.example.yaml")
