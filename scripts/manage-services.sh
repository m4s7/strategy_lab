#!/bin/bash
# Service management script for Strategy Lab

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check service status
check_status() {
    echo -e "${BLUE}=== Service Status ===${NC}"

    # Backend status
    if systemctl is-active --quiet strategylab-backend; then
        echo -e "Backend: ${GREEN}Running${NC}"
    else
        echo -e "Backend: ${RED}Stopped${NC}"
    fi

    # Frontend status
    if systemctl is-active --quiet strategylab-frontend; then
        echo -e "Frontend: ${GREEN}Running${NC}"
    else
        echo -e "Frontend: ${RED}Stopped${NC}"
    fi

    # Nginx status
    if systemctl is-active --quiet nginx; then
        echo -e "Nginx: ${GREEN}Running${NC}"
    else
        echo -e "Nginx: ${RED}Stopped${NC}"
    fi

    # PostgreSQL status
    if systemctl is-active --quiet postgresql; then
        echo -e "PostgreSQL: ${GREEN}Running${NC}"
    else
        echo -e "PostgreSQL: ${RED}Stopped${NC}"
    fi

    # Redis status
    if systemctl is-active --quiet redis || systemctl is-active --quiet redis-server; then
        echo -e "Redis: ${GREEN}Running${NC}"
    else
        echo -e "Redis: ${RED}Stopped${NC}"
    fi
}

# Function to start all services
start_all() {
    echo -e "${GREEN}Starting all services...${NC}"
    sudo systemctl start postgresql
    sudo systemctl start redis || sudo systemctl start redis-server
    sudo systemctl start strategylab-backend
    sudo systemctl start strategylab-frontend
    sudo systemctl start nginx
    echo -e "${GREEN}All services started${NC}"
}

# Function to stop all services
stop_all() {
    echo -e "${YELLOW}Stopping all services...${NC}"
    sudo systemctl stop strategylab-frontend
    sudo systemctl stop strategylab-backend
    echo -e "${GREEN}Application services stopped${NC}"
}

# Function to restart all services
restart_all() {
    echo -e "${YELLOW}Restarting all services...${NC}"
    sudo systemctl restart strategylab-backend
    sudo systemctl restart strategylab-frontend
    sudo systemctl reload nginx
    echo -e "${GREEN}All services restarted${NC}"
}

# Function to show logs
show_logs() {
    echo -e "${BLUE}=== Recent Logs ===${NC}"
    echo -e "${YELLOW}Backend logs:${NC}"
    sudo journalctl -u strategylab-backend -n 20 --no-pager
    echo ""
    echo -e "${YELLOW}Frontend logs:${NC}"
    sudo journalctl -u strategylab-frontend -n 20 --no-pager
}

# Function to follow logs
follow_logs() {
    echo -e "${BLUE}Following logs (Ctrl+C to exit)...${NC}"
    sudo journalctl -u strategylab-backend -u strategylab-frontend -f
}

# Function to update and restart
update_and_restart() {
    echo -e "${BLUE}Updating and restarting services...${NC}"

    # Backend
    echo -e "${YELLOW}Updating backend...${NC}"
    cd /home/dev/strategy_lab/backend
    uv sync

    # Frontend
    echo -e "${YELLOW}Updating frontend...${NC}"
    cd /home/dev/strategy_lab/frontend
    pnpm install --frozen-lockfile
    pnpm run build

    # Restart services
    restart_all
}

# Main menu
case "$1" in
    status)
        check_status
        ;;
    start)
        start_all
        sleep 2
        check_status
        ;;
    stop)
        stop_all
        ;;
    restart)
        restart_all
        sleep 2
        check_status
        ;;
    logs)
        show_logs
        ;;
    follow)
        follow_logs
        ;;
    update)
        update_and_restart
        ;;
    *)
        echo "Strategy Lab Service Manager"
        echo "=========================="
        echo ""
        echo "Usage: $0 {status|start|stop|restart|logs|follow|update}"
        echo ""
        echo "Commands:"
        echo "  status  - Show status of all services"
        echo "  start   - Start all services"
        echo "  stop    - Stop application services"
        echo "  restart - Restart all services"
        echo "  logs    - Show recent logs"
        echo "  follow  - Follow logs in real-time"
        echo "  update  - Update dependencies and restart"
        echo ""
        check_status
        ;;
esac
