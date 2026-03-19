@echo off
cd /d "G:\My Drive\Projects\_studio"
if not exist "%~dp0logs" mkdir "%~dp0logs"
echo [%date% %time%] Supervisor check starting >> "G:\My Drive\Projects\_studio\scheduler\logs\supervisor-check.log"
claude --dangerously-skip-permissions -p "Load supervisor.md. Run health check and report. Summarize any completed background tasks." >> "G:\My Drive\Projects\_studio\scheduler\logs\supervisor-check.log" 2>&1
echo [%date% %time%] Done >> "G:\My Drive\Projects\_studio\scheduler\logs\supervisor-check.log"
