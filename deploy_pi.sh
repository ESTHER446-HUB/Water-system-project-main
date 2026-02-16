#!/bin/bash

echo "🌱 Smart Irrigation System - Raspberry Pi Deployment"
echo "=================================================="

# Update system
echo "📦 Updating system..."
sudo apt update

# Install dependencies
echo "📦 Installing system dependencies..."
sudo apt install -y python3-pip python3-venv

# Install pipenv if not present
pip3 install --user pipenv

# Install Python packages
echo "📦 Installing Python packages..."
pipenv install Flask flask-cors requests gunicorn

# Create systemd service
echo "⚙️ Setting up systemd service..."
sudo cp irrigation.service /etc/systemd/system/
sudo sed -i "s|/home/pi/Water-system-project-main|$(pwd)|g" /etc/systemd/system/irrigation.service
sudo sed -i "s|User=pi|User=$(whoami)|g" /etc/systemd/system/irrigation.service

# Reload systemd
sudo systemctl daemon-reload

# Enable and start service
sudo systemctl enable irrigation.service
sudo systemctl start irrigation.service

# Check status
echo ""
echo "✅ Deployment complete!"
echo ""
echo "Service status:"
sudo systemctl status irrigation.service --no-pager

echo ""
echo "🌐 Access your system at:"
echo "   http://$(hostname -I | awk '{print $1}'):5000"
echo ""
echo "📝 Useful commands:"
echo "   sudo systemctl status irrigation    # Check status"
echo "   sudo systemctl restart irrigation   # Restart service"
echo "   sudo systemctl stop irrigation      # Stop service"
echo "   sudo journalctl -u irrigation -f    # View logs"
