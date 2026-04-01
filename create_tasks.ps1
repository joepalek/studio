$needed = @(
    @{Name="InboxManager";          Bat="overnight-inbox-manager.bat";    Time="02:30"; Desc="Daily inbox sync"},
    @{Name="AIIntelDaily";          Bat="overnight-ai-intel.bat";         Time="05:00"; Desc="AI Intel scraper"},
    @{Name="OrchestratorBriefing";  Bat="orchestrator-briefing.bat";      Time="08:00"; Desc="Daily orchestrator briefing"},
    @{Name="SidebarInjectDaily";    Bat="overnight-sidebar-inject.bat";   Time="06:00"; Desc="Sidebar data inject"},
    @{Name="AIServicesRankingsDaily";Bat="overnight-ai-services-rankings.bat"; Time="05:30"; Desc="AI services rankings"}
)

foreach ($t in $needed) {
    $batPath = "G:\My Drive\Projects\_studio\scheduler\$($t.Bat)"
    $action  = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$batPath`""
    $trigger = New-ScheduledTaskTrigger -Daily -At $t.Time
    $settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Hours 2) -StartWhenAvailable
    
    # Check if exists first
    $existing = Get-ScheduledTask -TaskName $t.Name -TaskPath "\Studio\" -ErrorAction SilentlyContinue
    if ($existing) {
        Set-ScheduledTask -TaskName "\Studio\$($t.Name)" -Action $action
        Write-Host "UPDATED: \Studio\$($t.Name)"
    } else {
        Register-ScheduledTask -TaskName $t.Name -TaskPath "\Studio\" `
            -Action $action -Trigger $trigger -Settings $settings `
            -RunLevel Highest -Description $t.Desc -Force | Out-Null
        Write-Host "CREATED: \Studio\$($t.Name)"
    }
}
