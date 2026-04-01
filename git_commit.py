"""
git_commit.py
Nightly git commit agent — replaces claude --dangerously-skip-permissions call.
Uses Gemini Flash to generate commit messages. Zero Claude quota.
Commits all dirty repos under G:/My Drive/Projects/
"""
import subprocess, json, urllib.request, os, sys
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

STUDIO   = "G:/My Drive/Projects/_studio"
BASE     = "G:/My Drive/Projects"
LOG_PATH = STUDIO + "/scheduler/logs/nightly-commit.log"
CONFIG   = json.load(open(STUDIO + "/studio-config.json", encoding="utf-8"))
KEY      = CONFIG.get("gemini_api_key", "")
GEMINI   = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=" + KEY

def log(msg):
    ts = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    line = ts + " " + str(msg)
    print(line)
    try:
        with open(LOG_PATH, "a", encoding="utf-8", errors="replace") as f:
            f.write(line + "\n")
    except: pass

def git(args, cwd):
    r = subprocess.run(["git"] + args, cwd=cwd,
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.stdout.strip(), r.stderr.strip(), r.returncode

def get_diff_summary(repo_path):
    diff, _, _ = git(["diff", "--stat", "HEAD"], repo_path)
    if not diff:
        diff, _, _ = git(["diff", "--cached", "--stat"], repo_path)
    status, _, _ = git(["status", "--short"], repo_path)
    return (status[:800] + "\n" + diff[:400]).strip()

def gemini_commit_message(project, diff_summary):
    if not KEY:
        return "chore: nightly auto-commit"
    prompt = (
        "Generate a concise git commit message for this project change.\n"
        "Project: " + project + "\n"
        "Changes:\n" + diff_summary + "\n\n"
        "Rules: conventional commits format (feat/fix/chore/docs/refactor). "
        "One line only. Max 72 chars. No quotes. No explanation."
    )
    payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode()
    try:
        r = urllib.request.urlopen(
            urllib.request.Request(GEMINI, data=payload,
                headers={"Content-Type": "application/json"}), timeout=10)
        text = json.loads(r.read())["candidates"][0]["content"]["parts"][0]["text"].strip()
        # Strip any quotes Gemini adds
        return text.strip('"').strip("'")[:72]
    except Exception as e:
        log("  Gemini msg failed: " + str(e)[:50] + " — using default")
        return "chore: nightly auto-commit [" + project + "]"

def commit_repo(repo_path, project):
    # Check if dirty
    status, _, _ = git(["status", "--short"], repo_path)
    if not status.strip():
        return "clean"

    dirty_count = len([l for l in status.strip().split("\n") if l.strip()])
    log("  " + project + ": " + str(dirty_count) + " dirty files")

    # Stage all
    _, err, rc = git(["add", "-A"], repo_path)
    if rc != 0:
        log("  " + project + " add failed: " + err[:60])
        return "error"

    # Generate commit message
    diff = get_diff_summary(repo_path)
    msg  = gemini_commit_message(project, diff)
    log("  " + project + " msg: " + msg)

    # Commit
    _, err, rc = git(["commit", "-m", msg], repo_path)
    if rc != 0:
        log("  " + project + " commit failed: " + err[:80])
        return "error"

    log("  " + project + ": committed OK")
    return "committed"

def main():
    log("Git commit agent starting")
    results = {"committed": [], "clean": [], "error": []}

    for d in sorted(os.listdir(BASE)):
        repo_path = BASE + "/" + d
        if not os.path.isdir(repo_path): continue
        if not os.path.exists(repo_path + "/.git"): continue

        result = commit_repo(repo_path, d)
        results[result].append(d)

    log("Done. Committed: " + str(len(results["committed"])) +
        " | Clean: " + str(len(results["clean"])) +
        " | Errors: " + str(len(results["error"])))
    if results["committed"]:
        log("Repos committed: " + ", ".join(results["committed"]))
    if results["error"]:
        log("Errors in: " + ", ".join(results["error"]))

    # Write to claude-status.txt
    try:
        summary = ("[GIT-COMMIT] " + datetime.now().isoformat() +
                   " committed=" + str(len(results["committed"])) +
                   " clean=" + str(len(results["clean"])))
        with open(STUDIO + "/claude-status.txt", "a", encoding="utf-8") as f:
            f.write(summary + "\n")
    except: pass

if __name__ == "__main__":
    main()
