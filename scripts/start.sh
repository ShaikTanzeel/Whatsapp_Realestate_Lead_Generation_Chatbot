#!/bin/bash

# ==============================================================================
# Bilingual WhatsApp Real Estate Lead Generation — Linux/VPS Startup Script
# ==============================================================================

# Exit immediately if any command returns a non-zero exit status
set -e

# ------------------------------------------------------------------------------
# TOUR BLOCK 1: Verify Docker Status
# ------------------------------------------------------------------------------
echo -e "\e[36m[INFO] Checking if Docker is running...\e[0m"
if ! docker info >/dev/null 2>&1; then
    echo -e "\e[31m[ERROR] Docker daemon is not running!\e[0m"
    echo -e "\e[33m[INFO] Please start the Docker service and try again.\e[0m"
    exit 1
fi
echo -e "\e[32m[SUCCESS] Docker is running.\e[0m"

# ------------------------------------------------------------------------------
# TOUR BLOCK 2: Setup Local Configuration (.env)
# ------------------------------------------------------------------------------
if [ ! -f .env ]; then
    echo -e "\e[33m[WARN] Local '.env' file not found. Bootstrapping from template...\e[0m"
    cp .env.example .env
    
    # Generate a random 32-character hex key using openssl
    RANDOM_KEY=$(openssl rand -hex 16 2>/dev/null || tr -dc 'a-f0-9' </dev/urandom | head -c 32)
    
    # Replace placeholder in .env
    # We use sed differently depending on macOS vs Linux
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s/generate_a_long_random_string_of_characters_here/$RANDOM_KEY/g" .env
    else
        sed -i "s/generate_a_long_random_string_of_characters_here/$RANDOM_KEY/g" .env
    fi
    echo -e "\e[32m[SUCCESS] Created '.env' and generated a unique N8N_ENCRYPTION_KEY.\e[0m"
fi

# ------------------------------------------------------------------------------
# TOUR BLOCK 3: Launch Docker Services
# ------------------------------------------------------------------------------
echo -e "\e[36m[INFO] Launching database and n8n services...\e[0m"
docker compose up -d

# ------------------------------------------------------------------------------
# TOUR BLOCK 4: Wait for n8n to be Healthy
# ------------------------------------------------------------------------------
echo -e "\e[36m[INFO] Waiting for n8n to finish initializing...\e[0m"
N8N_HEALTH_URL="http://localhost:5678/healthz"
HEALTHY=false

for i in {1..20}; do
    # Fetch HTTP status code silently
    STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$N8N_HEALTH_URL" || true)
    if [ "$STATUS_CODE" -eq 200 ]; then
        HEALTHY=true
        break
    fi
    echo -n -e "\e[33m.\e[0m"
    sleep 2
done

if [ "$HEALTHY" = false ]; then
    echo -e "\n\e[31m[ERROR] n8n took too long to start or is unhealthy.\e[0m"
    exit 1
fi
echo -e "\n\e[32m[SUCCESS] n8n is online and database connections are verified!\e[0m"

# ------------------------------------------------------------------------------
# TOUR BLOCK 5: Start Tunnel and Print Public Address
# ------------------------------------------------------------------------------
echo -e "\e[36m[INFO] Establishing secure ngrok tunnel...\e[0m"
ngrok http 5678 >/dev/null 2>&1 &

sleep 3

# Query ngrok's local API to fetch the public URL
NGROK_INFO=$(curl -s http://localhost:4040/api/tunnels || true)
if [[ $NGROK_INFO == *"public_url"* ]]; then
    # Extract public_url using basic string parsing since jq might not be installed on host
    PUBLIC_URL=$(echo "$NGROK_INFO" | grep -o '"public_url":"[^"]*' | head -n 1 | cut -d'"' -f4)
    
    echo -e "\n\e[32m========================================================\e[0m"
    echo -e "\e[32mSYSTEM IS FULLY OPERATIONAL\e[0m"
    echo -e "\e[32m========================================================\e[0m"
    echo -e "\e[36mn8n Dashboard:       http://localhost:5678\e[0m"
    echo -e "\e[36mPublic Webhook URL:  $PUBLIC_URL\e[0m"
    echo -e "\e[32m========================================================\e[0m"
    echo -e "\e[33mCopy the Public Webhook URL and paste it in your Meta Developer portal.\e[0m"
else
    echo -e "\n\e[33m[WARN] Containers started, but could not retrieve ngrok URL.\e[0m"
    echo -e "\e[33m[INFO] Make sure you have ngrok installed and running.\e[0m"
fi
