# Studio Agent Tasks — register all 13 agent tasks
# Run from PowerShell: powershell -ExecutionPolicy Bypass -File register-agents.ps1

$base = "G:\My Drive\Projects\_studio\scheduler"

$tasks = @(
    @{ name = "Studio\SupervisorBriefing";   xml = "AgentSupervisorBriefing.xml" },
    @{ name = "Studio\WorkflowIntelligence"; xml = "AgentWorkflowIntelligence.xml" },
    @{ name = "Studio\GitCommitNightly";     xml = "AgentGitCommitNightly.xml" },
    @{ name = "Studio\HeartbeatCheck";       xml = "AgentHeartbeatCheck.xml" },
    @{ name = "Studio\ProductArchaeology";   xml = "AgentProductArchaeology.xml" },
    @{ name = "Studio\Janitor";              xml = "AgentJanitor.xml" },
    @{ name = "Studio\GitScout";             xml = "AgentGitScout.xml" },
    @{ name = "Studio\IntelFeed";            xml = "AgentIntelFeed.xml" },
    @{ name = "Studio\SkillImprover";        xml = "AgentSkillImprover.xml" },
    @{ name = "Studio\WhiteboardAgent";      xml = "AgentWhiteboardAgent.xml" },
    @{ name = "Studio\WhiteboardScorer";     xml = "AgentWhiteboardScorer.xml" },
    @{ name = "Studio\PeerReview";           xml = "AgentPeerReview.xml" },
    @{ name = "Studio\CommonCrawlTrigger";   xml = "AgentCommonCrawlTrigger.xml" }
)

Write-Host "`n=== Registering Studio Agent Tasks ===`n"

foreach ($t in $tasks) {
    $xmlPath = Join-Path $base $t.xml
    $result = schtasks /create /xml $xmlPath /tn $t.name /f 2>&1
    if ($LASTEXITCODE -eq 0 -or ($result -join "") -match "SUCCESS") {
        Write-Host "  [OK  ] $($t.name)"
    } else {
        Write-Host "  [FAIL] $($t.name): $($result -join ' ')"
    }
}

Write-Host "`n=== Agent Tasks Registered ===`n"
schtasks /query /fo TABLE /nh 2>&1 | Select-String "Studio"
