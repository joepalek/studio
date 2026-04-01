@echo off
cd /d "G:\My Drive\Projects\_studio"
if not exist "%~dp0logs" mkdir "%~dp0logs"
echo [%date% %time%] Daily briefing starting >> "G:\My Drive\Projects\_studio\scheduler\logs\orchestrator-briefing.log"
claude --dangerously-skip-permissions -p "Load ai-gateway.md and orchestrator.md. Run daily briefing now. Save output to orchestrator-briefing.json." >> "G:\My Drive\Projects\_studio\scheduler\logs\orchestrator-briefing.log" 2>&1
python "G:\My Drive\Projects\_studio\populate_orchestrator_plan.py" >> "G:\My Drive\Projects\_studio\scheduler\logs\orchestrator-briefing.log" 2>&1
echo [%date% %time%] Done >> "G:\My Drive\Projects\_studio\scheduler\logs\orchestrator-briefing.log"
