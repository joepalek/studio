@echo off
REM Game Archaeology Weekly Run
REM Scheduled for: Monday 11:00 AM (off-peak for Claude API batch pricing)
REM Cost: ~$0.60/week

cd /d "G:\My Drive\Projects\_studio"

REM Run the weekly orchestration
python run_game_archaeology_weekly.py

REM Log output to heartbeat
echo [%date% %time%] Game Archaeology Weekly Run completed >> heartbeat-log.json

REM Commit results to Git
git add game_archaeology/
git commit -m "Game Archaeology Weekly Run - %date%"
git push origin main

exit /b 0
