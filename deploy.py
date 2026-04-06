"""
Deployment Script for Option C v3.0 + ClawCode Integration

Usage:
    python deploy.py --check          # Pre-flight checks only
    python deploy.py --day 1          # Deploy Day 1 (Security)
    python deploy.py --day 2          # Deploy Day 2 (Resilience)
    python deploy.py --clawcode       # Deploy ClawCode server
    python deploy.py --all            # Deploy everything
    python deploy.py --test           # Run test suite
"""

import os
import sys
import json
import shutil
import subprocess
import argparse
from datetime import datetime
from pathlib import Path

# Configuration
STUDIO = os.environ.get("STUDIO_PATH", "G:/My Drive/Projects/_studio")
DEPLOY_SOURCE = Path(__file__).parent
BACKUP_DIR = Path(STUDIO) / "backups" / datetime.now().strftime("%Y%m%d_%H%M%S")


def log(msg: str, level: str = "INFO"):
    """Log message with timestamp."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    prefix = {"INFO": "ℹ️", "OK": "✅", "WARN": "⚠️", "ERROR": "❌"}.get(level, "")
    print(f"[{timestamp}] {prefix} {msg}")


def run_command(cmd: list, check: bool = True) -> subprocess.CompletedProcess:
    """Run a command and return result."""
    log(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if check and result.returncode != 0:
        log(f"Command failed: {result.stderr}", "ERROR")
    return result


def preflight_checks() -> bool:
    """Run pre-flight checks before deployment."""
    log("Running pre-flight checks...")
    all_ok = True
    
    # Check Python version
    if sys.version_info < (3, 9):
        log(f"Python 3.9+ required, got {sys.version}", "ERROR")
        all_ok = False
    else:
        log(f"Python version: {sys.version_info.major}.{sys.version_info.minor}", "OK")
    
    # Check studio path exists
    if not os.path.exists(STUDIO):
        log(f"Studio path not found: {STUDIO}", "ERROR")
        all_ok = False
    else:
        log(f"Studio path exists: {STUDIO}", "OK")
    
    # Check for pywin32 (Windows only)
    if sys.platform == 'win32':
        try:
            import win32crypt
            log("pywin32 (DPAPI) available", "OK")
        except ImportError:
            log("pywin32 not installed - run: pip install pywin32", "WARN")
    
    # Check for Flask
    try:
        import flask
        log(f"Flask {flask.__version__} available", "OK")
    except ImportError:
        log("Flask not installed - run: pip install flask flask-cors", "WARN")
        all_ok = False
    
    # Check Ollama
    result = run_command(["ollama", "list"], check=False)
    if result.returncode == 0:
        log("Ollama available", "OK")
        # Check for qwen3 model
        if "qwen3" in result.stdout.lower():
            log("qwen3 model found", "OK")
        else:
            log("qwen3 model not found - run: ollama pull qwen3:14b", "WARN")
    else:
        log("Ollama not available", "WARN")
    
    # Check ClawCode
    clawcode_path = os.environ.get("CLAWCODE_PATH", r"C:\tools\claw\claw.exe")
    if os.path.exists(clawcode_path):
        log(f"ClawCode found at {clawcode_path}", "OK")
    else:
        log(f"ClawCode not found at {clawcode_path}", "WARN")
    
    return all_ok


def backup_existing():
    """Backup existing files before deployment."""
    log(f"Creating backup at {BACKUP_DIR}")
    os.makedirs(BACKUP_DIR, exist_ok=True)
    
    files_to_backup = [
        "panel/security_events.py",
        "panel/circuit_breaker.py",
        "utilities/secret_encryption.py",
        "schemas/retention_policy.json",
    ]
    
    for file in files_to_backup:
        src = Path(STUDIO) / file
        if src.exists():
            dst = BACKUP_DIR / file
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            log(f"Backed up: {file}")


def deploy_file(src_name: str, dst_path: str):
    """Deploy a single file."""
    src = DEPLOY_SOURCE / src_name
    dst = Path(STUDIO) / dst_path
    
    if not src.exists():
        log(f"Source file not found: {src}", "ERROR")
        return False
    
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    log(f"Deployed: {dst_path}", "OK")
    return True


def deploy_day1():
    """Deploy Day 1: Security Hardening."""
    log("=" * 50)
    log("DEPLOYING DAY 1: SECURITY HARDENING")
    log("=" * 50)
    
    # Install pywin32 if needed
    if sys.platform == 'win32':
        try:
            import win32crypt
        except ImportError:
            log("Installing pywin32...")
            run_command([sys.executable, "-m", "pip", "install", "pywin32"])
    
    # Deploy files
    files = [
        ("utilities/secret_encryption.py", "utilities/secret_encryption.py"),
        ("panel/security_events.py", "panel/security_events.py"),
        ("panel/tamper_proof_log.py", "panel/tamper_proof_log.py"),
    ]
    
    for src, dst in files:
        deploy_file(src, dst)
    
    # Encrypt existing secrets
    registry_path = Path(STUDIO) / "agent_registry.json"
    if registry_path.exists():
        log("Encrypting existing agent secrets...")
        from utilities.secret_encryption import encrypt_all_secrets
        result = encrypt_all_secrets(str(registry_path))
        log(f"Encrypted {result['encrypted']} secrets", "OK")
    
    log("Day 1 deployment complete!", "OK")


def deploy_day2():
    """Deploy Day 2: Resilience Patterns."""
    log("=" * 50)
    log("DEPLOYING DAY 2: RESILIENCE PATTERNS")
    log("=" * 50)
    
    files = [
        ("panel/circuit_breaker.py", "panel/circuit_breaker.py"),
    ]
    
    for src, dst in files:
        deploy_file(src, dst)
    
    log("Day 2 deployment complete!", "OK")
    log("Remember to add /health endpoint to serve_sidebar_server.py")


def deploy_day3():
    """Deploy Day 3: Data Governance."""
    log("=" * 50)
    log("DEPLOYING DAY 3: DATA GOVERNANCE")
    log("=" * 50)
    
    files = [
        ("schemas/retention_policy.json", "schemas/retention_policy.json"),
    ]
    
    for src, dst in files:
        deploy_file(src, dst)
    
    # Create required directories
    dirs = ["appeals", "experiments", "ground_truth"]
    for d in dirs:
        path = Path(STUDIO) / d
        path.mkdir(exist_ok=True)
        log(f"Created directory: {d}", "OK")
    
    log("Day 3 deployment complete!", "OK")


def deploy_clawcode():
    """Deploy ClawCode server integration."""
    log("=" * 50)
    log("DEPLOYING CLAWCODE INTEGRATION")
    log("=" * 50)
    
    files = [
        ("panel/clawcode_server.py", "panel/clawcode_server.py"),
        ("panel/clawcode_chat.js", "panel/clawcode_chat.js"),
        ("tests/test_clawcode_integration.py", "tests/test_clawcode_integration.py"),
    ]
    
    for src, dst in files:
        deploy_file(src, dst)
    
    # Create sidebar secret
    secret_file = Path(STUDIO) / ".sidebar_secret"
    if not secret_file.exists():
        import secrets
        new_secret = secrets.token_hex(32)
        secret_file.write_text(new_secret)
        log(f"Generated sidebar secret in {secret_file}", "OK")
        log(f"Set SIDEBAR_SECRET={new_secret[:16]}...")
    
    log("ClawCode deployment complete!", "OK")
    log("")
    log("Next steps:")
    log("1. Set SIDEBAR_SECRET environment variable")
    log("2. Start server: python panel/clawcode_server.py")
    log("3. Update sidebar HTML to use ClawCode chat")


def run_tests():
    """Run test suite."""
    log("=" * 50)
    log("RUNNING TESTS")
    log("=" * 50)
    
    # Add deploy source to path
    sys.path.insert(0, str(DEPLOY_SOURCE))
    
    # Import and run tests
    from tests.test_clawcode_integration import run_tests as run_unit_tests
    result = run_unit_tests()
    
    if result == 0:
        log("All tests passed!", "OK")
    else:
        log("Some tests failed", "ERROR")
    
    return result


def main():
    parser = argparse.ArgumentParser(description="Deploy Option C v3.0 + ClawCode")
    parser.add_argument("--check", action="store_true", help="Run pre-flight checks only")
    parser.add_argument("--day", type=int, choices=[1, 2, 3], help="Deploy specific day")
    parser.add_argument("--clawcode", action="store_true", help="Deploy ClawCode server")
    parser.add_argument("--all", action="store_true", help="Deploy everything")
    parser.add_argument("--test", action="store_true", help="Run test suite")
    parser.add_argument("--no-backup", action="store_true", help="Skip backup")
    
    args = parser.parse_args()
    
    # Default to check if no args
    if len(sys.argv) == 1:
        args.check = True
    
    log("=" * 50)
    log("OPTION C v3.0 + CLAWCODE DEPLOYMENT")
    log("=" * 50)
    log(f"Studio: {STUDIO}")
    log(f"Source: {DEPLOY_SOURCE}")
    log("")
    
    # Pre-flight checks
    if not preflight_checks():
        if not args.check:
            log("Pre-flight checks failed. Fix issues and retry.", "ERROR")
            return 1
    
    if args.check:
        log("Pre-flight checks complete.")
        return 0
    
    # Backup
    if not args.no_backup and not args.test:
        backup_existing()
    
    # Deploy
    if args.day == 1 or args.all:
        deploy_day1()
    
    if args.day == 2 or args.all:
        deploy_day2()
    
    if args.day == 3 or args.all:
        deploy_day3()
    
    if args.clawcode or args.all:
        deploy_clawcode()
    
    if args.test:
        return run_tests()
    
    log("")
    log("=" * 50)
    log("DEPLOYMENT COMPLETE", "OK")
    log("=" * 50)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
