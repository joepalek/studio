@echo off
REM Weekend Hunter - Delta Update (run manually when you're out hunting)
cd /d "G:\My Drive\Projects\_studio"
python weekend-hunter\weekend_hunter_agent.py --mode delta >> weekend-hunter\hunter.log 2>&1
echo Done. Check weekend-hunter\hunt-delta.json for new listings.
pause
