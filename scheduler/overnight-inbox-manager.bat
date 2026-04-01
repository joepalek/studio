@echo off
cd /d "G:\My Drive\Projects\_studio"
if not exist "%~dp0logs" mkdir "%~dp0logs"
echo [%date% %time%] InboxManager starting >> "G:\My Drive\Projects\_studio\scheduler\logs\overnight-inbox-manager.log"
set PYTHONIOENCODING=utf-8
python "G:\My Drive\Projects\_studio\run_inbox_sync.py" >> "G:\My Drive\Projects\_studio\scheduler\logs\overnight-inbox-manager.log" 2>&1
echo [%date% %time%] Done >> "G:\My Drive\Projects\_studio\scheduler\logs\overnight-inbox-manager.log"
