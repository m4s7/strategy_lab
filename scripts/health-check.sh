#!/bin/bash
# Health check script for Strategy Lab services

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "Strategy Lab Health Check"
echo "========================"
echo ""

# Check Backend API
echo -n "Backend API: "
if curl -s -f http://localhost:8000/api/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Healthy${NC}"
else
    echo -e "${RED}✗ Unhealthy${NC}"
fi

# Check Frontend
echo -n "Frontend: "
if curl -s -f http://localhost:3000/api/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Healthy${NC}"
else
    echo -e "${RED}✗ Unhealthy${NC}"
fi

# Check Nginx
echo -n "Nginx (HTTPS): "
if curl -s -f -k https://lab.m4s8.dev/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Healthy${NC}"
else
    echo -e "${RED}✗ Unhealthy${NC}"
fi

# Check PostgreSQL
echo -n "PostgreSQL: "
if sudo -u postgres pg_isready > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Healthy${NC}"
else
    echo -e "${RED}✗ Unhealthy${NC}"
fi

# Check Redis
echo -n "Redis: "
if redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Healthy${NC}"
else
    echo -e "${RED}✗ Unhealthy${NC}"
fi

echo ""
echo "Service URLs:"
echo "- Frontend: https://lab.m4s8.dev"
echo "- API: https://lab.m4s8.dev/api"
echo "- WebSocket: wss://lab.m4s8.dev/ws"
