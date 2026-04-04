@echo off
REM Setup Windows Task Scheduler to auto-start sidebar_bridge.py at login
REM Run this as Administrator

echo.
echo ============================================================================
echo SETTING UP AUTO-START FOR STUDIO SIDEBAR BRIDGE
echo ============================================================================
echo.

REM Check if admin
net session >nul 2>&1
if errorlevel 1 (
    echo ERROR: Must run as Administrator
    echo Right-click this file and select "Run as administrator"
    pause
    exit /b 1
)

REM Create Task Scheduler task
schtasks /create ^
    /tn "Studio Sidebar Bridge" ^
    /tr "python.exe G:\My Drive\Projects\_studio\orchestrator\sidebar_bridge.py" ^
    /sc onlogon ^
    /rl highest ^
    /f

if errorlevel 1 (
    echo ERROR: Failed to create task
    pause
    exit /b 1
)

echo.
echo ============================================================================
echo SUCCESS!
echo ============================================================================
echo.
echo Task created: "Studio Sidebar Bridge"
echo Trigger: At user login
echo.
echo The sidebar bridge will start automatically next time you log in.
echo.
echo To test it now, open Command Prompt and run:
echo   cd "G:\My Drive\Projects\_studio\orchestrator"
echo   python sidebar_bridge.py
echo.
pause
