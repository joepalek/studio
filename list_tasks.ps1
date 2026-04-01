$tasks = Get-ScheduledTask | Where-Object { $_.TaskPath -like "*Studio*" }
$tasks | Select-Object TaskPath, TaskName, State | Format-Table -AutoSize
