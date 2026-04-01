@echo off
cd /d "G:\My Drive\Projects\_studio"
if not exist "G:\My Drive\Projects\_studio\scheduler\logs" mkdir "G:\My Drive\Projects\_studio\scheduler\logs"

echo [%date% %time%] SidebarBridge starting >> "G:\My Drive\Projects\_studio\scheduler\logs\sidebar-bridge.log"

:: Wait for Ollama to be available (up to 60 seconds)
set TRIES=0
:CHECK_OLLAMA
set /a TRIES+=1
curl -s -o nul http://localhost:11434/api/tags
if %errorlevel%==0 goto LAUNCH
if %TRIES% GEQ 12 goto LAUNCH
echo [%date% %time%] Waiting for Ollama... attempt %TRIES% >> "G:\My Drive\Projects\_studio\scheduler\logs\sidebar-bridge.log"
timeout /t 5 /nobreak >nul
goto CHECK_OLLAMA

:LAUNCH
:: Kill any existing bridge on port 11435
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":11435"') do (
    taskkill /PID %%a /F >nul 2>&1
)
timeout /t 2 /nobreak >nul

echo [%date% %time%] Launching bridge >> "G:\My Drive\Projects\_studio\scheduler\logs\sidebar-bridge.log"
python "G:\My Drive\Projects\_studio\studio_bridge.py" >> "G:\My Drive\Projects\_studio\scheduler\logs\sidebar-bridge.log" 2>&1
echo [%date% %time%] Bridge exited >> "G:\My Drive\Projects\_studio\scheduler\logs\sidebar-bridge.log"
