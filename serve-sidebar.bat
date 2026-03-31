@echo off
title Studio Sidebar Server - Port 8765
cd /d "G:\My Drive\Projects\_studio"
echo Starting Studio Sidebar Server on http://localhost:8765
echo.
python "G:\My Drive\Projects\_studio\serve_sidebar_server.py"
pause
