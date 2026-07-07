#!/bin/bash

# ==============================================================================
# Bilingual WhatsApp Real Estate Lead Generation — Linux/VPS Shutdown Script
# ==============================================================================

echo -e "\e[36m[INFO] Shutting down system services...\e[0m"

# ------------------------------------------------------------------------------
# TOUR BLOCK 1: Terminate ngrok Tunnel
# ------------------------------------------------------------------------------
echo -e "\e[36m[INFO] Closing secure ngrok tunnel...\e[0m"
# Kill the running background process named 'ngrok'
pkill ngrok || killall ngrok || true
echo -e "\e[32m[SUCCESS] Tunnel closed.\e[0m"

# ------------------------------------------------------------------------------
# TOUR BLOCK 2: Stop Docker Containers
# ------------------------------------------------------------------------------
echo -e "\e[36m[INFO] Stopping Docker containers...\e[0m"
docker compose down
echo -e "\e[32m[SUCCESS] Containers stopped and cleaned.\e[0m"

echo -e "\n\e[32m========================================================\e[0m"
echo -e "\e[32mALL SERVICES SHUT DOWN SUCCESSFULLY\e[0m"
echo -e "\e[32m========================================================\e[0m"
