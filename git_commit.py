"""
git_commit.py
Nightly git commit agent — replaces claude --dangerously-skip-permissions.
Uses Gemini Flash for commit messages. Zero Claude quota.
Also scans GitHub Trending and pushes relevant repos to whiteboard.
"""
import subprocess, json, urllib.request, urllib.parse, os, sys, re, time
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
        "Rules: conventional commits format. One line only. Max 72 chars. No quotes."
    )
    payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode()
    try:
        r = urllib.request.urlopen(
            urllib.request.Request(GEMINI, data=payload,
                headers={"Content-Type": "application/json"}), timeout=10)
        text = json.loads(r.read())["candidates"][0]["content"]["parts"][0]["text"].strip()
        return text.strip('"').strip("'")[:72]
    except Exception as e:
        log("  Gemini msg failed: " + str(e)[:50] + " — using default")
        return "chore: nightly auto-commit [" + project + "]"

def commit_repo(repo_path, project):
    status, _, _ = git(["status", "--short"], repo_path)
    if not status.strip():
        return "clean"
    dirty_count = len([l for l in status.strip().split("\n") if l.strip()])
    log("  " + project + ": " + str(dirty_count) + " dirty files")
    _, err, rc = git(["add", "-A"], repo_path)
    if rc != 0:
        log("  " + project + " add failed: " + err[:60])
        return "error"
    diff = get_diff_summary(repo_path)
    msg  = gemini_commit_message(project, diff)
    log("  " + project + " msg: " + msg)
    _, err, rc = git(["commit", "-m", msg], repo_path)
    if rc != 0:
        log("  " + project + " commit failed: " + err[:80])
        return "error"
    log("  " + project + ": committed OK")
    return "committed"

def scan_github_trending():
    """Scan GitHub Trending for relevant repos, push new ones to whiteboard."""
    log("Scanning GitHub Trending...")
    topics = ["python", "llm", "ai-agents"]
    found = []
    try:
        for topic in topics:
            url = "https://github.com/trending/" + topic + "?since=daily"
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (compatible; StudioGitScout/1.0)"})
            r = urllib.request.urlopen(req, timeout=12)
            html = r.read().decode("utf-8", errors="ignore")
            repos = re.findall(r'href="/([a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+)"', html)
            descs = re.findall(r'<p class="col-9[^"]*"[^>]*>\s*(.*?)\s*</p>', html)
            seen = set()
            for i, repo in enumerate(repos):
                if repo in seen or repo.count("/") != 1: continue
                seen.add(repo)
                desc = descs[i].strip() if i < len(descs) else ""
                found.append({"repo": repo, "desc": desc[:120], "topic": topic})
                if len(found) >= 15: break
            time.sleep(1)
    except Exception as e:
        log("GitHub Trending error: " + str(e)[:60])
        return 0

    wb_path = STUDIO + "/whiteboard.json"
    try:
        wb = json.load(open(wb_path, encoding="utf-8"))
        existing = {i.get("title","").lower() for i in wb.get("items", [])}
        added = 0
        for r in found:
            title = "GitHub Trending: " + r["repo"]
            if title.lower() not in existing:
                wb["items"].append({
                    "id": "gh-" + r["repo"].replace("/", "-"),
                    "title": title,
                    "description": r["desc"],
                    "type": "github_trending",
                    "tags": ["github", "trending", r["topic"]],
                    "added_at": datetime.now().isoformat()
                })
                existing.add(title.lower())
                added += 1
        if added:
            json.dump(wb, open(wb_path, "w", encoding="utf-8"), indent=2)
            log("Added " + str(added) + " trending repos to whiteboard")
        else:
            log("No new trending repos to add")
        return added
    except Exception as e:
        log("Whiteboard write error: " + str(e)[:60])
        return 0

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

    # GitHub Trending scan — push to whiteboard
    try:
        scan_github_trending()
    except Exception as e:
        log("GitHub scan error: " + str(e)[:60])

    # claude-status.txt
    try:
        summary = ("[GIT-COMMIT] " + datetime.now().isoformat() +
                   " committed=" + str(len(results["committed"])) +
                   " clean=" + str(len(results["clean"])))
        with open(STUDIO + "/claude-status.txt", "a", encoding="utf-8") as f:
            f.write(summary + "\n")
    except: pass

    # Heartbeat
    sys.path.insert(0, STUDIO)
    try:
        from utilities.heartbeat import write as hb_write
        hb_write("git-commit", "clean" if not results["error"] else "flagged",
                 "committed=" + str(len(results["committed"])) +
                 " errors=" + str(len(results["error"])))
    except Exception as e:
        log("[heartbeat] " + str(e)[:60])

if __name__ == "__main__":
    main()
