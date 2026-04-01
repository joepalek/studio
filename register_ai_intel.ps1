$action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"G:\My Drive\Projects\_studio\scheduler\overnight-ai-intel.bat`""
Set-ScheduledTask -TaskName "\Studio\AIIntel" -Action $action
Write-Host "AIIntel task updated"
