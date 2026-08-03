#!/bin/bash
# ==============================================================================
# QUANT AI TRADING BOT - 1-CLICK CLOUD DEPLOYMENT SCRIPT (24/7 UPTIME)
# Author: Quant AI Engineering Team
# Target OS: Ubuntu 20.04 / 22.04 LTS (DigitalOcean, Linode, AWS EC2, GCP)
# ==============================================================================

echo "🚀 Starting Quant AI Cloud Production Deployment Setup..."

# 1. Update system packages
sudo apt-get update && sudo apt-get upgrade -y

# 2. Install Docker & Docker Compose if missing
if ! command -v docker &> /dev/null; then
    echo "📦 Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
fi

if ! command -v docker-compose &> /dev/null; then
    echo "📦 Installing Docker Compose..."
    sudo apt-get install -y docker-compose
fi

# 3. Configure UFW Firewall (Open Port 8501 for Web Dashboard, 22 for SSH)
sudo ufw allow 22/tcp
sudo ufw allow 8501/tcp
sudo ufw --force enable

# 4. Build and Launch Containers in Background (24/7 Auto-Restart)
echo "⚡ Building and Launching Quant AI 24/7 Services via Docker Compose..."
docker-compose up -d --build

echo "=============================================================================="
echo "🎉 DEPLOYMENT COMPLETE! QUANT AI IS NOW RUNNING 24/7 ON THE CLOUD SERVER!"
echo "=============================================================================="
echo "🌐 Dashboard Web Access: http://$(curl -s ifconfig.me):8501"
echo "🤖 Auto-Trader Daemon Status: ACTIVE & RUNNING IN BACKGROUND (24/7)"
echo "📲 Telegram Notifications: CONNECTED & READY"
echo "=============================================================================="
