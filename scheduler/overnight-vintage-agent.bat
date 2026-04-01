@echo off
cd /d "G:\My Drive\Projects\_studio"
if not exist "%~dp0logs" mkdir "%~dp0logs"
echo [%date% %time%] Vintage Agent starting >> "G:\My Drive\Projects\_studio\scheduler\logs\overnight-vintage-agent.log"
set PYTHONIOENCODING=utf-8
python "G:\My Drive\Projects\_studio\vintage_agent.py" >> "G:\My Drive\Projects\_studio\scheduler\logs\overnight-vintage-agent.log" 2>&1
echo [%date% %time%] Done >> "G:\My Drive\Projects\_studio\scheduler\logs\overnight-vintage-agent.log"
