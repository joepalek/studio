@echo off
cd /d "G:\My Drive\Projects\ghost-book"
if not exist "G:\My Drive\Projects\_studio\scheduler\logs" mkdir "G:\My Drive\Projects\_studio\scheduler\logs"
echo [%date% %time%] Ghost Book Pass 3 starting >> "G:\My Drive\Projects\_studio\scheduler\logs\overnight-ghost-book-pass3.log"
python "G:\My Drive\Projects\ghost-book\pass2_validate.py" >> "G:\My Drive\Projects\_studio\scheduler\logs\overnight-ghost-book-pass3.log" 2>&1
echo [%date% %time%] Pass 2 complete, checking concat opportunities >> "G:\My Drive\Projects\_studio\scheduler\logs\overnight-ghost-book-pass3.log"
claude --dangerously-skip-permissions -p "Read G:\My Drive\Projects\ghost-book\concat-opportunities.json. Evaluate top concatenation opportunities for ghost-book project. Write a summary of top 5 candidates to G:\My Drive\Projects\_studio\claude-status.txt with timestamp prefix [GHOST-BOOK-PASS3]." >> "G:\My Drive\Projects\_studio\scheduler\logs\overnight-ghost-book-pass3.log" 2>&1
echo [%date% %time%] Done >> "G:\My Drive\Projects\_studio\scheduler\logs\overnight-ghost-book-pass3.log"
