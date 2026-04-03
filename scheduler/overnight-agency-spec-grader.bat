@echo off
cd /d "G:\My Drive\Projects\_studio\agency\spec-queue"
if not exist "G:\My Drive\Projects\_studio\scheduler\logs" mkdir "G:\My Drive\Projects\_studio\scheduler\logs"
echo [%date% %time%] Spec Grader starting >> "G:\My Drive\Projects\_studio\scheduler\logs\overnight-agency-spec-grader.log"
set PYTHONIOENCODING=utf-8
python "G:\My Drive\Projects\_studio\agency\spec-queue\spec_auto_grader.py" >> "G:\My Drive\Projects\_studio\scheduler\logs\overnight-agency-spec-grader.log" 2>&1
echo [%date% %time%] Done >> "G:\My Drive\Projects\_studio\scheduler\logs\overnight-agency-spec-grader.log"
