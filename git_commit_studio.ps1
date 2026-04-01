Set-Location "G:\My Drive\Projects\_studio"

# Disable Vedic tasks (closed/deferred module)
foreach ($task in @("VedicScan", "VedicSync")) {
    $t = Get-ScheduledTask -TaskName $task -ErrorAction SilentlyContinue
    if ($t) {
        Disable-ScheduledTask -TaskName $task | Out-Null
        Write-Host "Disabled: $task"
    } else {
        Write-Host "Not found: $task"
    }
}

# Verify sidebar_http archived
if (Test-Path "_archive\sidebar_http.py.old") { Write-Host "sidebar_http.py confirmed archived" }

# Git commit all changes
git add STUDIO_AUDIT.md check_sidebar.py
git add -A _archive/
git rm --cached sidebar_http.py 2>$null
git commit -m "audit v3: all tasks verified, sidebar_http retired to _archive, Vedic tasks disabled, ghost book/notification items queued"
git push origin master
Write-Host "done"
