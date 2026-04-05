# register-new-tasks.ps1
# Registers WhiteboardScanner (daily 4AM) and SEO Agent (Monday 6AM)
# Run once: powershell -ExecutionPolicy Bypass -File register-new-tasks.ps1

$studio = "G:\My Drive\Projects\_studio"

# Task 1 — Whiteboard Scanner (daily 4:00 AM)
$action1 = New-ScheduledTaskAction `
    -Execute "cmd.exe" `
    -Argument "/c `"$studio\scheduler\whiteboard-scanner.bat`""
$trigger1 = New-ScheduledTaskTrigger -Daily -At "04:00AM"
$settings1 = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Minutes 10) -RunOnlyIfNetworkAvailable $false
Register-ScheduledTask `
    -TaskName "StudioWhiteboardScanner" `
    -Action $action1 `
    -Trigger $trigger1 `
    -Settings $settings1 `
    -Description "Nightly whiteboard status sync — closes done items, writes morning report" `
    -Force
Write-Host "[OK] StudioWhiteboardScanner registered — daily 4:00 AM"

# Task 2 — SEO Agent (every Monday 6:00 AM)
$action2 = New-ScheduledTaskAction `
    -Execute "cmd.exe" `
    -Argument "/c `"$studio\scheduler\seo-agent.bat`""
$trigger2 = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At "06:00AM"
$settings2 = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Minutes 15) -RunOnlyIfNetworkAvailable $true
Register-ScheduledTask `
    -TaskName "StudioSEOAgent" `
    -Action $action2 `
    -Trigger $trigger2 `
    -Settings $settings2 `
    -Description "Weekly SEO and internet intelligence sweep — keyword gaps, ghost page triggers, social angles" `
    -Force
Write-Host "[OK] StudioSEOAgent registered — every Monday 6:00 AM"

Write-Host ""
Write-Host "Done. Verify with: schtasks /query /tn StudioWhiteboardScanner"
Write-Host "               and: schtasks /query /tn StudioSEOAgent"
