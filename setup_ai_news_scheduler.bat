@echo off
REM AI News Scraper - Windows Task Scheduler Setup
REM Run this batch file ONCE to register the scheduled task
REM Then it will run daily at 8:15 AM (ArXiv update is 8 PM EST previous day)
REM and 10:00 AM (Reddit/GitHub check)

setlocal enabledelayedexpansion

REM Set your Python path and script location
set PYTHON_EXE=python
set SCRIPT_PATH=G:\My Drive\Projects\_studio\ai_news_scraper.py
set OUTPUT_DIR=G:\My Drive\Projects\_studio\news-digest

REM Create output directory if it doesn't exist
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

echo.
echo ====================================
echo AI News Scraper - Task Setup
echo ====================================
echo.

REM Task 1: ArXiv Daily (8:15 AM, captures overnight update)
echo [1/3] Creating ArXiv morning digest task...
schtasks /create /tn "Studio\ArXiv-Daily-Digest" ^
  /tr "cmd /c cd /d %OUTPUT_DIR% && %PYTHON_EXE% %SCRIPT_PATH% >> log.txt 2>&1" ^
  /sc daily /st 08:15 /f
if %ERRORLEVEL% EQU 0 (
  echo  ✓ ArXiv task created: Daily at 8:15 AM
) else (
  echo  ✗ Failed to create ArXiv task
)

REM Task 2: Reddit/GitHub alerts (10:00 AM)
echo [2/3] Creating Reddit/GitHub alerts task...
schtasks /create /tn "Studio\Reddit-GitHub-Alerts" ^
  /tr "cmd /c cd /d %OUTPUT_DIR% && %PYTHON_EXE% %SCRIPT_PATH% >> log.txt 2>&1" ^
  /sc daily /st 10:00 /f
if %ERRORLEVEL% EQU 0 (
  echo  ✓ Reddit/GitHub task created: Daily at 10:00 AM
) else (
  echo  ✗ Failed to create Reddit/GitHub task
)

REM Task 3: Run immediately for testing
echo [3/3] Running scraper now for testing...
cd /d "%OUTPUT_DIR%"
%PYTHON_EXE% %SCRIPT_PATH%

echo.
echo ====================================
echo Setup Complete
echo ====================================
echo.
echo Tasks registered:
echo   - Studio\ArXiv-Daily-Digest       (8:15 AM daily)
echo   - Studio\Reddit-GitHub-Alerts     (10:00 AM daily)
echo.
echo Output location: %OUTPUT_DIR%
echo.
echo To verify tasks:
echo   schtasks /query /tn "Studio\*"
echo.
echo To view task status:
echo   python task_status.py
echo.
pause
