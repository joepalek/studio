$tasks = @(
    @{Name="\Studio\CheckDrift";    Bat="G:\My Drive\Projects\_studio\scheduler\overnight-check-drift.bat"},
    @{Name="\Studio\InboxManager";  Bat="G:\My Drive\Projects\_studio\scheduler\overnight-inbox-manager.bat"},
    @{Name="\Studio\Janitor";       Bat="G:\My Drive\Projects\_studio\scheduler\overnight-janitor.bat"}
)
foreach ($t in $tasks) {
    $action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$($t.Bat)`""
    Set-ScheduledTask -TaskName $t.Name -Action $action -ErrorAction SilentlyContinue
    if ($?) { Write-Host "OK: $($t.Name)" } else { Write-Host "FAILED: $($t.Name)" }
}
