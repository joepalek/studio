@echo off
cd /d "G:\My Drive\Projects\_studio"
if not exist "%~dp0logs" mkdir "%~dp0logs"
echo [%date% %time%] Auto-answer agent starting (Gemini Flash) >> "G:\My Drive\Projects\_studio\scheduler\logs\overnight-auto-answer.log"
python "G:\My Drive\Projects\_studio\auto_answer_gemini.py" >> "G:\My Drive\Projects\_studio\scheduler\logs\overnight-auto-answer.log" 2>&1
echo [%date% %time%] Done >> "G:\My Drive\Projects\_studio\scheduler\logs\overnight-auto-answer.log"
