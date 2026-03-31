$repos = @(
    "G:\My Drive\Projects\_studio",
    "G:\My Drive\Projects\CTW",
    "G:\My Drive\Projects\job-match",
    "G:\My Drive\Projects\listing-optimizer"
)
foreach ($repo in $repos) {
    Write-Host "--- $repo ---"
    Set-Location $repo
    git status --short 2>&1
}
