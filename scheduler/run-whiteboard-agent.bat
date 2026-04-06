@echo off
cd /d "G:\My Drive\Projects\_studio"
if not exist "%~dp0logs" mkdir "%~dp0logs"
echo [%date% %time%] WhiteboardAgent starting >> "G:\My Drive\Projects\_studio\scheduler\logs\whiteboard-agent.log"
set PYTHONIOENCODING=utf-8
python "G:\My Drive\Projects\_studio\run-agent.py" whiteboard-agent >> "G:\My Drive\Projects\_studio\scheduler\logs\whiteboard-agent.log" 2>&1
echo [%date% %time%] WhiteboardAgent done >> "G:\My Drive\Projects\_studio\scheduler\logs\whiteboard-agent.log"
