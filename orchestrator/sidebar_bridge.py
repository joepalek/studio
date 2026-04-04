"""
STUDIO SIDEBAR BRIDGE SERVICE
HTTP server that provides live project data to sidebar-agent.html
Runs on port 11436 (adjacent to studio_bridge.py at 11435)

Endpoints:
  /api/projects/status       → JSON of all projects + status
  /api/projects/ticker       → HTML ticker widget
  /api/escalations/active    → Active escalations
  /api/stats/daily           → Daily stats snapshot
"""

from flask import Flask, jsonify, render_template_string
from datetime import datetime
from studio_orchestrator import StudioOrchestrator
import logging
import json

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route("/api/projects/status", methods=["GET"])
def get_projects_status():
    """Return all projects with current status."""
    orch = StudioOrchestrator()
    projects = orch.list_projects()
    
    # Enrich with production data
    for p in projects:
        prod = orch.get_project_production(p["id"], days=7)
        p["production_week"] = prod
        p["blockers"] = orch.get_blocking_projects(p["id"])
        p["dependents"] = orch.get_dependent_projects(p["id"])
    
    orch.close()
    return jsonify(projects)


@app.route("/api/projects/ticker", methods=["GET"])
def get_ticker_html():
    """Return HTML ticker widget for sidebar integration."""
    orch = StudioOrchestrator()
    
    # Get priority-ordered active projects
    projects = orch.list_projects({"status": "active"})
    
    # Build HTML
    html = """
    <div id="studio-ticker" style="font-family: monospace; font-size: 12px; padding: 10px; background: #0a0e27; color: #00ff41; border-radius: 4px; overflow-y: auto; max-height: 400px;">
        <div style="margin-bottom: 8px; border-bottom: 1px solid #00ff41; padding-bottom: 4px;">
            <strong>🎬 STUDIO PROJECTS</strong>
            <span style="float: right; font-size: 10px; color: #888;">LIVE</span>
        </div>
    """
    
    for p in projects:
        # Get status color
        if p["status"] == "blocked":
            color = "#ff4444"
            icon = "🔴"
        elif p["status"] == "active":
            color = "#00ff41"
            icon = "🟢"
        else:
            color = "#ffaa00"
            icon = "🟡"
        
        # Get next milestone
        next_milestone = orch.db.execute(
            "SELECT title FROM milestones WHERE project_id = ? AND status IN ('pending', 'in_progress') ORDER BY target_date ASC LIMIT 1",
            (p["id"],)
        ).fetchone()
        
        milestone_text = next_milestone[0][:30] if next_milestone else "(no active milestone)"
        
        html += f"""
        <div style="margin: 6px 0; padding: 4px; border-left: 2px solid {color}; background: rgba(0, 255, 65, 0.05);">
            <div style="color: {color};"><strong>{icon} {p['name']}</strong></div>
            <div style="color: #888; font-size: 10px; margin-top: 2px;">
                {p['division']} | P{p['priority']} | {milestone_text}
            </div>
        </div>
        """
    
    html += "</div>"
    
    orch.close()
    return {"html": html, "timestamp": datetime.now().isoformat()}


@app.route("/api/escalations/active", methods=["GET"])
def get_active_escalations():
    """Return all unresolved escalations."""
    orch = StudioOrchestrator()
    escalations = orch.get_unresolved_escalations()
    orch.close()
    return jsonify([dict(e) for e in escalations])


@app.route("/api/stats/daily", methods=["GET"])
def get_daily_stats():
    """Return today's stats snapshot."""
    orch = StudioOrchestrator()
    stats = orch.get_daily_status()
    orch.close()
    return jsonify(stats)


@app.route("/api/milestones/due-week", methods=["GET"])
def get_milestones_due_week():
    """Return milestones due in next 7 days."""
    orch = StudioOrchestrator()
    
    from datetime import timedelta
    today = datetime.now().isoformat()[:10]
    week_end = (datetime.now() + timedelta(days=7)).isoformat()[:10]
    
    rows = orch.db.execute("""
        SELECT p.name, m.title, m.target_date, m.assigned_agent, m.status, p.id
        FROM milestones m
        JOIN projects p ON m.project_id = p.id
        WHERE m.status IN ('pending', 'in_progress')
        AND m.target_date BETWEEN ? AND ?
        ORDER BY m.target_date ASC
    """, (today, week_end)).fetchall()
    
    milestones = [
        {
            "project_id": row[5],
            "project": row[0],
            "milestone": row[1],
            "due_date": row[2],
            "agent": row[3],
            "status": row[4]
        }
        for row in rows
    ]
    
    orch.close()
    return jsonify(milestones)


