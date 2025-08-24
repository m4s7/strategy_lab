#!/bin/bash

# Complete deployment script for Strategy Lab
# This script installs and configures everything needed for production

set -e

echo "========================================"
echo "  Strategy Lab Production Deployment"
echo "========================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[1;34m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run with sudo: sudo bash deploy.sh${NC}"
    exit 1
fi

# Get the actual user (not root)
ACTUAL_USER="${SUDO_USER:-$(logname)}"
echo -e "${BLUE}Deploying as user: $ACTUAL_USER${NC}"
echo ""

# Step 1: Install TimescaleDB
echo -e "${YELLOW}Step 1/8: Installing PostgreSQL with TimescaleDB...${NC}"
bash scripts/install_timescaledb.sh
echo -e "${GREEN}✓ TimescaleDB installed${NC}"
echo ""

# Step 2: Setup Database
echo -e "${YELLOW}Step 2/8: Setting up database...${NC}"
bash scripts/setup_database.sh
echo -e "${GREEN}✓ Database setup complete${NC}"
echo ""

# Step 3: Run Migrations
echo -e "${YELLOW}Step 3/8: Running database migrations...${NC}"
sudo -u $ACTUAL_USER bash scripts/run_migrations.sh
echo -e "${GREEN}✓ Migrations complete${NC}"
echo ""

# Step 4: Build Applications
echo -e "${YELLOW}Step 4/8: Building applications for production...${NC}"
sudo -u $ACTUAL_USER bash scripts/build_production.sh
echo -e "${GREEN}✓ Applications built${NC}"
echo ""

# Step 5: Setup SystemD Services
echo -e "${YELLOW}Step 5/8: Setting up systemd services...${NC}"
bash scripts/setup_services.sh
echo -e "${GREEN}✓ Services configured${NC}"
echo ""

# Step 6: Setup Nginx
echo -e "${YELLOW}Step 6/8: Setting up Nginx reverse proxy...${NC}"
bash scripts/setup_nginx.sh
echo -e "${GREEN}✓ Nginx configured${NC}"
echo ""

# Step 7: Configure Firewall
echo -e "${YELLOW}Step 7/8: Configuring firewall...${NC}"
if command -v ufw &> /dev/null; then
    # Allow SSH
    ufw allow ssh
    # Allow HTTP
    ufw allow 80
    # Allow HTTPS (for future SSL)
    ufw allow 443
    # Enable firewall
    echo "y" | ufw enable
    echo -e "${GREEN}✓ UFW firewall configured${NC}"
else
    echo -e "${YELLOW}UFW not installed, skipping firewall configuration${NC}"
fi
echo ""

# Step 8: Final checks and status
echo -e "${YELLOW}Step 8/8: Running final health checks...${NC}"
sleep 5 # Give services time to fully start

# Check if services are running
if systemctl is-active --quiet strategylab-backend; then
    echo -e "${GREEN}✓ Backend service is running${NC}"
else
    echo -e "${RED}✗ Backend service is not running${NC}"
    systemctl status strategylab-backend --no-pager
fi

if systemctl is-active --quiet strategylab-frontend; then
    echo -e "${GREEN}✓ Frontend service is running${NC}"
else
    echo -e "${RED}✗ Frontend service is not running${NC}"
    systemctl status strategylab-frontend --no-pager
fi

if systemctl is-active --quiet nginx; then
    echo -e "${GREEN}✓ Nginx is running${NC}"
else
    echo -e "${RED}✗ Nginx is not running${NC}"
    systemctl status nginx --no-pager
fi

# Test API health
echo ""
echo "Testing API health..."
if curl -s http://localhost/health > /dev/null; then
    echo -e "${GREEN}✓ API health check passed${NC}"
else
    echo -e "${RED}✗ API health check failed${NC}"
fi

echo ""
echo "========================================"
echo -e "${GREEN}  DEPLOYMENT COMPLETE!${NC}"
echo "========================================"
echo ""
echo -e "${BLUE}Strategy Lab is now running at:${NC}"
echo "  http://$(hostname -I | awk '{print $1}')"
echo "  http://localhost"
echo ""
echo -e "${BLUE}Services Status:${NC}"
echo "  Backend:  http://localhost:8001 (direct)"
echo "  Frontend: http://localhost:3000 (direct)"
echo "  Nginx:    http://localhost (proxy)"
echo ""
echo -e "${BLUE}Useful Commands:${NC}"
echo "  View logs:         sudo journalctl -u strategylab-backend -f"
echo "  Restart services:  sudo systemctl restart strategylab-backend strategylab-frontend"
echo "  Check status:      sudo systemctl status strategylab-backend strategylab-frontend nginx"
echo ""
echo -e "${BLUE}Log Files:${NC}"
echo "  Backend:  /var/log/strategylab/backend.log"
echo "  Frontend: /var/log/strategylab/frontend.log"
echo "  Nginx:    /var/log/nginx/strategylab_access.log"
echo ""
echo -e "${GREEN}Deployment successful! 🚀${NC}"
echo ""