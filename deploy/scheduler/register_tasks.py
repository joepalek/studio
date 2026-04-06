"""
Register studio services with Windows Task Scheduler.

Usage:
    python register_tasks.py --all         # Register all tasks
    python register_tasks.py --clawcode    # Register ClawCode server
    python register_tasks.py --watchdog    # Register supervisor watchdog
    python register_tasks.py --list        # List registered tasks
    python register_tasks.py --remove      # Remove all studio tasks
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

STUDIO = os.environ.get("STUDIO_PATH", "G:/My Drive/Projects/_studio")
PYTHON = sys.executable

# Task definitions
TASKS = {
    "StudioClawCodeServer": {
        "description": "ClawCode server for sidebar chat integration",
        "script": "panel/clawcode_server.py",
        "trigger": "AtLogon",
        "delay": "PT30S",  # 30 second delay after logon
    },
    "StudioSupervisorWatchdog": {
        "description": "Supervisor health watchdog",
        "script": "utilities/supervisor_watchdog.py",
        "trigger": "Daily",
        "repetition": "PT5M",  # Every 5 minutes
    },
    "StudioDataRetention": {
        "description": "Nightly data retention purge",
        "script": "utilities/retention_purge.py",
        "trigger": "Daily",
        "time": "03:00",
    },
}


def run_schtasks(args: list, check: bool = True) -> subprocess.CompletedProcess:
    """Run schtasks command."""
    cmd = ["schtasks"] + args
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"Error: {result.stderr}")
    return result


def register_task(name: str, config: dict) -> bool:
    """Register a single task."""
    script_path = Path(STUDIO) / config["script"]
    
    if not script_path.exists():
        print(f"WARNING: Script not found: {script_path}")
    
    # Build schtasks command
    args = [
        "/Create",
        "/TN", f"Studio\\{name}",
        "/TR", f'"{PYTHON}" "{script_path}"',
        "/F",  # Force overwrite
    ]
    
    # Add trigger
    trigger = config.get("trigger", "Daily")
    if trigger == "AtLogon":
        args.extend(["/SC", "ONLOGON"])
        if "delay" in config:
            args.extend(["/DELAY", config["delay"]])
    elif trigger == "Daily":
        args.extend(["/SC", "DAILY"])
        if "time" in config:
            args.extend(["/ST", config["time"]])
        if "repetition" in config:
            args.extend(["/RI", config["repetition"].replace("PT", "").replace("M", "")])
            args.extend(["/DU", "24:00"])  # Duration: all day
    
    # Add description
    # Note: schtasks /Create doesn't support description directly
    # We'll use XML for that if needed
    
    result = run_schtasks(args)
    return result.returncode == 0


def remove_task(name: str) -> bool:
    """Remove a task."""
    result = run_schtasks(["/Delete", "/TN", f"Studio\\{name}", "/F"])
    return result.returncode == 0


def list_tasks() -> list:
    """List studio tasks."""
    result = run_schtasks(["/Query", "/FO", "LIST", "/TN", "Studio\\*"], check=False)
    if result.returncode == 0:
        print(result.stdout)
    else:
        print("No studio tasks found or error querying.")
    return []


def main():
    parser = argparse.ArgumentParser(description="Register studio tasks")
    parser.add_argument("--all", action="store_true", help="Register all tasks")
    parser.add_argument("--clawcode", action="store_true", help="Register ClawCode server")
    parser.add_argument("--watchdog", action="store_true", help="Register watchdog")
    parser.add_argument("--list", action="store_true", help="List tasks")
    parser.add_argument("--remove", action="store_true", help="Remove all tasks")
    
    args = parser.parse_args()
    
    if args.list:
        list_tasks()
        return
    
    if args.remove:
        print("Removing all studio tasks...")
        for name in TASKS:
            remove_task(name)
        return
    
    tasks_to_register = []
    
    if args.all:
        tasks_to_register = list(TASKS.keys())
    else:
        if args.clawcode:
            tasks_to_register.append("StudioClawCodeServer")
        if args.watchdog:
            tasks_to_register.append("StudioSupervisorWatchdog")
    
    if not tasks_to_register:
        print("No tasks specified. Use --all, --clawcode, or --watchdog")
        return
    
    print(f"Registering {len(tasks_to_register)} tasks...")
    
    for name in tasks_to_register:
        print(f"\nRegistering {name}...")
        config = TASKS[name]
        success = register_task(name, config)
        print(f"  {'✓ Success' if success else '✗ Failed'}")
    
    print("\nDone. Use --list to verify.")


if __name__ == "__main__":
    main()
