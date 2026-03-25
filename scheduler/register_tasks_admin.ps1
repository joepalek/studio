# Studio Task Scheduler Registration
# Run this once from an elevated PowerShell prompt (Run as Administrator)
# Right-click PowerShell -> Run as Administrator, then:
#   cd "G:\My Drive\Projects\_studio\scheduler"
#   .\register_tasks_admin.ps1

$SCHED = "G:\My Drive\Projects\_studio\scheduler"
$LOG   = "$SCHED\logs"
if (!(Test-Path $LOG)) { New-Item -ItemType Directory -Path $LOG | Out-Null }

# Ensure Studio folder exists in Task Scheduler
$folder = "\Studio"
$service = New-Object -ComObject Schedule.Service
$service.Connect()
try {
    $service.GetFolder($folder) | Out-Null
} catch {
    $root = $service.GetFolder("\")
    $root.CreateFolder("Studio") | Out-Null
    Write-Host "Created Task Scheduler folder: \Studio"
}

$tasks = @(
    @{ Name="DailyBriefing";              Bat="orchestrator-briefing.bat";        Trigger="Daily";  Time="08:00"; Days=$null },
    @{ Name="SupervisorCheck";            Bat="supervisor-check.bat";             Trigger="Minute"; Time=$null;   Days=$null; Interval=30 },
    @{ Name="NightlyCommit";              Bat="nightly-commit.bat";               Trigger="Daily";  Time="23:00"; Days=$null },
    @{ Name="GhostBookRescan";            Bat="ghost-book-rescan.bat";            Trigger="Weekly"; Time="02:00"; Days="Sunday" },
    @{ Name="OvernightVintageAgent";      Bat="overnight-vintage-agent.bat";      Trigger="Weekly"; Time="01:00"; Days="Monday" },
    @{ Name="OvernightGhostBookPass3";    Bat="overnight-ghost-book-pass3.bat";   Trigger="Weekly"; Time="01:30"; Days="Wednesday" },
    @{ Name="OvernightProductArchaeology";Bat="overnight-product-archaeology.bat";Trigger="Daily";  Time="02:00"; Days=$null },
    @{ Name="OvernightJobDelta";          Bat="overnight-job-delta.bat";          Trigger="Daily";  Time="03:00"; Days=$null },
    @{ Name="OvernightAutoAnswer";        Bat="overnight-auto-answer.bat";        Trigger="Daily";  Time="03:30"; Days=$null },
    @{ Name="OvernightWhiteboardScore";   Bat="overnight-whiteboard-score.bat";   Trigger="Daily";  Time="04:00"; Days=$null }
)

Write-Host "`n=== Registering Studio Tasks ===`n"

foreach ($t in $tasks) {
    $tn  = "Studio\$($t.Name)"
    $bat = "$SCHED\$($t.Bat)"

    # Build action
    $action = New-ScheduledTaskAction -Execute $bat

    # Build trigger
    if ($t.Trigger -eq "Daily") {
        $trigger = New-ScheduledTaskTrigger -Daily -At $t.Time
    } elseif ($t.Trigger -eq "Weekly") {
        $trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek $t.Days -At $t.Time
    } elseif ($t.Trigger -eq "Minute") {
        $trigger = New-ScheduledTaskTrigger -RepetitionInterval (New-TimeSpan -Minutes $t.Interval) -Once -At "00:00"
    }

    $settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Hours 4) `
        -StartWhenAvailable -WakeToRun

    try {
        Unregister-ScheduledTask -TaskName $tn -Confirm:$false -ErrorAction SilentlyContinue
        Register-ScheduledTask -TaskName $tn -Action $action -Trigger $trigger `
            -Settings $settings -RunLevel Highest -Force | Out-Null
        Write-Host "  [OK  ] $($t.Name)"
    } catch {
        Write-Host "  [FAIL] $($t.Name): $($_.Exception.Message)"
    }
}

Write-Host "`n=== Registered Tasks ==="
Get-ScheduledTask -TaskPath "\Studio\" | Select-Object TaskName, State | Format-Table -AutoSize
Write-Host "Done. View in: taskschd.msc -> Task Scheduler Library -> Studio"
