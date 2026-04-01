@echo off
cd /d "G:\My Drive\Projects\_studio"
if not exist "%~dp0logs" mkdir "%~dp0logs"
echo [%date% %time%] CheckDrift starting >> "G:\My Drive\Projects\_studio\scheduler\logs\overnight-check-drift.log"
set PYTHONIOENCODING=utf-8
python "G:\My Drive\Projects\_studio\check-drift.py" >> "G:\My Drive\Projects\_studio\scheduler\logs\overnight-check-drift.log" 2>&1
echo [%date% %time%] Done >> "G:\My Drive\Projects\_studio\scheduler\logs\overnight-check-drift.log"
