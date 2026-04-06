"""
Cascade impact analysis for agent/dependency failures.
Shows what breaks when something fails.

Option C Panel Architecture v3.0 - Resilience
"""

import json
import os
from typing import Set, List, Dict, Optional

STUDIO = os.environ.get("STUDIO_PATH", "G:/My Drive/Projects/_studio")


def load_dependency_map() -> dict:
    """Load the agent dependency map."""
    path = os.path.join(STUDIO, "dependency_map.json")
    if not os.path.exists(path):
        # Return a default structure if file doesn't exist
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_downstream_agents(failed_agent: str, dep_map: dict = None) -> Set[str]:
    """
    Get all agents that depend on the failed agent.
    Returns set of agent IDs that would be impacted.
    """
    if dep_map is None:
        dep_map = load_dependency_map()
    
    downstream = set()
    to_check = [failed_agent]
    checked = set()
    
    while to_check:
        current = to_check.pop()
        if current in checked:
            continue
        checked.add(current)
        
        # Find agents that list current as a dependency
        for agent_id, deps in dep_map.items():
            if current in deps.get("depends_on", []):
                downstream.add(agent_id)
                to_check.append(agent_id)
    
    return downstream


def get_upstream_dependencies(agent_id: str, dep_map: dict = None) -> Set[str]:
    """Get all dependencies an agent relies on (what it needs)."""
    if dep_map is None:
        dep_map = load_dependency_map()
    
    agent = dep_map.get(agent_id, {})
    return set(agent.get("depends_on", []))


def analyze_failure_impact(failed_entity: str, entity_type: str = "agent") -> dict:
    """
    Analyze the full impact of a failure.
    
    Args:
        failed_entity: Agent ID or dependency name
        entity_type: "agent" or "dependency"
    
    Returns:
        Impact analysis with affected agents and severity
    """
    dep_map = load_dependency_map()
    
    if entity_type == "agent":
        affected = get_downstream_agents(failed_entity, dep_map)
        direct_deps = list(dep_map.get(failed_entity, {}).get("depended_on_by", []))
    else:
        # Dependency failure - find all agents using it
        affected = set()
        direct_deps = []
        for agent_id, deps in dep_map.items():
            if failed_entity in deps.get("uses_dependencies", []):
                affected.add(agent_id)
                direct_deps.append(agent_id)
        
        # Add transitive impacts
        for agent in list(affected):
            affected.update(get_downstream_agents(agent, dep_map))
    
    # Calculate severity
    total_agents = len(dep_map)
    impact_ratio = len(affected) / max(total_agents, 1)
    
    if impact_ratio > 0.5:
        severity = "critical"
    elif impact_ratio > 0.25:
        severity = "high"
    elif impact_ratio > 0.1:
        severity = "medium"
    else:
        severity = "low"
    
    return {
        "failed_entity": failed_entity,
        "entity_type": entity_type,
        "directly_affected": direct_deps,
        "total_affected": list(affected),
        "affected_count": len(affected),
        "total_agents": total_agents,
        "impact_ratio": round(impact_ratio, 3),
        "severity": severity,
        "recommendation": _get_recommendation(severity, entity_type)
    }


def _get_recommendation(severity: str, entity_type: str) -> str:
    """Get recommendation based on severity."""
    if severity == "critical":
        return f"IMMEDIATE ACTION: {entity_type.title()} failure affects >50% of agents. Prioritize recovery."
    elif severity == "high":
        return f"HIGH PRIORITY: {entity_type.title()} failure affects >25% of agents. Investigate promptly."
    elif severity == "medium":
        return f"Monitor: {entity_type.title()} failure has moderate impact. Check dependent agents."
    else:
        return f"Low impact: {entity_type.title()} failure is contained. Monitor for cascade."


def create_dependency_map_template() -> dict:
    """Create a template dependency map if none exists."""
    return {
        "_schema_version": "1.0",
        "_description": "Agent dependency map for cascade analysis",
        
        "supervisor": {
            "depends_on": [],
            "uses_dependencies": ["filesystem", "json"],
            "depended_on_by": ["all_agents"]
        },
        
        "ebay_agent": {
            "depends_on": ["supervisor"],
            "uses_dependencies": ["ebay_api", "chromadb", "ollama"],
            "depended_on_by": []
        },
        
        "game_archaeology": {
            "depends_on": ["supervisor", "legal_agent"],
            "uses_dependencies": ["internet_archive", "github_api", "ollama"],
            "depended_on_by": []
        },
        
        "legal_agent": {
            "depends_on": ["supervisor"],
            "uses_dependencies": ["ollama"],
            "depended_on_by": ["game_archaeology"]
        }
    }


def visualize_dependencies(agent_id: Optional[str] = None) -> str:
    """Create ASCII visualization of dependency tree."""
    dep_map = load_dependency_map()
    
    if not dep_map:
        return "No dependency map found. Run: python cascade_analysis.py init"
    
    lines = ["DEPENDENCY TREE", "=" * 40]
    
    if agent_id:
        # Show specific agent
        if agent_id not in dep_map:
            return f"Agent not found: {agent_id}"
        
        agent = dep_map[agent_id]
        lines.append(f"\n{agent_id}")
        lines.append(f"  ├── Depends on: {', '.join(agent.get('depends_on', [])) or 'none'}")
        lines.append(f"  ├── Uses: {', '.join(agent.get('uses_dependencies', [])) or 'none'}")
        lines.append(f"  └── Depended on by: {', '.join(agent.get('depended_on_by', [])) or 'none'}")
    else:
        # Show all
        for aid, agent in dep_map.items():
            if aid.startswith("_"):
                continue
            deps = agent.get("depends_on", [])
            lines.append(f"\n{aid}")
            for i, dep in enumerate(deps):
                prefix = "└──" if i == len(deps) - 1 else "├──"
                lines.append(f"  {prefix} {dep}")
            if not deps:
                lines.append("  └── (no dependencies)")
    
    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python cascade_analysis.py analyze <agent_id|dependency> [agent|dependency]")
        print("  python cascade_analysis.py visualize [agent_id]")
        print("  python cascade_analysis.py init")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "analyze":
        entity = sys.argv[2]
        entity_type = sys.argv[3] if len(sys.argv) > 3 else "agent"
        result = analyze_failure_impact(entity, entity_type)
        print(json.dumps(result, indent=2))
    
    elif command == "visualize":
        agent_id = sys.argv[2] if len(sys.argv) > 2 else None
        print(visualize_dependencies(agent_id))
    
    elif command == "init":
        path = os.path.join(STUDIO, "dependency_map.json")
        if os.path.exists(path):
            print(f"Dependency map already exists at {path}")
        else:
            template = create_dependency_map_template()
            with open(path, "w", encoding="utf-8") as f:
                json.dump(template, f, indent=2)
            print(f"Created dependency map template at {path}")
            print("Edit this file to reflect your actual agent dependencies.")
