@echo off
cd /d "G:\My Drive\Projects\_studio"
if not exist "%~dp0logs" mkdir "%~dp0logs"
echo [%date% %time%] Nightly commit starting >> "G:\My Drive\Projects\_studio\scheduler\logs\nightly-commit.log"
set PYTHONIOENCODING=utf-8
python "G:\My Drive\Projects\_studio\git_commit.py" >> "G:\My Drive\Projects\_studio\scheduler\logs\nightly-commit.log" 2>&1
echo [%date% %time%] Done >> "G:\My Drive\Projects\_studio\scheduler\logs\nightly-commit.log"
