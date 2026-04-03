# Register Game Archaeology Daily Cycle with Windows Task Scheduler
# Run this script as Administrator to create the scheduled task

# Configuration
$TaskName = "Game Archaeology Daily Cycle"
$TaskPath = "\Game Archaeology\"
$PythonScript = "G:\My Drive\Projects\_studio\game_archaeology\run_orchestrator.py"
$WorkingDir = "G:\My Drive\Projects\_studio\game_archaeology"
$PythonExe = "python"  # Assumes python is in PATH

# Trigger: 2:00 AM UTC daily (adjust if needed)
$TriggerTime = "02:00:00"

Write-Host "=========================================="
Write-Host "Game Archaeology Task Scheduler Setup"
Write-Host "=========================================="
Write-Host ""

# Check if running as Administrator
$IsAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")
if (-not $IsAdmin) {
    Write-Host "ERROR: This script must be run as Administrator" -ForegroundColor Red
    Write-Host "Please run PowerShell as Administrator and try again"
    exit 1
}

Write-Host "Admin check: OK" -ForegroundColor Green
Write-Host ""

# Verify Python script exists
if (-not (Test-Path $PythonScript)) {
    Write-Host "ERROR: Script not found: $PythonScript" -ForegroundColor Red
    exit 1
}

Write-Host "Python script found: OK" -ForegroundColor Green
Write-Host "  Path: $PythonScript"
Write-Host ""

# Verify working directory exists
if (-not (Test-Path $WorkingDir)) {
    Write-Host "ERROR: Working directory not found: $WorkingDir" -ForegroundColor Red
    exit 1
}

Write-Host "Working directory found: OK" -ForegroundColor Green
Write-Host "  Path: $WorkingDir"
Write-Host ""

# Check if task already exists
$ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($ExistingTask) {
    Write-Host "WARNING: Task already exists" -ForegroundColor Yellow
    Write-Host "  Updating existing task..."
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

Write-Host ""
Write-Host "Creating Task Scheduler entry..."
Write-Host ""

# Create trigger (Daily at 2:00 AM UTC)
$Trigger = New-ScheduledTaskTrigger `
    -Daily `
    -At $TriggerTime `
    -DaysInterval 1

# Create action
$Action = New-ScheduledTaskAction `
    -Execute $PythonExe `
    -Argument $PythonScript `
    -WorkingDirectory $WorkingDir

# Create settings
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -MultipleInstances IgnoreNew

# Create principal (run with highest privileges)
$Principal = New-ScheduledTaskPrincipal -UserID "NT AUTHORITY\SYSTEM" -LogonType ServiceAccount -RunLevel Highest

# Register the task
try {
    Register-ScheduledTask `
        -TaskName $TaskName `
        -TaskPath $TaskPath `
        -Trigger $Trigger `
        -Action $Action `
        -Settings $Settings `
        -Principal $Principal `
        -Description "Game Archaeology: Daily crawler, legal assessment, and Supabase sync. Runs at 2:00 AM UTC daily." `
        -Force | Out-Null
    
    Write-Host "✓ Task registered successfully" -ForegroundColor Green
}
catch {
    Write-Host "✗ Failed to register task: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=========================================="
Write-Host "Task Details:"
Write-Host "=========================================="

$Task = Get-ScheduledTask -TaskName $TaskName
Write-Host "  Name: $($Task.TaskName)" -ForegroundColor Cyan
Write-Host "  Path: $($Task.TaskPath)" -ForegroundColor Cyan
Write-Host "  State: $($Task.State)" -ForegroundColor Cyan
Write-Host "  Trigger: Daily at $TriggerTime UTC" -ForegroundColor Cyan
Write-Host "  Script: $PythonScript" -ForegroundColor Cyan
Write-Host "  Working Dir: $WorkingDir" -ForegroundColor Cyan

Write-Host ""
Write-Host "=========================================="
Write-Host "✓ Setup Complete!"
Write-Host "=========================================="
Write-Host ""
Write-Host "Next Steps:"
Write-Host "  1. Open Task Scheduler: tasksched.msc"
Write-Host "  2. Navigate to: Task Scheduler Library\Game Archaeology\"
Write-Host "  3. Right-click task → Run (to test immediately)"
Write-Host "  4. Task will run automatically at 2:00 AM UTC daily"
Write-Host ""
Write-Host "Monitoring:"
Write-Host "  • Check Supabase: game_candidates grows by 30+ rows daily"
Write-Host "  • Check Event Viewer: Task Scheduler logs"
Write-Host "  • Check: G:\My Drive\Projects\_studio\logs\GameArchaeology_*"
Write-Host ""
