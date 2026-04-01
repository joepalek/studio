## Set all studio tasks to run as SYSTEM — no password needed
## Run in Admin PowerShell

$toFix = @(
    "AIIntel", "CheckDrift", "GitCommitNightly", "Janitor",
    "NightlyRollup", "ProductArchaeology", "VectorReindex",
    "MonthlyJobDiscovery", "SidebarBridge", "WhiteboardScorer",
    "PeerReview", "SkillImprover", "WhiteboardAgent"
)

foreach ($name in $toFix) {
    try {
        $task = Get-ScheduledTask -TaskPath "\Studio\" -TaskName $name -ErrorAction Stop
        Set-ScheduledTask -TaskPath "\Studio\" -TaskName $name -User "SYSTEM" | Out-Null
        Write-Host "OK: $name"
    } catch {
        Write-Host "FAIL: $name - $($_.Exception.Message.Split('.')[0])"
    }
}

## Disable the ones we want parked
$toDisable = @("GitScout", "HeartbeatCheck", "IntelFeed", "WorkflowIntelligence", "VedicScan", "MirofishTest")
foreach ($name in $toDisable) {
    try {
        Disable-ScheduledTask -TaskPath "\Studio\" -TaskName $name -ErrorAction Stop | Out-Null
        Write-Host "DISABLED: $name"
    } catch {
        Write-Host "SKIP: $name - not found"
    }
}

Write-Host ""
Write-Host "Done. Verifying..."
Get-ScheduledTask -TaskPath "\Studio\" | Select-Object TaskName, State | Format-Table -AutoSize
