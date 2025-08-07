# Strategy Lab

A modular backtesting and optimization framework for CME MNQ futures trading strategies, built with Next.js frontend and FastAPI backend.

## Features

- 🚀 **Modern Stack**: Next.js 14+ with App Router, FastAPI with async/await
- 📊 **Real-time Updates**: WebSocket integration for live data streaming
- 🎨 **Beautiful UI**: shadcn/ui components with dark theme
- 🗄️ **Flexible Database**: SQLite with SQLAlchemy ORM and migrations
- 🐳 **Docker Ready**: Full containerized development environment
- 🔧 **Development Tools**: Hot reload, linting, formatting, pre-commit hooks

## Quick Start

### Prerequisites

- Node.js 20+
- Python 3.12+
- pnpm package manager
- uv Python package manager
- Docker (optional)

### Option 1: Local Development

```bash
# Clone the repository
git clone <repository-url>
cd strategy_lab

# Set up the entire development environment
make setup

# Start development servers
make dev
```

Access the application:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### Option 2: Docker Development

```bash
# Start with Docker Compose
make docker-dev
```

## Development Commands

### Environment Management
```bash
make setup         # Set up development environment
make clean         # Clean build artifacts and caches
make health-check  # Check if all services are running
```

### Development
```bash
make dev           # Start development servers
make build         # Build applications for production
make test          # Run all tests
make lint          # Run linting checks
make format        # Format code
```

### Database
```bash
make db-migrate    # Run database migrations
make db-seed       # Seed database with sample data
make db-reset      # Reset database (migrate + seed)
```

### Docker
```bash
make docker-build  # Build Docker images
make docker-dev    # Start development with Docker
make docker-clean  # Clean Docker containers and images
```

## Project Structure

```
strategy_lab/
├── frontend/              # Next.js frontend application
│   ├── src/
│   │   ├── app/          # Next.js App Router pages
│   │   ├── components/   # Reusable UI components
│   │   ├── lib/          # Utilities and configurations
│   │   └── hooks/        # Custom React hooks
│   └── public/           # Static assets
├── backend/              # FastAPI backend application
│   ├── app/
│   │   ├── api/          # API routes
│   │   ├── database/     # Database models and configuration
│   │   ├── websocket/    # WebSocket handlers
│   │   └── core/         # Core application logic
│   ├── tests/            # Backend tests
│   └── alembic/          # Database migrations
└── docs/                 # Documentation and project stories
```

## Technology Stack

### Frontend
- **Next.js 14+** with App Router and TypeScript
- **shadcn/ui** for component library
- **Tailwind CSS** for styling
- **Zustand** for state management
- **WebSocket** client for real-time updates

### Backend
- **FastAPI** with async/await patterns
- **SQLAlchemy** with async support
- **Alembic** for database migrations
- **WebSocket** support with connection management
- **SQLite** database (development)

### Development Tools
- **pnpm** for frontend package management
- **uv** for Python package management
- **ESLint** and **Prettier** for code quality
- **Black** and **ruff** for Python formatting
- **pre-commit** hooks for automated code quality
- **Docker** and **Docker Compose** for containerization

## Environment Variables

### Frontend (.env.local)
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

### Backend (.env)
```bash
DATABASE_URL=sqlite+aiosqlite:///./data/strategy_lab.db
DEBUG=True
ENVIRONMENT=development
CORS_ORIGINS=["http://localhost:3000"]
```

## Development Workflow

1. **Code Quality**: All commits go through pre-commit hooks that run linting, formatting, and basic checks
2. **Hot Reload**: Both frontend and backend support hot reload for rapid development
3. **API First**: Backend API is fully documented with automatic OpenAPI/Swagger docs
4. **Type Safety**: Full TypeScript on frontend, Python typing on backend
5. **Testing**: Comprehensive test setup (tests to be implemented)

## Common Tasks

### Adding a New API Endpoint
1. Create the endpoint in `backend/app/api/`
2. Add database models if needed in `backend/app/database/models.py`
3. Create migration: `cd backend && alembic revision --autogenerate -m "description"`
4. Run migration: `make db-migrate`

### Adding a New Frontend Component
1. Create component in `frontend/src/components/`
2. Follow existing patterns for shadcn/ui integration
3. Add to the relevant page in `frontend/src/app/`

### Real-time Features
- Use the WebSocket client in `frontend/src/lib/websocket/`
- Backend WebSocket handlers in `backend/app/websocket/`
- Automatic reconnection and subscription management included

## Troubleshooting

### Development Server Won't Start
```bash
# Check if ports are in use
lsof -i :3000
lsof -i :8000

# Clean and restart
make clean
make setup
make dev
```

### Database Issues
```bash
# Reset database completely
make db-reset

# Check database health
make health-check
```

### Docker Issues
```bash
# Clean Docker environment
make docker-clean

# Rebuild from scratch
make docker-build
make docker-dev
```

### Pre-commit Hooks Not Working
```bash
# Install pre-commit hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

## License

This project is private and proprietary.

## Contributing

1. Follow the existing code style and patterns
2. Run `make test` before committing
3. All commits must pass pre-commit hooks
4. Update documentation for new features
