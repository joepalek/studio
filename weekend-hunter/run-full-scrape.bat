@echo off
REM Weekend Hunter - Full Scrape (runs Friday nights via Task Scheduler)
cd /d "G:\My Drive\Projects\_studio"
python weekend-hunter\weekend_hunter_agent.py --mode full >> weekend-hunter\hunter.log 2>&1
