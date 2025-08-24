#!/bin/bash

# Build Script for Production Deployment
# Builds both frontend and backend in production mode

set -e

echo "=== Building Strategy Lab for Production ==="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Build Backend
echo -e "${YELLOW}Building Backend API Server...${NC}"
cd "$PROJECT_ROOT/standalone_api"

# Build in release mode
cargo build --release

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Backend built successfully${NC}"
    echo "  Binary: $PROJECT_ROOT/standalone_api/target/release/strategy_lab_api"
else
    echo -e "${RED}✗ Backend build failed${NC}"
    exit 1
fi

# Build Frontend
echo ""
echo -e "${YELLOW}Building Frontend...${NC}"
cd "$PROJECT_ROOT/frontend"

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

# Build Next.js for production
npm run build

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Frontend built successfully${NC}"
else
    echo -e "${RED}✗ Frontend build failed${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}=== Production Build Complete ===${NC}"
echo ""
echo "Next steps:"
echo "1. Run: sudo bash scripts/setup_services.sh"
echo "2. This will configure systemd services for auto-start"
echo ""