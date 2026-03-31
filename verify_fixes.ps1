Set-Location "G:\My Drive\Projects\_studio"
python -m py_compile nightly_rollup.py 2>&1
if ($LASTEXITCODE -eq 0) { Write-Host "SYNTAX OK" } else { Write-Host "SYNTAX ERROR" }
python -m py_compile auto_answer_gemini.py 2>&1
if ($LASTEXITCODE -eq 0) { Write-Host "auto_answer_gemini OK" } else { Write-Host "auto_answer_gemini ERROR" }
python -m py_compile session-startup.py 2>&1
if ($LASTEXITCODE -eq 0) { Write-Host "session-startup OK" } else { Write-Host "session-startup ERROR" }
Set-Location "G:\My Drive\Projects\_studio\agency"
python -m py_compile character_batch_builder.py 2>&1
if ($LASTEXITCODE -eq 0) { Write-Host "character_batch_builder OK" } else { Write-Host "character_batch_builder ERROR" }
Set-Location "G:\My Drive\Projects\job-match"
python -m py_compile job_daily_harvest.py 2>&1
if ($LASTEXITCODE -eq 0) { Write-Host "job_daily_harvest OK" } else { Write-Host "job_daily_harvest ERROR" }
