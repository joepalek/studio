@echo off
cd /d "G:\My Drive\Projects\_studio"
if not exist "%~dp0logs" mkdir "%~dp0logs"
echo [%date% %time%] Nightly commit starting >> "G:\My Drive\Projects\_studio\scheduler\logs\nightly-commit.log"
claude --dangerously-skip-permissions -p "Load git-commit-agent.md. Commit all dirty projects now. Then load changelog-agent.md. Update changelogs for all changed projects." >> "G:\My Drive\Projects\_studio\scheduler\logs\nightly-commit.log" 2>&1
echo [%date% %time%] Done >> "G:\My Drive\Projects\_studio\scheduler\logs\nightly-commit.log"
