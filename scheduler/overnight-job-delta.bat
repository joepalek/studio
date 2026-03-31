@echo off
cd /d "G:\My Drive\Projects\job-match"
if not exist "G:\My Drive\Projects\_studio\scheduler\logs" mkdir "G:\My Drive\Projects\_studio\scheduler\logs"
echo [%date% %time%] Job daily harvest starting >> "G:\My Drive\Projects\_studio\scheduler\logs\overnight-job-delta.log"
set PYTHONIOENCODING=utf-8
python "G:\My Drive\Projects\job-match\job_daily_harvest.py" >> "G:\My Drive\Projects\_studio\scheduler\logs\overnight-job-delta.log" 2>&1
echo [%date% %time%] Done >> "G:\My Drive\Projects\_studio\scheduler\logs\overnight-job-delta.log"
