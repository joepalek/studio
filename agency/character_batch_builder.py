# AGENCY CHARACTER BATCH BUILDER
# Reads passing-specs.json, promotes top specs into full character folders.
# Run nightly after spec grader completes (schedule after 5:30 AM).
# Gateway routing: pure Python -- zero LLM cost.
# Output: agency/characters/{universe}/{name}/ folders with full file structure.

import json, os, sys, time
from datetime import datetime
from pathlib import Path

STUDIO = "G:/My Drive/Projects/_studio"
AGENCY = STUDIO + "/agency"
PASSING = AGENCY + "/spec-queue/passing-specs.json"
BUILD_LOG = AGENCY + "/spec-queue/build-log.json"
STATUS = STUDIO + "/claude-status.txt"
SCHED_LOG = STUDIO + "/scheduler/logs/overnight-agency-build.log"

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = "[" + ts + "] " + msg
    print(line)
    try:
        with open(SCHED_LOG, "a", encoding="utf-8", errors="replace") as f:
            f.write(line + "\n")
    except PermissionError:
        # Log file locked by prior Task Scheduler run — write to fallback
        fallback = SCHED_LOG.replace(".log", "-fallback.log")
        with open(fallback, "a", encoding="utf-8", errors="replace") as f:
            f.write(line + "\n")

log("Agency character batch build starting")

# Load passing specs
try:
    data = json.load(open(PASSING, encoding="utf-8"))
    specs = data.get("specs", [])
    log("Passing specs loaded: " + str(len(specs)))
except Exception as e:
    log("ERROR loading passing-specs.json: " + str(e))
    sys.exit(1)

# Load existing build log to skip already-built characters
built_ids = set()
try:
    blog = json.load(open(BUILD_LOG, encoding="utf-8"))
    built_ids = set(blog.get("built_ids", []))
    log("Already built: " + str(len(built_ids)) + " characters (will skip)")
except:
    log("No build log found -- fresh run")

# Import create_character from character_creator.py
sys.path.insert(0, AGENCY)
from character_creator import create_character

# Filter: only build specs not already built
to_build = [s for s in specs if s.get("id") not in built_ids]
log("To build this run: " + str(len(to_build)) + " new characters")

if not to_build:
    log("Nothing new to build -- all passing specs already have character folders")
    with open(STATUS, "a", encoding="utf-8") as f:
        f.write("[AGENCY-BUILD] " + datetime.now().isoformat() + " -- No new characters to build.\n")
    sys.exit(0)

# Build each character
results = {"built": [], "failed": [], "skipped": []}

for i, spec in enumerate(to_build):
    char_name = spec.get("name", "Unknown")
    char_id = spec.get("id", "?")
    universe = spec.get("universe", "original_fiction")

    # Normalize universe folder name (underscores to hyphens for folder)
    spec["universe"] = universe.replace("_", "-")

    try:
        result = create_character(spec)
        results["built"].append({
            "id": char_id,
            "name": char_name,
            "universe": universe,
            "path": result.get("path", ""),
            "built_at": datetime.now().isoformat()
        })
        built_ids.add(char_id)
        if (i + 1) % 25 == 0:
            log("  Progress: " + str(i+1) + "/" + str(len(to_build)) + " built")
    except Exception as e:
        log("  FAILED: " + char_name + " (" + char_id + ") -- " + str(e)[:80])
        results["failed"].append({"id": char_id, "name": char_name, "error": str(e)[:80]})

    # Small delay to avoid filesystem hammering
    time.sleep(0.05)

# Save updated build log
build_log = {
    "last_run": datetime.now().isoformat(),
    "total_ever_built": len(built_ids),
    "built_ids": list(built_ids),
    "last_run_stats": {
        "attempted": len(to_build),
        "built": len(results["built"]),
        "failed": len(results["failed"]),
    },
    "last_run_built": results["built"],
    "last_run_failed": results["failed"],
}
json.dump(build_log, open(BUILD_LOG, "w", encoding="utf-8"), indent=2)

# Summary by universe
by_universe = {}
for r in results["built"]:
    u = r["universe"]
    by_universe[u] = by_universe.get(u, 0) + 1

log("Build complete:")
log("  Built:  " + str(len(results["built"])))
log("  Failed: " + str(len(results["failed"])))
log("  By universe: " + str(by_universe))

# Count actual folders now
char_root = Path(AGENCY + "/characters")
total_folders = sum(1 for u in char_root.iterdir() if u.is_dir()
                    for c in u.iterdir() if c.is_dir())
log("  Total character folders now: " + str(total_folders))

# Heartbeat
with open(STATUS, "a", encoding="utf-8") as f:
    f.write("[AGENCY-BUILD] " + datetime.now().isoformat()
            + " -- built=" + str(len(results["built"]))
            + " failed=" + str(len(results["failed"]))
            + " total_folders=" + str(total_folders) + "\n")

log("Done.")
