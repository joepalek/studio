# _STUDIO

## What It Is
The central Studio dashboard and utilities hub — studio.html (project launcher/agent roster/inbox), session_logger.py, workflow tooling, scheduler, and status infrastructure (status.json → GitHub Pages + Supabase).

## Status
Progress: 65%
Last Updated: 2026-03-20

## Stack
Python 3, vanilla JS/HTML, Google Drive API, Supabase (REST), GitHub Pages, Windows Task Scheduler, git

## Completed
- studio.html: Drive Refresh replace-not-append (ghost items fixed)
- session_logger.py: update_status() + complete_task() + log_action() full API
- status.json: v-increment field added (CDN cache bust)
- Supabase session_status table populated; session_logger dual-writes on every update_status()
- status-page.html deployed to GitHub Pages
- utilities layer: unicode_safe, ollama_utils, gemini_utils, workflow_hook complete
- inbox-manager built and syncing (31 active items)
- standing-rules.json: 11 rules loaded
- workflow-intelligence.md built
- git-commit-agent.md wired into SESSION END PROTOCOL
- sysguard project initialized
- watchdog project initialized
- ghost-book git initialized; Pass 2 complete (161 viable, 105 PD)
- whiteboard: 30 items scored

## In Progress
- VS Code studio Drive refresh shows only 5 items (Opera shows 43) — token/auth issue in embedded browser

## Next Action
Fix VS Code studio Drive refresh (check token mismatch in VS Code localStorage vs Opera), then review ghost-book 161 viable candidates

## Blockers
- scheduler register_tasks.py needs admin terminal (user must run manually)
- VS Code studio partial refresh (5 items vs 43 in Opera)

## Session Log
- 2026-03-20: refreshFromDrive() analysis — listProjectSubfolders pageSize=50 confirmed; ghost-item fix is REPLACE-not-APPEND (filter approach, committed); VS Code 5-item bug identified as likely token-state issue
- 2026-03-20: Supabase session_status table populated; session_logger.py updated to dual-write status.json + Supabase on every update_status()
- 2026-03-20: status.json v-increment field added; status-page.html deployed; pending list cleaned (4 completed items removed, 5 new items added)
- 2026-03-20: Session end — all _studio changes committed and pushed (33c490b)
