# Studio Task Scheduler — register all 10 tasks
# Run from any PowerShell (no admin needed — LeastPrivilege)

$base = "G:\My Drive\Projects\_studio\scheduler"

$tasks = @(
    @{ name = "Studio\DailyBriefing";               xml = "DailyBriefing.xml" },
    @{ name = "Studio\SupervisorCheck";              xml = "SupervisorCheck.xml" },
    @{ name = "Studio\NightlyCommit";                xml = "NightlyCommit.xml" },
    @{ name = "Studio\GhostBookRescan";              xml = "GhostBookRescan.xml" },
    @{ name = "Studio\OvernightVintageAgent";        xml = "OvernightVintageAgent.xml" },
    @{ name = "Studio\OvernightGhostBookPass3";      xml = "OvernightGhostBookPass3.xml" },
    @{ name = "Studio\OvernightProductArchaeology";  xml = "OvernightProductArchaeology.xml" },
    @{ name = "Studio\OvernightJobDelta";            xml = "OvernightJobDelta.xml" },
    @{ name = "Studio\OvernightAutoAnswer";          xml = "OvernightAutoAnswer.xml" },
    @{ name = "Studio\OvernightWhiteboardScore";     xml = "OvernightWhiteboardScore.xml" }
)

# Clean up any stale/malformed task from previous attempts
schtasks /delete /tn "Studio\`${xml}" /f 2>$null
schtasks /delete /tn "Studio${xml}"   /f 2>$null

Write-Host "`n=== Registering Studio Tasks ===`n"

foreach ($t in $tasks) {
    $xmlPath = Join-Path $base $t.xml
    $result = schtasks /create /xml $xmlPath /tn $t.name /f 2>&1
    if ($result -match "SUCCESS") {
        Write-Host "  [OK  ] $($t.name)"
    } else {
        Write-Host "  [FAIL] $($t.name): $result"
    }
}

Write-Host "`n=== Registered Studio Tasks ===`n"
schtasks /query /fo TABLE /nh 2>&1 | Select-String "Studio"
