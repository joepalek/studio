@echo off
:: Expected runtime: 2 minutes. TTL watchdog: 3 minutes (Hamilton Rule)
cd /d "G:\My Drive\Projects\_studio\automation"
python studio_automation.py --mode art-scan >> studio_automation.log 2>&1
