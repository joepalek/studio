# Register Job Source Discovery in Windows Task Scheduler
# Run this once to set up the nightly discovery job
# PowerShell must run as Administrator

$TaskName = "Job_Source_Discovery_Weekly"
$TaskPath = "\Studio\"
$ScriptPath = "G:\My Drive\Projects\_studio\job-source-discovery-scheduler.bat"
$TriggerTime = "06:00:00"  # 6 AM UTC = 1 AM EST
$Repeat = "Weekly"

# Check if task already exists
$ExistingTask = Get-ScheduledTask -TaskName $TaskName -TaskPath $TaskPath -ErrorAction SilentlyContinue

if ($ExistingTask) {
    Write-Host "Task already registered. Unregistering..."
    Unregister-ScheduledTask -TaskName $TaskName -TaskPath $TaskPath -Confirm:$false
}

# Create trigger (weekly at 6 AM UTC)
$Trigger = New-ScheduledTaskTrigger `
    -Weekly `
    -DaysOfWeek Wednesday `
    -At $TriggerTime

# Create action
$Action = New-ScheduledTaskAction `
    -Execute $ScriptPath

# Create principal (run as current user)
$Principal = New-ScheduledTaskPrincipal `
    -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType Interactive `
    -RunLevel Highest

# Create settings
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable

# Register the task
Register-ScheduledTask `
    -TaskName $TaskName `
    -TaskPath $TaskPath `
    -Trigger $Trigger `
    -Action $Action `
    -Principal $Principal `
    -Settings $Settings `
    -Force

Write-Host "✓ Task registered: $TaskName"
Write-Host "  Path: $TaskPath"
Write-Host "  Script: $ScriptPath"
Write-Host "  Schedule: Weekly Wednesday at 06:00 UTC (1 AM EST)"
Write-Host ""
Write-Host "To run immediately for testing:"
Write-Host "  Start-ScheduledTask -TaskName '$TaskName' -TaskPath '$TaskPath'"
