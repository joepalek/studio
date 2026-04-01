"""
janitor_run.py — Studio Workspace Janitor
Runs daily via Task Scheduler (Studio/Janitor).
Keeps studio clean: truncates oversized logs, removes stale temp files,
reports dead/orphaned files, writes heartbeat.
Zero LLM cost — pure Python.
"""
import os, sys, json, shutil
from datetime import datetime, timedelta

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

STUDIO   = "G:/My Drive/Projects/_studio"
LOG_DIR  = STUDIO + "/scheduler/logs"
LOG_PATH = LOG_DIR + "/overnight-janitor.log"
REPORT   = STUDIO + "/janitor-report.json"
HB_PATH  = STUDIO + "/heartbeat-log.json"

MAX_LOG_BYTES  = 500_000   # 500KB — truncate logs above this
MAX_LOG_AGE    = 30        # days — remove log files older than this
STALE_TEMP_AGE = 7         # days — remove temp/scratch files older than this

TEMP_PATTERNS = [
    "find_tabs.py", "full_audit.py", "count_blocks.py",
    "find_brace.py", "check_scripts.py", "audit_agents.py",
]

def log(msg):
    ts = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    line = ts + " " + str(msg)
    print(line)
    try:
        with open(LOG_PATH, "a", encoding="utf-8", errors="replace") as f:
            f.write(line + "\n")
    except: pass

def load_json(path, default=None):
    try: return json.load(open(path, encoding="utf-8", errors="replace"))
    except: return default

def save_json(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, path)

def truncate_large_logs():
    """Truncate log files over MAX_LOG_BYTES — keep last 1000 lines."""
    truncated = []
    for fname in os.listdir(LOG_DIR):
        if not fname.endswith(".log"): continue
        path = LOG_DIR + "/" + fname
        size = os.path.getsize(path)
        if size > MAX_LOG_BYTES:
            try:
                lines = open(path, encoding="utf-8", errors="replace").readlines()
                keep  = lines[-1000:]
                with open(path, "w", encoding="utf-8") as f:
                    f.write("".join(keep))
                truncated.append(fname + " (" + str(size//1024) + "KB → kept last 1000 lines)")
            except Exception as e:
                log("  WARN: could not truncate " + fname + ": " + str(e)[:50])
    return truncated

def remove_old_logs():
    """Remove log files not touched in MAX_LOG_AGE days."""
    cutoff = datetime.now().timestamp() - MAX_LOG_AGE * 86400
    removed = []
    for fname in os.listdir(LOG_DIR):
        if not fname.endswith(".log"): continue
        path = LOG_DIR + "/" + fname
        if os.path.getmtime(path) < cutoff:
            try:
                os.remove(path)
                removed.append(fname)
            except: pass
    return removed

def remove_pycache():
    """Remove all __pycache__ dirs under studio."""
    removed = []
    for root, dirs, files in os.walk(STUDIO):
        if "__pycache__" in dirs:
            cache_path = os.path.join(root, "__pycache__")
            try:
                shutil.rmtree(cache_path)
                removed.append(cache_path.replace(STUDIO, ""))
            except: pass
    return removed

def remove_temp_scripts():
    """Remove known temp/scratch scripts."""
    removed = []
    for fname in TEMP_PATTERNS:
        path = STUDIO + "/" + fname
        if os.path.exists(path):
            try:
                os.remove(path)
                removed.append(fname)
            except: pass
    return removed

def check_orphaned_bats():
    """Find bat files with no corresponding task registered."""
    sched_dir = STUDIO + "/scheduler"
    bats = [f for f in os.listdir(sched_dir) if f.endswith(".bat")]
    xmls = [f.replace(".xml","").lower() for f in os.listdir(sched_dir) if f.endswith(".xml")]
    orphaned = []
    for bat in bats:
        name = bat.replace(".bat","").lower().replace("-","").replace("_","")
        if not any(name in x.replace("-","").replace("_","") for x in xmls):
            orphaned.append(bat)
    return orphaned

def get_large_files():
    """Flag any non-log file in studio over 5MB."""
    large = []
    for root, dirs, files in os.walk(STUDIO):
        dirs[:] = [d for d in dirs if d not in [".git","vector-memory","__pycache__","_archive","_splat_projects"]]
        for f in files:
            path = os.path.join(root, f)
            try:
                size = os.path.getsize(path)
                if size > 5_000_000:
                    rel = path.replace(STUDIO, "").replace("\\","/")
                    large.append(rel + " (" + str(size//1024//1024) + "MB)")
            except: pass
    return large

def main():
    log("Janitor starting")
    report = {
        "date": datetime.now().isoformat(),
        "truncated_logs": [],
        "removed_old_logs": [],
        "removed_pycache": [],
        "removed_temp_scripts": [],
        "orphaned_bats": [],
        "large_files": [],
        "status": "clean"
    }

    # Truncate large logs
    truncated = truncate_large_logs()
    report["truncated_logs"] = truncated
    if truncated:
        log("Truncated " + str(len(truncated)) + " large logs:")
        for t in truncated: log("  " + t)

    # Remove old logs
    old_removed = remove_old_logs()
    report["removed_old_logs"] = old_removed
    if old_removed:
        log("Removed " + str(len(old_removed)) + " old logs: " + ", ".join(old_removed))

    # Remove pycache
    caches = remove_pycache()
    report["removed_pycache"] = caches
    if caches:
        log("Removed " + str(len(caches)) + " __pycache__ dirs")

    # Remove temp scripts
    temps = remove_temp_scripts()
    report["removed_temp_scripts"] = temps
    if temps:
        log("Removed temp scripts: " + ", ".join(temps))

    # Orphaned bats
    orphaned = check_orphaned_bats()
    report["orphaned_bats"] = orphaned
    if orphaned:
        log("Orphaned bat files (no matching XML task): " + ", ".join(orphaned))

    # Large files
    large = get_large_files()
    report["large_files"] = large
    if large:
        log("Large files flagged: " + str(len(large)))
        for f in large[:5]: log("  " + f)

    # Set status
    issues = len(truncated) + len(orphaned) + len(large)
    report["status"] = "flagged" if issues > 0 else "clean"
    save_json(REPORT, report)
    log("Janitor report saved. Status: " + report["status"])

    # Heartbeat
    hb = load_json(HB_PATH, {"entries": []})
    if not isinstance(hb, dict): hb = {"entries": []}
    hb["entries"].append({
        "date": datetime.now().isoformat(),
        "agent": "janitor",
        "status": report["status"],
        "notes": ("truncated=" + str(len(truncated)) + " old=" + str(len(old_removed)) +
                  " caches=" + str(len(caches)) + " large=" + str(len(large)))
    })
    hb["entries"] = hb["entries"][-200:]
    save_json(HB_PATH, hb)

    log("Janitor complete — " + report["status"])

if __name__ == "__main__":
    main()
