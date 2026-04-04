@echo off
REM Simple script to start sidebar_bridge.py

cd /d "G:\My Drive\Projects\_studio\orchestrator"

echo Starting Studio Sidebar Bridge...
echo.
echo This window should say: "Running on http://127.0.0.1:11436/"
echo.
echo Keep this window open. Close it to stop the service.
echo.

python sidebar_bridge.py

pause
