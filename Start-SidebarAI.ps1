# Start-SidebarAI.ps1
# Startup script for Sidebar AI Server
# Location: G:/My Drive/Projects/_studio/Start-SidebarAI.ps1
#
# API keys are loaded from .studio-vault.json automatically.
# Only set env vars here for overrides.

# Studio path
$env:STUDIO_PATH = "G:/My Drive/Projects/_studio"

# Garage Ollama - set when GPU arrives
# 1. Find garage IP: on garage machine run `ipconfig | Select-String "IPv4"`
# 2. Configure Ollama to accept network: on garage run `$env:OLLAMA_HOST="0.0.0.0:11434"; ollama serve`
# 3. Uncomment and set the URL below:
# $env:GARAGE_OLLAMA_URL = "http://192.168.1.X:11434"

# HOME for any tools that need it
$env:HOME = $env:USERPROFILE

# Change to studio directory
Set-Location $env:STUDIO_PATH

# Start server
Write-Host ""
Write-Host "Starting Sidebar AI Server..." -ForegroundColor Cyan
Write-Host "  Keys loaded from: .studio-vault.json" -ForegroundColor Gray
Write-Host ""

python panel/sidebar_ai_server.py
