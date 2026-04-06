"""
Supervisor watchdog with restart backoff.
Monitors supervisor health and restarts if unhealthy.
Prevents restart loops with exponential backoff.

Option C Panel Architecture v3.0 - Resilience
"""

import subprocess
import sys
import os
import json
from datetime import datetime, timedelta

STUDIO = os.environ.get("STUDIO_PATH", "G:/My Drive/Projects/_studio")
SUPERVISOR_PID_FILE = os.path.join(STUDIO, "supervisor.pid")
SUPERVISOR_HEARTBEAT_FILE = os.path.join(STUDIO, "supervisor-heartbeat.json")
WATCHDOG_LOG = os.path.join(STUDIO, "logs/supervisor-watchdog.log")
WATCHDOG_STATE_FILE = os.path.join(STUDIO, "watchdog-state.json")

# Configuration
MAX_HEARTBEAT_AGE_MINUTES = 10
INITIAL_BACKOFF_SECONDS = 60
MAX_BACKOFF_SECONDS = 900  # 15 minutes max
MAX_RESTARTS_PER_HOUR = 5


def load_watchdog_state() -> dict:
    """Load watchdog state from file."""
    if os.path.exists(WATCHDOG_STATE_FILE):
        try:
            with open(WATCHDOG_STATE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {
        "last_restart": None,
        "restart_count": 0,
        "restart_history": [],
        "current_backoff": INITIAL_BACKOFF_SECONDS
    }


def save_watchdog_state(state: dict):
    """Save watchdog state to file."""
    os.makedirs(os.path.dirname(WATCHDOG_STATE_FILE), exist_ok=True)
    with open(WATCHDOG_STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2)


def log(message: str):
    """Log message with timestamp."""
    timestamp = datetime.now().isoformat()
    os.makedirs(os.path.dirname(WATCHDOG_LOG), exist_ok=True)
    with open(WATCHDOG_LOG, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")
    print(f"[{timestamp}] {message}")


def check_backoff(state: dict) -> tuple:
    """
    Check if we're in backoff period after a restart.
    Returns (should_skip, reason, seconds_remaining).
    """
    if state.get("last_restart"):
        last_restart = datetime.fromisoformat(state["last_restart"])
        elapsed = (datetime.now() - last_restart).total_seconds()
        backoff = state.get("current_backoff", INITIAL_BACKOFF_SECONDS)
        
        if elapsed < backoff:
            remaining = int(backoff - elapsed)
            return True, f"In backoff period: {remaining}s remaining", remaining
    
    return False, "", 0


def check_restart_rate(state: dict) -> tuple:
    """
    Check if we've exceeded max restarts per hour.
    Returns (is_exceeded, count_in_hour).
    """
    now = datetime.now()
    hour_ago = now - timedelta(hours=1)
    
    # Clean old history
    history = state.get("restart_history", [])
    recent = [t for t in history if datetime.fromisoformat(t) > hour_ago]
    state["restart_history"] = recent
    
    return len(recent) >= MAX_RESTARTS_PER_HOUR, len(recent)


def check_supervisor_health() -> tuple:
    """
    Check if supervisor is healthy.
    Returns (is_healthy, reason).
    """
    # Check heartbeat file exists
    if not os.path.exists(SUPERVISOR_HEARTBEAT_FILE):
        return False, "No heartbeat file"
    
    try:
        with open(SUPERVISOR_HEARTBEAT_FILE, "r", encoding="utf-8") as f:
            heartbeat = json.load(f)
        
        timestamp = heartbeat.get("timestamp")
        if not timestamp:
            return False, "Heartbeat missing timestamp"
        
        last_beat = datetime.fromisoformat(timestamp)
        age = datetime.now() - last_beat
        
        if age > timedelta(minutes=MAX_HEARTBEAT_AGE_MINUTES):
            return False, f"Heartbeat stale: {age.total_seconds()/60:.1f} min old"
        
        # Check for error state
        if heartbeat.get("status") == "error":
            return False, f"Supervisor reporting error: {heartbeat.get('error', 'unknown')}"
        
        return True, "OK"
    
    except json.JSONDecodeError:
        return False, "Heartbeat file corrupt"
    except Exception as e:
        return False, f"Error reading heartbeat: {e}"


def check_process_running() -> tuple:
    """
    Check if supervisor process is running.
    Returns (is_running, pid or None).
    """
    if not os.path.exists(SUPERVISOR_PID_FILE):
        return False, None
    
    try:
        with open(SUPERVISOR_PID_FILE, "r") as f:
            pid = int(f.read().strip())
        
        # Check if process exists (Windows)
        if sys.platform == 'win32':
            result = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if str(pid) in result.stdout:
                return True, pid
        else:
            # Unix
            try:
                os.kill(pid, 0)
                return True, pid
            except OSError:
                pass
        
        return False, pid
    except:
        return False, None


def kill_supervisor(pid: int) -> bool:
    """Kill supervisor process."""
    try:
        if sys.platform == 'win32':
            subprocess.run(
                ["taskkill", "/F", "/PID", str(pid)],
                capture_output=True,
                timeout=10
            )
        else:
            os.kill(pid, 9)
        return True
    except:
        return False


def restart_supervisor(state: dict) -> bool:
    """
    Restart the supervisor with backoff tracking.
    Returns True if restart initiated.
    """
    log("Initiating supervisor restart...")
    
    # Kill existing if running
    is_running, pid = check_process_running()
    if is_running and pid:
        log(f"Killing existing supervisor (PID {pid})")
        kill_supervisor(pid)
    
    # Clear old PID file
    if os.path.exists(SUPERVISOR_PID_FILE):
        os.remove(SUPERVISOR_PID_FILE)
    
    # Start supervisor
    supervisor_script = os.path.join(STUDIO, "supervisor_check.py")
    
    if not os.path.exists(supervisor_script):
        log(f"ERROR: Supervisor script not found: {supervisor_script}")
        return False
    
    try:
        if sys.platform == 'win32':
            # Windows - use CREATE_NO_WINDOW
            proc = subprocess.Popen(
                [sys.executable, supervisor_script],
                cwd=STUDIO,
                creationflags=subprocess.CREATE_NO_WINDOW,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        else:
            # Unix
            proc = subprocess.Popen(
                [sys.executable, supervisor_script],
                cwd=STUDIO,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
        
        # Write new PID
        with open(SUPERVISOR_PID_FILE, "w") as f:
            f.write(str(proc.pid))
        
        # Update state with exponential backoff
        now = datetime.now().isoformat()
        state["last_restart"] = now
        state["restart_count"] = state.get("restart_count", 0) + 1
        state["restart_history"].append(now)
        
        # Increase backoff (exponential, capped)
        current_backoff = state.get("current_backoff", INITIAL_BACKOFF_SECONDS)
        state["current_backoff"] = min(current_backoff * 2, MAX_BACKOFF_SECONDS)
        
        save_watchdog_state(state)
        
        log(f"Supervisor restarted with PID {proc.pid}")
        log(f"Next check in {state['current_backoff']}s (backoff)")
        return True
    
    except Exception as e:
        log(f"ERROR restarting supervisor: {e}")
        return False


def reset_backoff(state: dict):
    """Reset backoff after sustained healthy period."""
    state["current_backoff"] = INITIAL_BACKOFF_SECONDS
    save_watchdog_state(state)


def main():
    """Main watchdog check."""
    state = load_watchdog_state()
    
    # Check backoff
    in_backoff, reason, remaining = check_backoff(state)
    if in_backoff:
        log(f"Skipping check: {reason}")
        return
    
    # Check restart rate
    rate_exceeded, count = check_restart_rate(state)
    if rate_exceeded:
        log(f"ALERT: Restart rate exceeded ({count} restarts in last hour). Manual intervention required.")
        return
    
    # Check process
    is_running, pid = check_process_running()
    if not is_running:
        log("Supervisor process not running")
        restart_supervisor(state)
        return
    
    # Check health
    is_healthy, reason = check_supervisor_health()
    
    if is_healthy:
        log(f"Supervisor healthy (PID {pid}): {reason}")
        
        # Reset backoff after sustained health
        if state.get("current_backoff", 0) > INITIAL_BACKOFF_SECONDS:
            last_restart = state.get("last_restart")
            if last_restart:
                elapsed = (datetime.now() - datetime.fromisoformat(last_restart)).total_seconds()
                # Reset after 30 minutes of health
                if elapsed > 1800:
                    log("Resetting backoff after sustained health")
                    reset_backoff(state)
    else:
        log(f"Supervisor unhealthy: {reason}")
        restart_supervisor(state)


def status():
    """Print current watchdog status."""
    state = load_watchdog_state()
    is_running, pid = check_process_running()
    is_healthy, health_reason = check_supervisor_health()
    in_backoff, backoff_reason, remaining = check_backoff(state)
    rate_exceeded, restart_count = check_restart_rate(state)
    
    print("=" * 50)
    print("SUPERVISOR WATCHDOG STATUS")
    print("=" * 50)
    print(f"Process running: {is_running} (PID: {pid})")
    print(f"Health status: {'healthy' if is_healthy else 'unhealthy'} - {health_reason}")
    print(f"In backoff: {in_backoff} - {backoff_reason if in_backoff else 'no'}")
    print(f"Current backoff: {state.get('current_backoff', INITIAL_BACKOFF_SECONDS)}s")
    print(f"Restarts (last hour): {restart_count}/{MAX_RESTARTS_PER_HOUR}")
    print(f"Total restarts: {state.get('restart_count', 0)}")
    
    if state.get("last_restart"):
        print(f"Last restart: {state['last_restart']}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "status":
            status()
        elif sys.argv[1] == "reset":
            state = load_watchdog_state()
            state["current_backoff"] = INITIAL_BACKOFF_SECONDS
            state["restart_history"] = []
            save_watchdog_state(state)
            print("Watchdog state reset")
        elif sys.argv[1] == "restart":
            state = load_watchdog_state()
            restart_supervisor(state)
        else:
            print("Usage:")
            print("  python supervisor_watchdog.py         # Run check")
            print("  python supervisor_watchdog.py status  # Show status")
            print("  python supervisor_watchdog.py reset   # Reset backoff")
            print("  python supervisor_watchdog.py restart # Force restart")
    else:
        main()
