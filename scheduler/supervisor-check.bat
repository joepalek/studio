@echo off
cd /d "G:\My Drive\Projects\_studio"
if not exist "%~dp0logs" mkdir "%~dp0logs"
echo [%date% %time%] Supervisor check starting >> "G:\My Drive\Projects\_studio\scheduler\logs\supervisor-check.log"
python "G:\My Drive\Projects\_studio\supervisor_check.py" >> "G:\My Drive\Projects\_studio\scheduler\logs\supervisor-check.log" 2>&1
echo [%date% %time%] Done >> "G:\My Drive\Projects\_studio\scheduler\logs\supervisor-check.log"
