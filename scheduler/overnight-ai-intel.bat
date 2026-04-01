@echo off
cd /d "G:\My Drive\Projects\_studio"
if not exist "%~dp0logs" mkdir "%~dp0logs"
echo [%date% %time%] AI Intel starting >> "G:\My Drive\Projects\_studio\scheduler\logs\overnight-ai-intel.log"
set PYTHONIOENCODING=utf-8
python "G:\My Drive\Projects\_studio\ai_intel_run.py" >> "G:\My Drive\Projects\_studio\scheduler\logs\overnight-ai-intel.log" 2>&1
echo [%date% %time%] Done >> "G:\My Drive\Projects\_studio\scheduler\logs\overnight-ai-intel.log"
