@echo off
cd /d "G:\My Drive\Projects\_studio"
if not exist "scheduler\logs" mkdir "scheduler\logs"
echo [%date% %time%] Janitor starting >> "G:\My Drive\Projects\_studio\scheduler\logs\overnight-janitor.log"
set PYTHONIOENCODING=utf-8
python "G:\My Drive\Projects\_studio\janitor_run.py" >> "G:\My Drive\Projects\_studio\scheduler\logs\overnight-janitor.log" 2>&1
echo [%date% %time%] Done >> "G:\My Drive\Projects\_studio\scheduler\logs\overnight-janitor.log"
