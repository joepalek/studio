"""
inject_sidebar_data.py
Rebuilds sidebar-agent.html with fresh studio data.
Delegates to rebuild_sidebar.py which owns the full HTML structure.
"""

# EXPECTED_RUNTIME_SECONDS: 300
import subprocess, sys, os

import sys as _sys
_sys.path.insert(0, "G:/My Drive/Projects/_studio/utilities")
from constraint_gates import hamilton_watchdog

STUDIO = "G:/My Drive/Projects/_studio"
result = subprocess.run(
    [sys.executable, STUDIO + "/rebuild_sidebar.py"],
    capture_output=True, text=True, encoding='utf-8', errors='replace'
)
print(result.stdout)
if result.returncode != 0:
    print("ERRORS:")
    print(result.stderr[:500])
