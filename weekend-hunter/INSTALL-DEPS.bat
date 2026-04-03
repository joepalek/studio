@echo off
title Weekend Hunter - Install Dependencies
echo ============================================
echo  Weekend Hunter - Installing Python Packages
echo ============================================
echo.
echo This will install the required packages...
echo.
pip install selenium requests beautifulsoup4 --break-system-packages
if %errorlevel% neq 0 (
    echo.
    echo Trying without --break-system-packages flag...
    pip install selenium requests beautifulsoup4
)
echo.
echo ============================================
echo  Done! You can close this window.
echo ============================================
pause
