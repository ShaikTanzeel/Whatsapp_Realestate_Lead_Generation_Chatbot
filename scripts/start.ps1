# ==============================================================================
# Bilingual WhatsApp Real Estate Lead Generation — Startup Automation Script
# ==============================================================================

# Ensure the terminal stops running the script if any command encounters a major error
$ErrorActionPreference = "Stop"

# ------------------------------------------------------------------------------
# TOUR BLOCK 1: Verify Docker Status
# ------------------------------------------------------------------------------
Write-Host "[INFO] Checking if Docker Desktop is running..." -ForegroundColor Cyan
try {
    # Run a quick, silent docker query. If Docker is closed, this will throw an exception.
    $null = docker info
} catch {
    Write-Host "[ERROR] Docker is not running!" -ForegroundColor Red
    Write-Host "[INFO] Please launch Docker Desktop and try running this script again." -ForegroundColor Yellow
    Exit 1
}
Write-Host "[SUCCESS] Docker is running." -ForegroundColor Green

# ------------------------------------------------------------------------------
# TOUR BLOCK 2: Setup Local Configuration (.env)
# ------------------------------------------------------------------------------
if (-not (Test-Path ".env")) {
    Write-Host "[WARN] Local '.env' file not found. Bootstrapping it from template..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    
    # Generate a random 32-character hexadecimal key to secure n8n credentials
    $guid = [Guid]::NewGuid().ToString().Replace("-", "")
    
    # Read the new .env file, replace the placeholder key with our generated key, and save it
    (Get-Content ".env") -replace "generate_a_long_random_string_of_characters_here", $guid | Set-Content ".env"
    Write-Host "[SUCCESS] Created '.env' and generated a unique N8N_ENCRYPTION_KEY." -ForegroundColor Green
}

# ------------------------------------------------------------------------------
# TOUR BLOCK 3: Launch Docker Services
# ------------------------------------------------------------------------------
Write-Host "[INFO] Launching database and n8n services..." -ForegroundColor Cyan
# Starts the containers in the background ('-d' for detached)
docker compose up -d

# ------------------------------------------------------------------------------
# TOUR BLOCK 4: Wait for n8n to be Healthy
# ------------------------------------------------------------------------------
Write-Host "[INFO] Waiting for n8n to finish initializing..." -ForegroundColor Cyan
$n8nHealthUrl = "http://localhost:5678/healthz"
$healthy = $false
$maxRetries = 20

for ($i = 1; $i -le $maxRetries; $i++) {
    try {
        # Query n8n's health check page. -UseBasicParsing speeds up request execution
        $response = Invoke-WebRequest -Uri $n8nHealthUrl -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            $healthy = $true
            break
        }
    } catch {
        # n8n is still starting up, ignore error and wait
    }
    
    # Print a dot to show progress and sleep for 2 seconds
    Write-Host "." -NoNewline -ForegroundColor Yellow
    Start-Sleep -Seconds 2
}

if (-not $healthy) {
    Write-Host "`n[ERROR] n8n took too long to start or is unhealthy." -ForegroundColor Red
    Exit 1
}

Write-Host "`n[SUCCESS] n8n is online and database connections are verified!" -ForegroundColor Green

# ------------------------------------------------------------------------------
# TOUR BLOCK 5: Start Tunnel and Print Public Address
# ------------------------------------------------------------------------------
Write-Host "[INFO] Establishing secure ngrok tunnel..." -ForegroundColor Cyan

# Start ngrok pointing to port 5678. Start-Process runs it in a separate background job
# so it doesn't block this PowerShell window.
Start-Process -FilePath "ngrok" -ArgumentList "http 5678" -NoNewWindow

# Wait 3 seconds to let ngrok connect to its cloud servers and setup the tunnel
Start-Sleep -Seconds 3

try {
    # Query ngrok's local API (running on port 4040) to retrieve our public URL
    $ngrokInfo = Invoke-RestMethod -Uri "http://localhost:4040/api/tunnels"
    $publicUrl = $ngrokInfo.tunnels[0].public_url
    
    Write-Host "`n========================================================" -ForegroundColor Green
    Write-Host "SYSTEM IS FULLY OPERATIONAL" -ForegroundColor Green
    Write-Host "========================================================" -ForegroundColor Green
    Write-Host "n8n Dashboard:       http://localhost:5678" -ForegroundColor Cyan
    Write-Host "Public Webhook URL:  $publicUrl" -ForegroundColor Cyan
    Write-Host "========================================================" -ForegroundColor Green
    Write-Host "Copy the Public Webhook URL and paste it in your Meta Developer portal." -ForegroundColor Yellow
} catch {
    Write-Host "`n[WARN] Containers started, but could not retrieve ngrok URL." -ForegroundColor Yellow
    Write-Host "[INFO] Make sure you have ngrok installed on your machine and on your system's PATH." -ForegroundColor Yellow
}
