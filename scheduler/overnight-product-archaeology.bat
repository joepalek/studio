@echo off
cd /d "G:\My Drive\Projects\_studio"
if not exist "%~dp0logs" mkdir "%~dp0logs"
echo [%date% %time%] Product Archaeology scoring starting >> "G:\My Drive\Projects\_studio\scheduler\logs\overnight-product-archaeology.log"
python "G:\My Drive\Projects\_studio\whiteboard_score.py" >> "G:\My Drive\Projects\_studio\scheduler\logs\overnight-product-archaeology.log" 2>&1
echo [%date% %time%] Done >> "G:\My Drive\Projects\_studio\scheduler\logs\overnight-product-archaeology.log"
python -c "
import datetime
with open('G:/My Drive/Projects/_studio/claude-status.txt', 'a', encoding='utf-8') as f:
    f.write(f'[PRODUCT-ARCHAEOLOGY] {datetime.datetime.now().isoformat()} — Whiteboard scoring pass complete. See whiteboard.json for updated scores.\n')
"
