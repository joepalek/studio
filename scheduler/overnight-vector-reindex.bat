@echo off
cd /d "G:\My Drive\Projects\_studio"
if not exist "%~dp0logs" mkdir "%~dp0logs"
echo [%date% %time%] VectorReindex starting >> "G:\My Drive\Projects\_studio\scheduler\logs\vector-reindex.log"
set PYTHONIOENCODING=utf-8
python "G:\My Drive\Projects\_studio\vector_reindex.py" >> "G:\My Drive\Projects\_studio\scheduler\logs\vector-reindex.log" 2>&1
echo [%date% %time%] Done >> "G:\My Drive\Projects\_studio\scheduler\logs\vector-reindex.log"
