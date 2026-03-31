@echo off
cd /d "G:\My Drive\Projects\_studio"
python nightly_rollup.py >> "G:\My Drive\Projects\_studio\scheduler\logs\nightly-rollup.log" 2>&1
