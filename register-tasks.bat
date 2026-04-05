@echo off
echo Registering StudioWhiteboardScanner...
schtasks /create /tn "StudioWhiteboardScanner" /tr "\"G:\My Drive\Projects\_studio\scheduler\run-whiteboard-scanner.bat\"" /sc DAILY /st 04:00 /f
if %errorlevel%==0 (echo [OK] StudioWhiteboardScanner registered) else (echo [FAIL] StudioWhiteboardScanner)

echo Registering StudioSEOAgent...
schtasks /create /tn "StudioSEOAgent" /tr "\"G:\My Drive\Projects\_studio\scheduler\run-seo-agent.bat\"" /sc WEEKLY /d MON /st 06:00 /f
if %errorlevel%==0 (echo [OK] StudioSEOAgent registered) else (echo [FAIL] StudioSEOAgent)

echo.
echo Verifying...
schtasks /query /tn "StudioWhiteboardScanner" /fo LIST
schtasks /query /tn "StudioSEOAgent" /fo LIST
pause