@app.route("/api/projects/<int:project_id>/details", methods=["GET"])
def get_project_details(project_id: int):
    """Return detailed info for a specific project."""
    orch = StudioOrchestrator()
    
    project = orch.db.execute(
        "SELECT * FROM projects WHERE id = ?", (project_id,)
    ).fetchone()
    
    if not project:
        return jsonify({"error": "Project not found"}), 404
    
    project_dict = dict(project)
    
    # Get milestones
    milestones = orch.db.execute(
        "SELECT * FROM milestones WHERE project_id = ? ORDER BY target_date ASC",
        (project_id,)
    ).fetchall()
    project_dict["milestones"] = [dict(m) for m in milestones]
    
    # Get production
    project_dict["production_30d"] = orch.get_project_production(project_id, 30)
    
    # Get dependencies
    project_dict["blockers"] = orch.get_blocking_projects(project_id)
    project_dict["dependents"] = orch.get_dependent_projects(project_id)
    
    # Get escalations
    escalations = orch.db.execute(
        "SELECT * FROM escalations WHERE project_id = ? AND resolved_date IS NULL",
        (project_id,)
    ).fetchall()
    project_dict["escalations"] = [dict(e) for e in escalations]
    
    orch.close()
    return jsonify(project_dict)


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "operational", "timestamp": datetime.now().isoformat()})


# ============================================================================
# HTML DASHBOARD (optional, for browser access)
# ============================================================================

@app.route("/", methods=["GET"])
def dashboard():
    """Simple web dashboard."""
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Studio Orchestrator Dashboard</title>
        <style>
            body { font-family: monospace; background: #0a0e27; color: #00ff41; padding: 20px; }
            h1 { border-bottom: 2px solid #00ff41; padding-bottom: 10px; }
            .project { border-left: 3px solid #00ff41; padding: 10px; margin: 10px 0; background: rgba(0, 255, 65, 0.05); }
            .blocked { border-left-color: #ff4444; }
            .section { margin-top: 30px; }
            a { color: #00ff41; text-decoration: none; }
        </style>
    </head>
    <body>
        <h1>🎬 STUDIO ORCHESTRATOR DASHBOARD</h1>
        <p>Last updated: <span id="timestamp">loading...</span></p>
        
        <div class="section">
            <h2>📊 Daily Stats</h2>
            <div id="daily-stats">Loading...</div>
        </div>
        
        <div class="section">
            <h2>🟢 Active Projects</h2>
            <div id="projects">Loading...</div>
        </div>
        
        <div class="section">
            <h2>⛔ Active Escalations</h2>
            <div id="escalations">Loading...</div>
        </div>
        
        <div class="section">
            <h2>📅 Milestones Due This Week</h2>
            <div id="milestones">Loading...</div>
        </div>
        
        <script>
        async function updateDashboard() {
            // Daily stats
            const stats = await fetch("/api/stats/daily").then(r => r.json());
            document.getElementById("daily-stats").innerHTML = `
                <pre>Active: ${stats.projects_active}
Blocked: ${stats.projects_blocked}
Production today: ${stats.assets_produced_today} assets ($${stats.cost_today_usd.toFixed(2)})
Escalations: ${stats.unresolved_escalations}</pre>
            `;
            
            // Projects
            const projects = await fetch("/api/projects/status").then(r => r.json());
            document.getElementById("projects").innerHTML = projects
                .filter(p => p.status === "active")
                .slice(0, 10)
                .map(p => `
                    <div class="project ${p.status === 'blocked' ? 'blocked' : ''}">
                        <strong>${p.name}</strong> [P${p.priority}] ${p.division}
                        <br><small>Status: ${p.status}</small>
                    </div>
                `).join("");
            
            // Escalations
            const escalations = await fetch("/api/escalations/active").then(r => r.json());
            document.getElementById("escalations").innerHTML = escalations.length === 0 
                ? "<p style='color: #00ff41;'>✓ No escalations</p>"
                : escalations.map(e => `
                    <div style="margin: 5px 0; padding: 5px; border-left: 2px solid #ff4444;">
                        <strong>${e.escalation_type}</strong>: ${e.description}
                    </div>
                `).join("");
            
            // Milestones
            const milestones = await fetch("/api/milestones/due-week").then(r => r.json());
            document.getElementById("milestones").innerHTML = milestones.length === 0
                ? "<p style='color: #888;'>(none)</p>"
                : milestones.map(m => `
                    <div style="margin: 5px 0; padding: 5px;">
                        ${m.project} → ${m.milestone}
                        <br><small>Due: ${m.due_date} | Agent: ${m.agent}</small>
                    </div>
                `).join("");
            
            document.getElementById("timestamp").textContent = new Date().toLocaleTimeString();
        }
        
        updateDashboard();
        setInterval(updateDashboard, 60000);  // Update every minute
        </script>
    </body>
    </html>
    """)


if __name__ == "__main__":
    logger.info("Starting Studio Sidebar Bridge on port 11436...")
    app.run(host="127.0.0.1", port=11436, debug=False)
