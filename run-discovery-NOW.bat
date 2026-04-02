@echo off
REM Run Job Source Discovery NOW (Test/Immediate Launch)
REM Use this to start Phase 1 discovery immediately instead of waiting for scheduler

setlocal enabledelayedexpansion

set STUDIO_PATH=G:\My Drive\Projects\_studio
set SCRIPT=%STUDIO_PATH%\job-source-discovery-launcher.py
set LOG_DIR=%STUDIO_PATH%\logs
set TIMESTAMP=%date:~10,4%%date:~4,2%%date:~7,2%-%time:~0,2%%time:~3,2%
set LOG_FILE=%LOG_DIR%\job-source-discovery-RUN-!TIMESTAMP!.log

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

echo ========================================
echo Job Source Discovery - IMMEDIATE RUN
echo Started: %date% %time%
echo ========================================
echo.
echo Log: %LOG_FILE%
echo.

if not exist "%SCRIPT%" (
    echo ERROR: Script not found: %SCRIPT%
    exit /b 1
)

REM Run Python script and redirect output to log file
python "%SCRIPT%" >> "%LOG_FILE%" 2>&1

echo.
echo ========================================
echo Job Source Discovery Complete
echo Log: %LOG_FILE%
echo ========================================

REM Show last 20 lines of log
echo.
echo --- Last Output ---
echo.
powershell -Command "Get-Content '%LOG_FILE%' -Tail 20"

pause
