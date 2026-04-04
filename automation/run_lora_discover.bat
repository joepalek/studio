@echo off
:: Expected runtime: 3 minutes. TTL watchdog: 5 minutes (Hamilton Rule)
cd /d "G:\My Drive\Projects\_studio\automation"
python studio_automation.py --mode lora-discover >> studio_automation.log 2>&1
