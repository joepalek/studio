$xmlPath = 'G:\My Drive\Projects\_studio\scheduler\AgentNightlyRollup.xml'
schtasks /Delete /TN "AgentNightlyRollup" /F 2>$null
schtasks /Create /XML $xmlPath /TN "AgentNightlyRollup"
Write-Host "Task re-registered"
