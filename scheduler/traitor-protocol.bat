@echo off
cd /d "G:\My Drive\Projects\_studio"
if not exist "G:\My Drive\Projects\_studio\scheduler\logs" mkdir "G:\My Drive\Projects\_studio\scheduler\logs"
echo [%date% %time%] Traitor Protocol starting >> "G:\My Drive\Projects\_studio\scheduler\logs\traitor-protocol.log"
set PYTHONIOENCODING=utf-8
python "G:\My Drive\Projects\_studio\traitor_protocol.py" >> "G:\My Drive\Projects\_studio\scheduler\logs\traitor-protocol.log" 2>&1
echo [%date% %time%] Done >> "G:\My Drive\Projects\_studio\scheduler\logs\traitor-protocol.log"
