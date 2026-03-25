@echo off
cd /d "G:\My Drive\Projects\_studio"
if not exist "%~dp0logs" mkdir "%~dp0logs"
echo [%date% %time%] Whiteboard scoring pass starting >> "G:\My Drive\Projects\_studio\scheduler\logs\overnight-whiteboard-score.log"
python "G:\My Drive\Projects\_studio\whiteboard_score.py" >> "G:\My Drive\Projects\_studio\scheduler\logs\overnight-whiteboard-score.log" 2>&1
echo [%date% %time%] Done >> "G:\My Drive\Projects\_studio\scheduler\logs\overnight-whiteboard-score.log"
python -c "
import datetime
with open('G:/My Drive/Projects/_studio/claude-status.txt', 'a', encoding='utf-8') as f:
    f.write(f'[WHITEBOARD-SCORE] {datetime.datetime.now().isoformat()} — Whiteboard scoring pass complete.\n')
"
