@echo off
cd /d "G:\My Drive\Projects\_studio\agency\spec-queue"
if not exist "G:\My Drive\Projects\_studio\scheduler\logs" mkdir "G:\My Drive\Projects\_studio\scheduler\logs"
echo [%date% %time%] Spec Generator starting >> "G:\My Drive\Projects\_studio\scheduler\logs\overnight-agency-spec-generator.log"
set PYTHONIOENCODING=utf-8
python "G:\My Drive\Projects\_studio\agency\spec-queue\character-spec-generator.py" >> "G:\My Drive\Projects\_studio\scheduler\logs\overnight-agency-spec-generator.log" 2>&1
echo [%date% %time%] Done >> "G:\My Drive\Projects\_studio\scheduler\logs\overnight-agency-spec-generator.log"
