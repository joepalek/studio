@echo off
cd /d "G:\My Drive\Projects\job-match"
if not exist "G:\My Drive\Projects\_studio\scheduler\logs" mkdir "G:\My Drive\Projects\_studio\scheduler\logs"
echo [%date% %time%] Job source daily delta starting >> "G:\My Drive\Projects\_studio\scheduler\logs\overnight-job-delta.log"
python "G:\My Drive\Projects\job-match\update_scraper_config.py" >> "G:\My Drive\Projects\_studio\scheduler\logs\overnight-job-delta.log" 2>&1
echo [%date% %time%] Done >> "G:\My Drive\Projects\_studio\scheduler\logs\overnight-job-delta.log"
python -c "
import datetime
with open('G:/My Drive/Projects/_studio/claude-status.txt', 'a', encoding='utf-8') as f:
    f.write(f'[JOB-DELTA] {datetime.datetime.now().isoformat()} — Job source delta fetch complete.\n')
"
