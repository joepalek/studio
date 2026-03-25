@echo off
cd /d "G:\My Drive\Projects\_studio"
if not exist "%~dp0logs" mkdir "%~dp0logs"
echo [%date% %time%] Auto-answer agent starting >> "G:\My Drive\Projects\_studio\scheduler\logs\overnight-auto-answer.log"
claude --dangerously-skip-permissions -p "Load auto-answer.md. Run the full triage pass against the current inbox. Write a summary of items auto-resolved vs items escalated to G:\My Drive\Projects\_studio\claude-status.txt with timestamp prefix [AUTO-ANSWER]." >> "G:\My Drive\Projects\_studio\scheduler\logs\overnight-auto-answer.log" 2>&1
echo [%date% %time%] Done >> "G:\My Drive\Projects\_studio\scheduler\logs\overnight-auto-answer.log"
