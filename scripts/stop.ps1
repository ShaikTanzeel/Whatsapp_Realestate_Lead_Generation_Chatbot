# ==============================================================================
# Bilingual WhatsApp Real Estate Lead Generation — Shutdown Automation Script
# ==============================================================================

$ErrorActionPreference = "Continue"

Write-Host "[INFO] Shutting down system services..." -ForegroundColor Cyan

# ------------------------------------------------------------------------------
# TOUR BLOCK 1: Terminate ngrok Tunnel
# ------------------------------------------------------------------------------
Write-Host "[INFO] Closing secure ngrok tunnel..." -ForegroundColor Cyan
# Stop the running background process named 'ngrok'
Stop-Process -Name "ngrok" -ErrorAction SilentlyContinue
Write-Host "[SUCCESS] Tunnel closed." -ForegroundColor Green

# ------------------------------------------------------------------------------
# TOUR BLOCK 2: Stop Docker Containers
# ------------------------------------------------------------------------------
Write-Host "[INFO] Stopping Docker containers..." -ForegroundColor Cyan
# 'docker compose down' stops and removes the postgres and n8n containers,
# but preserves the volumes (our data is safe!)
docker compose down
Write-Host "[SUCCESS] Containers stopped and cleaned." -ForegroundColor Green

Write-Host "`n========================================================" -ForegroundColor Green
Write-Host "ALL SERVICES SHUT DOWN SUCCESSFULLY" -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Green
