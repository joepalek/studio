# Register Weekend Hunter full scrape as a Task Scheduler job
# Runs every Friday at 11:00 PM
# Run this script once as Administrator

$taskName    = "WeekendHunterFullScrape"
$scriptPath  = "G:\My Drive\Projects\_studio\weekend-hunter\run-full-scrape.bat"
$logPath     = "G:\My Drive\Projects\_studio\weekend-hunter\task-scheduler.log"

$action  = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$scriptPath`" >> `"$logPath`" 2>&1"
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Friday -At "11:00PM"
$settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Hours 2) -StartWhenAvailable

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger `
    -Settings $settings -RunLevel Highest -Force

Write-Host "Weekend Hunter task registered: $taskName" -ForegroundColor Green
Write-Host "Runs every Friday at 11:00 PM"
