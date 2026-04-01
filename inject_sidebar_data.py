"""
inject_sidebar_data.py
Rebuilds sidebar-agent.html with fresh studio data.
Delegates to rebuild_sidebar.py which owns the full HTML structure.
"""
import subprocess, sys, os

STUDIO = "G:/My Drive/Projects/_studio"
result = subprocess.run(
    [sys.executable, STUDIO + "/rebuild_sidebar.py"],
    capture_output=True, text=True, encoding='utf-8', errors='replace'
)
print(result.stdout)
if result.returncode != 0:
    print("ERRORS:")
    print(result.stderr[:500])
