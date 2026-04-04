# register_constraint_audit.ps1
# Registers constraint_audit.py as a weekly Task Scheduler job
# Run once as Administrator: .\register_constraint_audit.ps1

$taskName    = "Studio\ConstraintAudit"
$scriptPath  = "G:\My Drive\Projects\_studio\constraint_audit.py"
$pythonPath  = "python"
$workingDir  = "G:\My Drive\Projects\_studio"
$logFile     = "G:\My Drive\Projects\_studio\logs\constraint-audit.log"

$action  = New-ScheduledTaskAction `
    -Execute $pythonPath `
    -Argument $scriptPath `
    -WorkingDirectory $workingDir

# Every Monday at 07:00
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At "07:00"

$settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 5) `
    -RestartCount 1 `
    -RestartInterval (New-TimeSpan -Minutes 2) `
    -StartWhenAvailable

Register-ScheduledTask `
    -TaskName  $taskName `
    -Action    $action `
    -Trigger   $trigger `
    -Settings  $settings `
    -RunLevel  Highest `
    -Force

Write-Host "Registered: $taskName -- runs every Monday 07:00"
Write-Host "Log output: $logFile"
Write-Host "Run now to test: Start-ScheduledTask -TaskName $taskName"
