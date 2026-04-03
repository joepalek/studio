@echo off
title Register Weekend Hunter Task
echo ============================================
echo  Weekend Hunter - Task Scheduler Setup
echo ============================================
echo.
echo Registering Friday 11pm scrape task...
echo.
schtasks /create /tn "WeekendHunterFullScrape" /tr "cmd /c \"G:\My Drive\Projects\_studio\weekend-hunter\run-full-scrape.bat\"" /sc WEEKLY /d FRI /st 23:00 /f /rl HIGHEST
if %errorlevel% equ 0 (
    echo.
    echo SUCCESS! Task registered.
    echo Every Friday at 11:00 PM the scraper will run automatically.
) else (
    echo.
    echo Could not register at HIGH level, trying standard...
    schtasks /create /tn "WeekendHunterFullScrape" /tr "cmd /c \"G:\My Drive\Projects\_studio\weekend-hunter\run-full-scrape.bat\"" /sc WEEKLY /d FRI /st 23:00 /f
    echo Done.
)
echo.
pause
