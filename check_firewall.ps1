$rules = Get-NetFirewallRule | Where-Object { $_.DisplayName -like "*8765*" }
$rules | Select-Object DisplayName, Enabled, Profile, Action | Format-Table -AutoSize
