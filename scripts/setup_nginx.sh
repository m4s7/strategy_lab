#!/bin/bash

# Setup Nginx as reverse proxy for Strategy Lab

set -e

echo "=== Setting up Nginx reverse proxy ==="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run with sudo: sudo bash setup_nginx.sh"
    exit 1
fi

# Install Nginx if not installed
if ! command -v nginx &> /dev/null; then
    echo "Installing Nginx..."
    apt-get update
    apt-get install -y nginx
fi

# Backup existing default config if it exists
if [ -f /etc/nginx/sites-available/default ]; then
    cp /etc/nginx/sites-available/default /etc/nginx/sites-available/default.backup
fi

# Create Strategy Lab Nginx configuration
echo "Creating Nginx configuration..."
cat > /etc/nginx/sites-available/strategylab <<'EOF'
server {
    listen 80 default_server;
    listen [::]:80 default_server;

    server_name _;

    # Logging
    access_log /var/log/nginx/strategylab_access.log;
    error_log /var/log/nginx/strategylab_error.log;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;

    # API routes - proxy to backend
    location /api/ {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 86400;
    }

    # Health check - proxy to backend
    location /health {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Frontend routes - proxy to Next.js
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 86400;
    }

    # Static assets caching
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Cache static assets
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# Remove default site and enable Strategy Lab
rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/strategylab /etc/nginx/sites-enabled/

# Test Nginx configuration
echo "Testing Nginx configuration..."
nginx -t

if [ $? -eq 0 ]; then
    echo "Nginx configuration is valid"
    
    # Enable and start Nginx
    systemctl enable nginx
    systemctl restart nginx
    
    echo ""
    echo "=== Nginx Setup Complete ==="
    echo ""
    echo "Strategy Lab is now accessible at:"
    echo "  http://$(hostname -I | awk '{print $1}')"
    echo "  http://localhost"
    echo ""
    echo "API endpoints are available at:"
    echo "  http://$(hostname -I | awk '{print $1}')/api/"
    echo ""
    echo "Nginx logs:"
    echo "  Access: /var/log/nginx/strategylab_access.log"
    echo "  Error:  /var/log/nginx/strategylab_error.log"
    echo ""
else
    echo "Nginx configuration test failed"
    exit 1
fi