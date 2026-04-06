@echo off
cd /d "G:\My Drive\Projects\_studio"
if not exist "%~dp0logs" mkdir "%~dp0logs"
echo [%date% %time%] WhiteboardScorer starting >> "G:\My Drive\Projects\_studio\scheduler\logs\whiteboard-scorer.log"
set PYTHONIOENCODING=utf-8
python "G:\My Drive\Projects\_studio\run-agent.py" whiteboard-scorer >> "G:\My Drive\Projects\_studio\scheduler\logs\whiteboard-scorer.log" 2>&1
echo [%date% %time%] WhiteboardScorer done >> "G:\My Drive\Projects\_studio\scheduler\logs\whiteboard-scorer.log"
