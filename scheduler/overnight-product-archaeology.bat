@echo off
cd /d "G:\My Drive\Projects\_studio"
if not exist "%~dp0logs" mkdir "%~dp0logs"
echo [%date% %time%] Product Archaeology scoring starting >> "G:\My Drive\Projects\_studio\scheduler\logs\overnight-product-archaeology.log"
set PYTHONIOENCODING=utf-8
python "G:\My Drive\Projects\_studio\whiteboard_score.py" >> "G:\My Drive\Projects\_studio\scheduler\logs\overnight-product-archaeology.log" 2>&1
echo [%date% %time%] Done >> "G:\My Drive\Projects\_studio\scheduler\logs\overnight-product-archaeology.log"
python -c "import datetime; open('G:/My Drive/Projects/_studio/claude-status.txt','a',encoding='utf-8').write('[PRODUCT-ARCHAEOLOGY] ' + datetime.datetime.now().isoformat() + ' -- Scoring pass complete.\n')"
