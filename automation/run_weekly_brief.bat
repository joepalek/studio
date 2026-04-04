@echo off
:: Expected runtime: 1 minute. TTL watchdog: 3 minutes (Hamilton Rule)
cd /d "G:\My Drive\Projects\_studio\automation"
python studio_automation.py --mode weekly-brief >> studio_automation.log 2>&1
