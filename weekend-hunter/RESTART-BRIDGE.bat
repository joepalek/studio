@echo off
title Restart Studio Bridge
echo Stopping any existing bridge...
taskkill /f /im python.exe /fi "WINDOWTITLE eq studio_bridge*" 2>nul
timeout /t 2 /nobreak >nul
echo Starting Studio Bridge on port 11435...
start "studio_bridge" /min python "G:\My Drive\Projects\_studio\studio_bridge.py"
timeout /t 3 /nobreak >nul
echo Bridge is running. You can minimize this window.
echo.
pause
