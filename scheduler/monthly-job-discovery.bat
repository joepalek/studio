@echo off
cd /d "G:\My Drive\Projects\job-match"
if not exist "G:\My Drive\Projects\_studio\scheduler\logs" mkdir "G:\My Drive\Projects\_studio\scheduler\logs"
echo [%date% %time%] Job source monthly discovery starting >> "G:\My Drive\Projects\_studio\scheduler\logs\monthly-job-discovery.log"
set PYTHONIOENCODING=utf-8
python "G:\My Drive\Projects\job-match\job_source_discovery_monthly.py" >> "G:\My Drive\Projects\_studio\scheduler\logs\monthly-job-discovery.log" 2>&1
echo [%date% %time%] Done >> "G:\My Drive\Projects\_studio\scheduler\logs\monthly-job-discovery.log"
