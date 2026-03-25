@echo off
cd /d "G:\My Drive\Projects\_studio"
if not exist "%~dp0logs" mkdir "%~dp0logs"
echo [%date% %time%] Vintage Agent starting >> "G:\My Drive\Projects\_studio\scheduler\logs\overnight-vintage-agent.log"
claude --dangerously-skip-permissions -p "Load vintage-agent.md. Fill any missing decade profiles. Write a summary of what was filled to G:\My Drive\Projects\_studio\claude-status.txt with timestamp prefix [VINTAGE-AGENT]." >> "G:\My Drive\Projects\_studio\scheduler\logs\overnight-vintage-agent.log" 2>&1
echo [%date% %time%] Done >> "G:\My Drive\Projects\_studio\scheduler\logs\overnight-vintage-agent.log"
