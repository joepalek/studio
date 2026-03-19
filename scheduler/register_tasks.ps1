$SchedDir = 'G:\My Drive\Projects\_studio\scheduler'
$results = @()

function Register-StudioTask {
    param($Name, $Bat, $Trigger)
    $bat = Join-Path $SchedDir $Bat
    try {
        Unregister-ScheduledTask -TaskName $Name -Confirm:$false -ErrorAction SilentlyContinue
        $action   = New-ScheduledTaskAction -Execute $bat
        $settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Hours 4) -StartWhenAvailable -MultipleInstances IgnoreNew
        Register-ScheduledTask -TaskName $Name -Action $action -Trigger $Trigger -Settings $settings -Force -ErrorAction Stop | Out-Null
        Write-Host "  [OK]  $Name"
        return $true
    } catch {
        Write-Host "  [FAIL] $Name — $($_.Exception.Message.Split([char]10)[0].Trim())"
        return $false
    }
}

Write-Host '=== Registering Studio Scheduled Tasks ==='
Write-Host ''

# Daily Briefing — 8:00 AM
Register-StudioTask -Name 'Studio\DailyBriefing' -Bat 'orchestrator-briefing.bat' `
    -Trigger (New-ScheduledTaskTrigger -Daily -At '08:00')

# Supervisor Check — Every 30 minutes (use MINUTE trigger, repeat daily)
$t30 = New-ScheduledTaskTrigger -RepetitionInterval (New-TimeSpan -Minutes 30) -Once -At (Get-Date -Hour 0 -Minute 0 -Second 0)
Register-StudioTask -Name 'Studio\SupervisorCheck' -Bat 'supervisor-check.bat' -Trigger $t30

# Nightly Commit — 11:00 PM
Register-StudioTask -Name 'Studio\NightlyCommit' -Bat 'nightly-commit.bat' `
    -Trigger (New-ScheduledTaskTrigger -Daily -At '23:00')

# Ghost Book Rescan — Sunday 2:00 AM
Register-StudioTask -Name 'Studio\GhostBookRescan' -Bat 'ghost-book-rescan.bat' `
    -Trigger (New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At '02:00')

Write-Host ''

# Verify
Write-Host '=== Registered Tasks ==='
Get-ScheduledTask -TaskPath '\Studio\' -ErrorAction SilentlyContinue | ForEach-Object {
    $info = $_ | Get-ScheduledTaskInfo -ErrorAction SilentlyContinue
    $next = if ($info) { $info.NextRunTime.ToString('yyyy-MM-dd HH:mm') } else { 'unknown' }
    Write-Host "  $($_.TaskName) | State: $($_.State) | Next: $next"
}

Write-Host ''
Write-Host 'To view: taskschd.msc -> Task Scheduler Library -> Studio'
Write-Host 'If tasks show as disabled, right-click -> Enable'
