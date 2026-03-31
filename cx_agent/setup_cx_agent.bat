@echo off
REM ============================================================================
REM CX Agent - Setup & Test Script for Google Drive
REM ============================================================================
REM
REM This script:
REM 1. Verifies Python is installed
REM 2. Tests CX Agent with a daily_scan
REM 3. Reports results
REM
REM Usage: Right-click this file → "Run as administrator"
REM
REM ============================================================================

echo.
echo ============================================================================
echo CX Agent - Google Drive Setup Test
echo ============================================================================
echo.

REM Get current directory (should be cx_agent folder)
cd /d "%~dp0"
set "INSTALL_DIR=%cd%"

echo Current directory: %INSTALL_DIR%
echo.

REM Check if we're in the cx_agent folder
if not exist "asset_distribution_manifest.json" (
    echo ERROR: asset_distribution_manifest.json not found in current directory
    echo.
    echo Please make sure you:
    echo 1. Downloaded cx_agent_complete.py and asset_distribution_manifest_complete.json
    echo 2. Renamed them to cx_agent.py and asset_distribution_manifest.json
    echo 3. Placed them in: %INSTALL_DIR%
    echo.
    pause
    exit /b 1
)

if not exist "cx_agent.py" (
    echo ERROR: cx_agent.py not found in current directory
    echo.
    echo Please rename cx_agent_complete.py to cx_agent.py
    echo.
    pause
    exit /b 1
)

echo [Step 1/3] Verifying Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo   ERROR: Python not found
    echo.
    echo   Please install Python from https://www.python.org/
    echo   Make sure to check "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do set "PYTHON_VER=%%i"
echo   ✓ Found: %PYTHON_VER%
echo.

REM Create data and logs folders if they don't exist
echo [Step 2/3] Creating folders...
if not exist "data" mkdir data
if not exist "logs" mkdir logs
echo   ✓ data/ and logs/ folders ready
echo.

REM Test CX Agent
echo [Step 3/3] Running CX Agent test (daily_scan)...
echo.
python cx_agent.py --mode daily_scan
echo.

if %errorlevel% equ 0 (
    echo ============================================================================
    echo SUCCESS! CX Agent is working
    echo ============================================================================
    echo.
    echo Files created:
    echo   - data/asset_creation_log.json
    echo   - logs/cx_agent.log
    echo.
    echo Next steps:
    echo 1. Set up Windows Task Scheduler tasks (see CX_Agent_GDrive_Installation_Guide.md, Step 6)
    echo 2. Or run this command daily at 2 AM:
    echo    python "%INSTALL_DIR%\cx_agent.py" --mode daily_scan
    echo.
) else (
    echo ============================================================================
    echo ERROR! CX Agent test failed
    echo ============================================================================
    echo.
    echo Check the error messages above for details
    echo.
)

pause
