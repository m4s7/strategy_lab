#!/bin/bash

# Setup systemd services for Strategy Lab

set -e

echo "=== Setting up systemd services ==="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run with sudo: sudo bash setup_services.sh"
    exit 1
fi

# Get paths
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_BINARY="$PROJECT_ROOT/standalone_api/target/release/strategy_lab_api"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

# Check if binaries exist
if [ ! -f "$BACKEND_BINARY" ]; then
    echo "Backend binary not found. Please run build_production.sh first"
    exit 1
fi

if [ ! -d "$FRONTEND_DIR/.next" ]; then
    echo "Frontend build not found. Please run build_production.sh first"
    exit 1
fi

# Create backend service
echo "Creating backend service..."
cat > /etc/systemd/system/strategylab-backend.service <<EOF
[Unit]
Description=Strategy Lab Backend API Server
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=simple
User=$SUDO_USER
Group=$SUDO_USER
WorkingDirectory=$PROJECT_ROOT/standalone_api
Environment="DATABASE_URL=postgresql://strategy_user:strategy_pass@localhost:5432/strategy_lab"
Environment="RUST_LOG=info"
ExecStart=$BACKEND_BINARY
Restart=always
RestartSec=10
StandardOutput=append:/var/log/strategylab/backend.log
StandardError=append:/var/log/strategylab/backend-error.log

[Install]
WantedBy=multi-user.target
EOF

# Create frontend service
echo "Creating frontend service..."
cat > /etc/systemd/system/strategylab-frontend.service <<EOF
[Unit]
Description=Strategy Lab Frontend Next.js Server
After=network.target strategylab-backend.service
Wants=strategylab-backend.service

[Service]
Type=simple
User=$SUDO_USER
Group=$SUDO_USER
WorkingDirectory=$FRONTEND_DIR
Environment="NODE_ENV=production"
Environment="PORT=3000"
ExecStart=/usr/bin/npm run start
Restart=always
RestartSec=10
StandardOutput=append:/var/log/strategylab/frontend.log
StandardError=append:/var/log/strategylab/frontend-error.log

[Install]
WantedBy=multi-user.target
EOF

# Create log directory
mkdir -p /var/log/strategylab
chown -R $SUDO_USER:$SUDO_USER /var/log/strategylab

# Reload systemd
echo "Reloading systemd daemon..."
systemctl daemon-reload

# Enable services
echo "Enabling services..."
systemctl enable strategylab-backend.service
systemctl enable strategylab-frontend.service

# Start services
echo "Starting services..."
systemctl start strategylab-backend.service
sleep 3 # Give backend time to start
systemctl start strategylab-frontend.service

# Check status
echo ""
echo "=== Service Status ==="
systemctl status strategylab-backend.service --no-pager | head -n 5
echo ""
systemctl status strategylab-frontend.service --no-pager | head -n 5

echo ""
echo "=== Services Setup Complete ==="
echo ""
echo "Services are now running and will start automatically on boot"
echo ""
echo "Commands:"
echo "  View backend logs:  sudo journalctl -u strategylab-backend -f"
echo "  View frontend logs: sudo journalctl -u strategylab-frontend -f"
echo "  Restart backend:    sudo systemctl restart strategylab-backend"
echo "  Restart frontend:   sudo systemctl restart strategylab-frontend"
echo ""
echo "Next: Run 'sudo bash scripts/setup_nginx.sh' to configure Nginx reverse proxy"
echo ""