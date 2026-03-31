@echo off
cd /d "G:\My Drive\Projects\_studio"
set PYTHONIOENCODING=utf-8
python "G:\My Drive\Projects\_studio\inject_sidebar_data.py" >> "G:\My Drive\Projects\_studio\scheduler\logs\sidebar-inject.log" 2>&1
