# Strategy Lab Development Makefile

.PHONY: help dev build setup clean test lint format docker-build docker-dev docker-clean db-migrate db-seed db-reset

# Default target
help:
	@echo "Strategy Lab Development Commands"
	@echo "================================"
	@echo ""
	@echo "Environment Setup:"
	@echo "  setup         - Set up development environment"
	@echo "  clean         - Clean build artifacts and caches"
	@echo ""
	@echo "Development:"
	@echo "  dev           - Start development servers"
	@echo "  build         - Build applications for production"
	@echo "  test          - Run all tests"
	@echo "  lint          - Run linting checks"
	@echo "  format        - Format code"
	@echo ""
	@echo "Docker Commands:"
	@echo "  docker-build  - Build Docker images"
	@echo "  docker-dev    - Start development with Docker"
	@echo "  docker-clean  - Clean Docker containers and images"
	@echo ""
	@echo "Database:"
	@echo "  db-migrate    - Run database migrations"
	@echo "  db-seed       - Seed database with sample data"
	@echo "  db-reset      - Reset database (migrate + seed)"

# Environment setup
setup:
	@echo "Setting up Strategy Lab development environment..."
	@echo "Installing frontend dependencies..."
	cd frontend && pnpm install
	@echo "Setting up backend environment..."
	cd backend && uv venv backend-env && ./backend-env/bin/pip install -r requirements-dev.txt
	@echo "Running database migrations..."
	cd backend && ./backend-env/bin/python -m alembic upgrade head
	@echo "Seeding database..."
	cd backend && ./backend-env/bin/python seed_database.py
	@echo "✅ Development environment setup complete!"

# Development servers
dev:
	@echo "Starting Strategy Lab development servers..."
	@echo "Frontend will be available at: http://localhost:3000"
	@echo "Backend will be available at: http://localhost:8000"
	@echo "Backend API docs: http://localhost:8000/docs"
	@echo ""
	@echo "Starting backend server..."
	cd backend && ./backend-env/bin/python run_dev.py &
	@echo "Waiting for backend to start..."
	@sleep 3
	@echo "Starting frontend server..."
	cd frontend && pnpm run dev

# Build applications
build:
	@echo "Building applications..."
	cd frontend && pnpm run build
	cd backend && ./backend-env/bin/python -c "from app.main import app; print('Backend build check passed')"

# Testing
test:
	@echo "Running tests..."
	cd frontend && pnpm run lint
	cd backend && ./backend-env/bin/python -m pytest tests/ -v
	@echo "Running API tests..."
	cd backend && ./backend-env/bin/python test_api_with_db.py
	@echo "Testing WebSocket functionality..."
	cd backend && ./backend-env/bin/python test_websocket.py

# Code quality
lint:
	@echo "Running linting checks..."
	cd frontend && pnpm run lint
	cd backend && ./backend-env/bin/python -m ruff check .
	cd backend && ./backend-env/bin/python -m black --check .

format:
	@echo "Formatting code..."
	cd frontend && pnpm run format
	cd backend && ./backend-env/bin/python -m black .
	cd backend && ./backend-env/bin/python -m ruff --fix .

# Docker commands
docker-build:
	@echo "Building Docker images..."
	docker-compose build

docker-dev:
	@echo "Starting development with Docker..."
	@echo "Frontend: http://localhost:3000"
	@echo "Backend: http://localhost:8000"
	docker-compose up --build

docker-clean:
	@echo "Cleaning Docker containers and images..."
	docker-compose down -v
	docker system prune -f

# Database commands
db-migrate:
	@echo "Running database migrations..."
	cd backend && ./backend-env/bin/python -m alembic upgrade head

db-seed:
	@echo "Seeding database with sample data..."
	cd backend && ./backend-env/bin/python seed_database.py

db-reset:
	@echo "Resetting database..."
	cd backend && rm -f data/strategy_lab.db
	cd backend && ./backend-env/bin/python -m alembic upgrade head
	cd backend && ./backend-env/bin/python seed_database.py

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	cd frontend && rm -rf .next node_modules/.cache
	cd backend && find . -type d -name __pycache__ -delete
	cd backend && find . -name "*.pyc" -delete
	@echo "✅ Clean complete!"

# Development environment health check
health-check:
	@echo "Checking development environment health..."
	@echo "1. Testing backend health..."
	@curl -s http://localhost:8000/health > /dev/null && echo "✅ Backend is healthy" || echo "❌ Backend is not responding"
	@echo "2. Testing frontend..."
	@curl -s http://localhost:3000 > /dev/null && echo "✅ Frontend is healthy" || echo "❌ Frontend is not responding"
	@echo "3. Testing database..."
	cd backend && ./backend-env/bin/python test_database.py > /dev/null && echo "✅ Database is healthy" || echo "❌ Database has issues"
	@echo "4. Testing WebSocket..."
	cd backend && timeout 5 ./backend-env/bin/python test_websocket.py > /dev/null && echo "✅ WebSocket is healthy" || echo "❌ WebSocket has issues"