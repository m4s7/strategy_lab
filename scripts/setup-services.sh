#!/bin/bash
# Setup script for Strategy Lab services

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Strategy Lab Service Setup${NC}"
echo "================================"

# Check if running as root for systemd operations
if [[ $EUID -ne 0 ]]; then
   echo -e "${YELLOW}This script needs to be run with sudo for systemd setup${NC}"
   exit 1
fi

# Create log directory
echo -e "${GREEN}Creating log directory...${NC}"
mkdir -p /var/log/strategylab
chown dev:dev /var/log/strategylab

# Create nginx cache directory
echo -e "${GREEN}Creating nginx cache directory...${NC}"
mkdir -p /var/cache/nginx/strategylab
chown www-data:www-data /var/cache/nginx/strategylab

# Copy systemd service files
echo -e "${GREEN}Installing systemd service files...${NC}"
cp /home/dev/strategy_lab/scripts/systemd/strategylab-backend.service /etc/systemd/system/
cp /home/dev/strategy_lab/scripts/systemd/strategylab-frontend.service /etc/systemd/system/

# Reload systemd
echo -e "${GREEN}Reloading systemd daemon...${NC}"
systemctl daemon-reload

# Enable services
echo -e "${GREEN}Enabling services...${NC}"
systemctl enable strategylab-backend.service
systemctl enable strategylab-frontend.service

# Setup nginx
echo -e "${GREEN}Setting up nginx configuration...${NC}"
if [ -f /etc/nginx/sites-enabled/default ]; then
    echo -e "${YELLOW}Disabling default nginx site...${NC}"
    rm -f /etc/nginx/sites-enabled/default
fi

# Create symlink for nginx site
ln -sf /home/dev/strategy_lab/nginx/sites-available/lab.m4s8.dev /etc/nginx/sites-enabled/

# Test nginx configuration
echo -e "${GREEN}Testing nginx configuration...${NC}"
nginx -t

# Setup SSL certificate if not exists
if [ ! -f /etc/letsencrypt/live/lab.m4s8.dev/fullchain.pem ]; then
    echo -e "${YELLOW}SSL certificate not found. Setting up Let's Encrypt...${NC}"
    certbot certonly --nginx -d lab.m4s8.dev --non-interactive --agree-tos --email admin@m4s8.dev
fi

# Create environment file
echo -e "${GREEN}Creating environment configuration...${NC}"
cat > /home/dev/strategy_lab/.env.production << EOF
# Database
DATABASE_URL=postgresql://strategylab:password@localhost:5432/strategylab
DB_USER=strategylab
DB_PASSWORD=password
DB_NAME=strategylab

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=

# Security
JWT_SECRET=$(openssl rand -base64 32)

# API
CORS_ORIGINS=https://lab.m4s8.dev
ENVIRONMENT=production

# Frontend
NEXT_PUBLIC_API_URL=https://lab.m4s8.dev/api
EOF

chown dev:dev /home/dev/strategy_lab/.env.production
chmod 600 /home/dev/strategy_lab/.env.production

echo -e "${GREEN}Service setup complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Update the database credentials in /home/dev/strategy_lab/.env.production"
echo "2. Ensure PostgreSQL and Redis are installed and running"
echo "3. Run database migrations: cd /home/dev/strategy_lab/backend && uv run alembic upgrade head"
echo "4. Start services:"
echo "   sudo systemctl start strategylab-backend"
echo "   sudo systemctl start strategylab-frontend"
echo "   sudo systemctl reload nginx"
echo "5. Check service status:"
echo "   sudo systemctl status strategylab-backend"
echo "   sudo systemctl status strategylab-frontend"
echo "6. View logs:"
echo "   sudo journalctl -u strategylab-backend -f"
echo "   sudo journalctl -u strategylab-frontend -f"
echo "   tail -f /var/log/strategylab/*.log"
