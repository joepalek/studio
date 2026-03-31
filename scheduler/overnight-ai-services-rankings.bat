@echo off
cd /d "G:\My Drive\Projects\_studio"
set PYTHONIOENCODING=utf-8
python "G:\My Drive\Projects\_studio\ai_services_rankings.py" >> "G:\My Drive\Projects\_studio\scheduler\logs\ai-services-rankings.log" 2>&1
