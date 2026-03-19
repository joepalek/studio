@echo off
cd /d "G:\My Drive\Projects\_studio"
if not exist "%~dp0logs" mkdir "%~dp0logs"
echo [%date% %time%] Ghost book rescan starting >> "G:\My Drive\Projects\_studio\scheduler\logs\ghost-book-rescan.log"
python "G:\My Drive\Projects\ghost-book\pass1_find_candidates.py" >> "G:\My Drive\Projects\_studio\scheduler\logs\ghost-book-rescan.log" 2>&1
python "G:\My Drive\Projects\ghost-book\pass1_atlantis_lore.py" >> "G:\My Drive\Projects\_studio\scheduler\logs\ghost-book-rescan.log" 2>&1
echo [%date% %time%] Done >> "G:\My Drive\Projects\_studio\scheduler\logs\ghost-book-rescan.log"
