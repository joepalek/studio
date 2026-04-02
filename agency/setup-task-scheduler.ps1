# AGENCY PIPELINE — TASK SCHEDULER SETUP
# Run this script as Administrator to create 3 daily tasks

# Configuration
$studioPath = "G:\My Drive\Projects\_studio\agency"
$pythonPath = "python"  # or full path: "C:\Users\YourUser\AppData\Local\Programs\Python\Python313\python.exe"
$taskUser = $env:USERNAME

Write-Host ""
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "AGENCY PIPELINE — TASK SCHEDULER SETUP"
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This script will create 3 daily tasks:"
Write-Host "  1. CX Agent (2:00 AM) — Process character specs"
Write-Host "  2. Image Gen (4:00 AM) — Generate 50 images per character"
Write-Host "  3. Social Media (6:00 AM) — Training wheels mode (awaits approval)"
Write-Host ""

# Check if running as admin
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")

if (-not $isAdmin) {
    Write-Host "ERROR: This script must run as Administrator" -ForegroundColor Red
    Write-Host "Right-click PowerShell → Run as Administrator"
    exit 1
}

# Verify paths exist
if (!(Test-Path $studioPath)) {
    Write-Host "ERROR: Studio path not found: $studioPath" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Studio path found: $studioPath" -ForegroundColor Green
Write-Host ""

# ============================================================================
# TASK 1: CX AGENT — 2:00 AM
# ============================================================================

Write-Host "Creating Task 1: CX Agent (2:00 AM)..." -ForegroundColor Yellow

$taskName1 = "Agency-CX-Agent-2AM"
$scriptPath1 = "$studioPath\cx-agent-main.py"

$action1 = New-ScheduledTaskAction `
    -Execute $pythonPath `
    -Argument "`"$scriptPath1`"" `
    -WorkingDirectory $studioPath

$trigger1 = New-ScheduledTaskTrigger `
    -Daily `
    -At 2:00AM

$settings1 = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable

# Remove existing task if it exists
if (Get-ScheduledTask -TaskName $taskName1 -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $taskName1 -Confirm:$false
    Write-Host "  (Replaced existing task)"
}

# Create new task
Register-ScheduledTask `
    -TaskName $taskName1 `
    -Action $action1 `
    -Trigger $trigger1 `
    -Settings $settings1 `
    -RunLevel Highest `
    -User $taskUser | Out-Null

Write-Host "✓ Task created: $taskName1" -ForegroundColor Green
Write-Host "  Schedule: Daily at 2:00 AM"
Write-Host "  Script: cx-agent-main.py"
Write-Host ""

# ============================================================================
# TASK 2: IMAGE GENERATION — 4:00 AM
# ============================================================================

Write-Host "Creating Task 2: Image Generation (4:00 AM)..." -ForegroundColor Yellow

$taskName2 = "Agency-ImageGen-4AM"
$scriptPath2 = "$studioPath\image-generation-agent.py"

$action2 = New-ScheduledTaskAction `
    -Execute $pythonPath `
    -Argument "`"$scriptPath2`"" `
    -WorkingDirectory $studioPath

$trigger2 = New-ScheduledTaskTrigger `
    -Daily `
    -At 4:00AM

$settings2 = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable

# Remove existing task if it exists
if (Get-ScheduledTask -TaskName $taskName2 -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $taskName2 -Confirm:$false
    Write-Host "  (Replaced existing task)"
}

# Create new task
Register-ScheduledTask `
    -TaskName $taskName2 `
    -Action $action2 `
    -Trigger $trigger2 `
    -Settings $settings2 `
    -RunLevel Highest `
    -User $taskUser | Out-Null

Write-Host "✓ Task created: $taskName2" -ForegroundColor Green
Write-Host "  Schedule: Daily at 4:00 AM"
Write-Host "  Script: image-generation-agent.py"
Write-Host ""

# ============================================================================
# TASK 3: SOCIAL MEDIA (TRAINING WHEELS) — 6:00 AM
# ============================================================================

Write-Host "Creating Task 3: Social Media Agent (6:00 AM - Training Wheels)..." -ForegroundColor Yellow

$taskName3 = "Agency-SocialMedia-6AM-TrainingWheels"
$scriptPath3 = "$studioPath\social-media-agent.py"

$action3 = New-ScheduledTaskAction `
    -Execute $pythonPath `
    -Argument "`"$scriptPath3`"" `
    -WorkingDirectory $studioPath

$trigger3 = New-ScheduledTaskTrigger `
    -Daily `
    -At 6:00AM

$settings3 = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -ExecutionTimeLimit ([timespan]::FromHours(2))  # 2 hour timeout for user input

# Remove existing task if it exists
if (Get-ScheduledTask -TaskName $taskName3 -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $taskName3 -Confirm:$false
    Write-Host "  (Replaced existing task)"
}

# Create new task
Register-ScheduledTask `
    -TaskName $taskName3 `
    -Action $action3 `
    -Trigger $trigger3 `
    -Settings $settings3 `
    -RunLevel Highest `
    -User $taskUser | Out-Null

Write-Host "✓ Task created: $taskName3" -ForegroundColor Green
Write-Host "  Schedule: Daily at 6:00 AM"
Write-Host "  Script: social-media-agent.py (TRAINING WHEELS MODE)"
Write-Host "  ⚠️  This task requires your approval input!"
Write-Host "  ⚠️  Set to run for up to 2 hours to allow for your review"
Write-Host ""

# ============================================================================
# SUMMARY
# ============================================================================

Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "TASK SCHEDULER SETUP COMPLETE"
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "✓ 3 tasks created successfully" -ForegroundColor Green
Write-Host ""
Write-Host "Daily schedule:"
Write-Host "  2:00 AM — CX Agent (spec validation + character creation)"
Write-Host "  4:00 AM — Image Generation (50 images per character)"
Write-Host "  6:00 AM — Social Media (training wheels - awaits your approval)"
Write-Host ""
Write-Host "To view tasks:"
Write-Host "  Open Task Scheduler → Task Scheduler Library → Agency-*"
Write-Host ""
Write-Host "To manually run a task:"
Write-Host "  cd '$studioPath'"
Write-Host "  python cx-agent-main.py"
Write-Host "  python image-generation-agent.py"
Write-Host "  python social-media-agent.py"
Write-Host ""
Write-Host "⚠️  IMPORTANT — Training Wheels Task (6:00 AM):"
Write-Host "  This task will wait for your input when it runs."
Write-Host "  You must approve/reject posts before they go live."
Write-Host "  First 24 posts per character require approval."
Write-Host "  After 24 approved → auto-post mode enabled."
Write-Host ""
Write-Host "========================================================================" -ForegroundColor Cyan
