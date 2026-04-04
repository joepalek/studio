"""
TASK SCHEDULER INTEGRATION SCRIPTS
Place these scripts in your Windows Task Scheduler to automate studio operations.

Each script should be scheduled as a separate task running under your user account.
Python interpreter path: C:\Users\[YourUser]\AppData\Local\Programs\Python\Python312\python.exe
(Adjust based on your Python installation)

SCHEDULED TASKS:
  1. daily_health_check.py       → 6:00 AM (detect blocks, silent failures)
  2. daily_digest.py             → 7:00 AM (send email digest)
  3. sidebar_bridge_launcher.py  → 5:00 AM (start HTTP server if not running)
  4. agent_production_logger.py  → Wrapped by each agent (log on completion)
"""

import subprocess
import sys
import os
from pathlib import Path

# Set working directory to studio system folder
STUDIO_DIR = Path(__file__).parent
os.chdir(STUDIO_DIR)

# ============================================================================
# Script 1: DAILY HEALTH CHECK
# ============================================================================

def daily_health_check():
    """
    Run at 6:00 AM daily.
    Detects and escalates issues: silent failures, blocks, missed deadlines.
    """
    from health_monitor import StudioHealthMonitor
    
    print("\n" + "="*80)
    print("STUDIO DAILY HEALTH CHECK")
    print("="*80)
    
    monitor = StudioHealthMonitor("studio_projects.db")
    monitor.run_daily_checks()


# ============================================================================
# Script 2: DAILY DIGEST EMAIL
# ============================================================================

def send_daily_digest():
    """
    Run at 7:00 AM daily.
    Sends summary of today's activity: projects, production, escalations.
    """
    from email_service import send_daily_digest
    
    print("\n" + "="*80)
    print("STUDIO DAILY DIGEST")
    print("="*80)
    
    send_daily_digest()


# ============================================================================
# Script 3: WEEKLY REPORT
# ============================================================================

def send_weekly_report():
    """
    Run Monday 8:00 AM.
    Sends comprehensive weekly accountability report.
    """
    from email_service import send_weekly_report
    
    print("\n" + "="*80)
    print("STUDIO WEEKLY REPORT")
    print("="*80)
    
    send_weekly_report()


# ============================================================================
# Script 4: SIDEBAR BRIDGE LAUNCHER
# ============================================================================

def ensure_sidebar_bridge_running():
    """
    Run at 5:00 AM daily (before health check).
    Ensures sidebar_bridge.py is running on port 11436.
    If not, restart it.
    """
    import socket
    import time
    
    PORT = 11436
    
    def is_port_open(port, timeout=1):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        return result == 0
    
    print(f"\nChecking if sidebar bridge is running on port {PORT}...")
    
    if is_port_open(PORT):
        print("✓ Sidebar bridge is running")
        return
    
    print("✗ Sidebar bridge not responding, restarting...")
    
    # Kill any existing process
    os.system(f"taskkill /F /IM python.exe /FI \"COMMANDLINE *sidebar_bridge*\" 2>nul")
    time.sleep(2)
    
    # Start sidebar bridge in background
    sidebar_script = STUDIO_DIR / "sidebar_bridge.py"
    subprocess.Popen(
        [sys.executable, str(sidebar_script)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    
    print("✓ Sidebar bridge started")
    time.sleep(2)


# ============================================================================
# Script 5: AGENT PRODUCTION LOGGER WRAPPER
# ============================================================================

def wrap_agent_execution(agent_name: str, agent_script: str, project_id: int):
    """
    Call this wrapper when executing any agent.
    
    Usage (from your agent launcher):
        python agent_wrapper.py ebay_agent "path/to/ebay_agent.py" 1
    
    The wrapper:
    1. Runs the agent
    2. Captures any output or assets produced
    3. Logs production to database
    4. Reports errors if agent fails
    """
    from studio_orchestrator import StudioOrchestrator
    import json
    
    print(f"\n{'='*80}")
    print(f"AGENT: {agent_name}")
    print(f"PROJECT_ID: {project_id}")
    print(f"{'='*80}")
    
    orch = StudioOrchestrator("studio_projects.db")
    
    # Track execution
    start_time = time.time()
    try:
        # Run agent script
        result = subprocess.run(
            [sys.executable, agent_script],
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout
        )
        
        # Parse output for asset counts
        # (assumes agent logs in format: "PRODUCED: listing=15, image=3")
        assets_produced = parse_agent_output(result.stdout)
        
        if result.returncode == 0:
            status = "success"
            details = {"execution_time_sec": time.time() - start_time}
        else:
            status = "failed"
            details = {
                "error": result.stderr[:500],
                "execution_time_sec": time.time() - start_time
            }
        
        # Log to database
        for asset_type, count in assets_produced.items():
            orch.log_production(
                agent=agent_name,
                project_id=project_id,
                asset_type=asset_type,
                asset_count=count,
                cost_usd=0.0,  # Update based on actual API usage
                status=status,
                details=details
            )
        
        print(f"\n✓ Agent completed: {asset_type}={count} assets")
    
    except subprocess.TimeoutExpired:
        orch.create_escalation(
            project_id=project_id,
            escalation_type="silent_fail",
            description=f"{agent_name} timeout after 1 hour",
            severity="high"
        )
        print(f"\n✗ Agent timeout: {agent_name}")
    
    except Exception as e:
        orch.create_escalation(
            project_id=project_id,
            escalation_type="silent_fail",
            description=f"{agent_name} error: {str(e)}",
            severity="medium"
        )
        print(f"\n✗ Agent error: {e}")
    
    finally:
        orch.close()


def parse_agent_output(output: str) -> dict:
    """
    Parse agent output for production metrics.
    
    Expected format:
        PRODUCED: listing=15, image=3, digest_sent=1
        COST: 0.05
    """
    import re
    
    assets = {}
    
    # Look for PRODUCED line
    match = re.search(r"PRODUCED:\s*(.*?)(?=\n|COST|$)", output, re.DOTALL)
    if match:
        pairs = match.group(1).split(",")
        for pair in pairs:
            k, v = pair.strip().split("=")
            assets[k.strip()] = int(v.strip())
    
    return assets


# ============================================================================
# COMMAND LINE INTERFACE
# ============================================================================

if __name__ == "__main__":
    import time
    
    if len(sys.argv) < 2:
        print("""
STUDIO TASK SCHEDULER INTEGRATION

Usage:
  python studio_tasks.py health_check          # Run daily health checks
  python studio_tasks.py digest                # Send daily digest
  python studio_tasks.py weekly_report         # Send weekly report
  python studio_tasks.py ensure_sidebar        # Ensure sidebar bridge running
  python studio_tasks.py wrap_agent <name> <script> <project_id>
                                                # Wrap and log agent execution

Examples:
  python studio_tasks.py health_check
  python studio_tasks.py wrap_agent ebay_agent "C:/path/to/ebay_agent.py" 1
        """)
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "health_check":
        daily_health_check()
    
    elif command == "digest":
        send_daily_digest()
    
    elif command == "weekly_report":
        send_weekly_report()
    
    elif command == "ensure_sidebar":
        ensure_sidebar_bridge_running()
    
    elif command == "wrap_agent":
        if len(sys.argv) < 5:
            print("Usage: python studio_tasks.py wrap_agent <name> <script> <project_id>")
            sys.exit(1)
        agent_name = sys.argv[2]
        agent_script = sys.argv[3]
        project_id = int(sys.argv[4])
        wrap_agent_execution(agent_name, agent_script, project_id)
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
