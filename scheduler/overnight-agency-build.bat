@echo off
cd /d "G:\My Drive\Projects\_studio\agency"
if not exist "G:\My Drive\Projects\_studio\scheduler\logs" mkdir "G:\My Drive\Projects\_studio\scheduler\logs"
echo [%date% %time%] Agency character batch build starting >> "G:\My Drive\Projects\_studio\scheduler\logs\overnight-agency-build.log"
set PYTHONIOENCODING=utf-8
python "G:\My Drive\Projects\_studio\agency\character_batch_builder.py" >> "G:\My Drive\Projects\_studio\scheduler\logs\overnight-agency-build.log" 2>&1
echo [%date% %time%] Done >> "G:\My Drive\Projects\_studio\scheduler\logs\overnight-agency-build.log"
