New-NetFirewallRule -DisplayName "Studio Sidebar 8765" -Direction Inbound -Protocol TCP -LocalPort 8765 -Action Allow -Profile Private
Write-Host "Rule created."
