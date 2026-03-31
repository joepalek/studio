$env:PYTHONIOENCODING = "utf-8"
Set-Location "G:\My Drive\Projects\listing-optimizer"
Write-Host "Paste the code value and press Enter:"
$code = Read-Host
python ebay_oauth.py $code
