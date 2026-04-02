@echo off
REM Job Source Discovery - Task Scheduler Wrapper
REM Runs job-source-discovery-launcher.py
REM Scheduled: Daily 06:00 UTC (1:00 AM EST)
REM Status: READY

setlocal enabledelayedexpansion

set STUDIO_PATH=G:\My Drive\Projects\_studio
set SCRIPT=%STUDIO_PATH%\job-source-discovery-launcher.py
set LOG_DIR=%STUDIO_PATH%\logs
set LOG_FILE=%LOG_DIR%\job-source-discovery-!date:~10,4!!date:~4,2!!date:~7,2!-!time:~0,2!!time:~3,2!.log

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

echo [%date% %time%] Job Source Discovery - Phase 1 Starting >> "%LOG_FILE%"
echo. >> "%LOG_FILE%"

python "%SCRIPT%" >> "%LOG_FILE%" 2>&1

echo. >> "%LOG_FILE%"
echo [%date% %time%] Job Source Discovery Complete >> "%LOG_FILE%"

REM Email notification
powershell -Command "Write-Host 'Job Source Discovery completed. Check log: %LOG_FILE%'"

exit /b 0
