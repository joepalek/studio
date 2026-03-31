@echo off
REM ============================================================================
REM CX Agent - Task Scheduler Setup Script
REM ============================================================================
REM
REM This script creates 2 automated tasks:
REM 1. CX_Agent_Daily_Scan - runs every day at 2 AM UTC
REM 2. CX_Agent_Hourly_Monitor - runs every hour
REM
REM Usage: Right-click → "Run as administrator"
REM
REM ============================================================================

setlocal enabledelayedexpansion

echo.
echo ============================================================================
echo CX Agent - Task Scheduler Setup
echo ============================================================================
echo.

REM Check if running as admin
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: This script must be run as Administrator.
    echo Please right-click and select "Run as administrator"
    pause
    exit /b 1
)

REM Get current directory
cd /d "%~dp0"
set "INSTALL_DIR=%cd%"

echo Installation directory: %INSTALL_DIR%
echo.

REM Verify cx_agent.py exists
if not exist "cx_agent.py" (
    echo ERROR: cx_agent.py not found in %INSTALL_DIR%
    pause
    exit /b 1
)

echo [Step 1/2] Creating Task 1: CX_Agent_Daily_Scan (2 AM UTC daily)
echo.

schtasks /create /tn "CX_Agent_Daily_Scan" ^
    /tr "python \"!INSTALL_DIR!\cx_agent.py\" --mode daily_scan" ^
    /sc daily /st 02:00 ^
    /f /rl highest

if %errorlevel% equ 0 (
    echo   ✓ Task created successfully
) else (
    echo   ✗ Failed to create task (may already exist)
)

echo.
echo [Step 2/2] Creating Task 2: CX_Agent_Hourly_Monitor (every 1 hour)
echo.

schtasks /create /tn "CX_Agent_Hourly_Monitor" ^
    /tr "python \"!INSTALL_DIR!\cx_agent.py\" --mode monitor --hours 1" ^
    /sc hourly /mo 1 ^
    /f /rl highest

if %errorlevel% equ 0 (
    echo   ✓ Task created successfully
) else (
    echo   ✗ Failed to create task (may already exist)
)

echo.
echo ============================================================================
echo Task Scheduler Setup Complete!
echo ============================================================================
echo.
echo Tasks created:
echo   1. CX_Agent_Daily_Scan       - Every day at 02:00 UTC
echo   2. CX_Agent_Hourly_Monitor   - Every hour
echo.
echo To verify tasks were created:
echo   1. Open Task Scheduler (taskschd.msc)
echo   2. Navigate to Task Scheduler Library
echo   3. Look for: CX_Agent_Daily_Scan and CX_Agent_Hourly_Monitor
echo.
echo To delete tasks later:
echo   schtasks /delete /tn "CX_Agent_Daily_Scan" /f
echo   schtasks /delete /tn "CX_Agent_Hourly_Monitor" /f
echo.
pause
