# Development Guide

This guide provides detailed information for developers working on Strategy Lab.

## Development Environment Setup

### Initial Setup

1. **Install Dependencies**:
   ```bash
   # Install Node.js 20+, Python 3.12+, pnpm, uv
   make setup
   ```

2. **Install Pre-commit Hooks**:
   ```bash
   pre-commit install
   ```

3. **Environment Variables**:
   - Copy `.env.example` to `.env` in backend/
   - Copy `.env.local.example` to `.env.local` in frontend/
   - Configure database and API URLs

### Development Workflow

1. **Start Development Servers**:
   ```bash
   make dev
   ```
   This starts both frontend (port 3000) and backend (port 8000) with hot reload.

2. **Code Quality Checks**:
   ```bash
   make lint          # Check code quality
   make format        # Auto-format code
   make test          # Run tests
   ```

3. **Database Operations**:
   ```bash
   make db-migrate    # Apply migrations
   make db-reset      # Reset with fresh data
   ```

## Architecture Overview

### Frontend Architecture
- **Next.js App Router**: File-based routing with server components
- **Components**: shadcn/ui components in `src/components/`
- **State Management**: Zustand stores for global state
- **WebSocket**: Real-time connection management
- **API Communication**: Fetch-based API client

### Backend Architecture
- **FastAPI**: Async Python web framework
- **SQLAlchemy**: Async ORM with SQLite
- **WebSocket**: Connection manager with pub/sub
- **Dependency Injection**: FastAPI's DI system
- **Database Migrations**: Alembic for schema changes

### Database Schema
```sql
-- Core entities
backtests (id, strategy_id, config, status, created_at, updated_at)
backtest_results (backtest_id, metrics, trades, created_at)
optimization_jobs (id, strategy_id, parameters, status, created_at)
optimization_results (job_id, parameter_set, performance_metrics)
```

## Code Style Guide

### TypeScript/JavaScript Standards
- Use TypeScript for all new code
- Prefer functional components with hooks
- Use proper TypeScript types (avoid `any`)
- Import organization: external → internal → relative
- Use descriptive variable and function names

### Python Standards
- Follow PEP 8 with Black formatting
- Use type hints for all functions
- Prefer async/await for I/O operations
- Use SQLAlchemy 2.0+ syntax
- Document functions with docstrings

### File Naming Conventions
- Frontend components: `PascalCase.tsx`
- Backend modules: `snake_case.py`
- Configuration files: `kebab-case.yaml`
- Database migrations: timestamp-based (Alembic default)

## Testing Strategy

### Frontend Testing
- Component testing with Jest/React Testing Library
- Integration testing for user workflows
- E2E testing with Playwright (planned)
- Mock API responses for testing

### Backend Testing
- Unit tests for business logic
- Integration tests with test database
- API endpoint testing with TestClient
- WebSocket connection testing

### Test Commands
```bash
# Frontend tests
cd frontend && pnpm test
cd frontend && pnpm test:watch

# Backend tests
cd backend && uv run pytest
cd backend && uv run pytest --cov=app
```

## API Development

### Adding New Endpoints
1. Create route in `backend/app/api/`
2. Add request/response models with Pydantic
3. Add database operations if needed
4. Update OpenAPI documentation
5. Add tests for the endpoint

### WebSocket Events
1. Add event handler in `backend/app/websocket/`
2. Update connection manager if needed
3. Add client-side handling in `frontend/src/lib/websocket/`
4. Test real-time functionality

## Database Management

### Creating Migrations
```bash
cd backend
alembic revision --autogenerate -m "Add new table"
alembic upgrade head
```

### Database Seeding
```bash
make db-seed  # Add sample data for development
```

### Schema Changes
1. Modify models in `backend/app/database/models.py`
2. Create migration with Alembic
3. Test migration up and down
4. Update API endpoints if needed

## Performance Considerations

### Frontend Performance
- Use Next.js Image component for optimization
- Implement proper loading states
- Use React.memo for expensive components
- Optimize bundle size with dynamic imports

### Backend Performance
- Use async/await for all I/O operations
- Implement proper database indexing
- Use connection pooling for database
- Cache frequently accessed data

### Real-time Updates
- Minimize WebSocket message frequency
- Use message compression for large payloads
- Implement proper error handling and reconnection
- Batch updates when possible

## Security Guidelines

### Authentication (Future)
- JWT tokens for API authentication
- Secure token storage in browser
- Token refresh mechanism
- Role-based access control

### Data Protection
- Validate all input data
- Sanitize database queries (SQLAlchemy protects against SQL injection)
- Use HTTPS in production
- Implement proper CORS configuration

### Environment Security
- Never commit secrets to version control
- Use environment variables for configuration
- Implement proper error handling (don't leak sensitive info)
- Regular dependency updates

## Debugging Tips

### Frontend Debugging
- Use React DevTools browser extension
- Enable source maps in development
- Use console.log strategically (remove before commit)
- Test in multiple browsers

### Backend Debugging
- Use debugger with IDE breakpoints
- Enable SQLAlchemy query logging
- Use FastAPI's automatic API documentation
- Test API endpoints with curl or Postman

### WebSocket Debugging
- Use browser DevTools Network tab
- Implement proper logging for connection events
- Test connection drops and reconnection
- Monitor message queuing and processing

## Deployment Notes

### Production Build
```bash
make build  # Build optimized frontend and test backend
```

### Docker Development
```bash
make docker-dev     # Full containerized development
make docker-clean   # Clean up containers
```

### Environment Configuration
- Production uses different database settings
- API URLs configured through environment variables
- CORS settings adjusted for production domains
- Error handling differs between dev/prod

## Common Issues and Solutions

### Port Conflicts
```bash
# Check what's using ports
lsof -i :3000
lsof -i :8000

# Kill processes if needed
kill -9 <PID>
```

### Database Connection Issues
```bash
# Reset database completely
make db-reset

# Check database file permissions
ls -la backend/data/
```

### Node Module Issues
```bash
# Clean frontend dependencies
cd frontend
rm -rf node_modules .next
pnpm install
```

### Pre-commit Hook Failures
```bash
# Run hooks manually to see errors
pre-commit run --all-files

# Skip hooks temporarily (not recommended)
git commit --no-verify
```

## VS Code Configuration

Recommended extensions:
- TypeScript and JavaScript Language Features
- Python
- Pylance
- ESLint
- Prettier
- SQLite Viewer
- Docker

### Settings.json additions:
```json
{
  "python.defaultInterpreterPath": "./backend/backend-env/bin/python",
  "python.formatting.provider": "black",
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "typescript.preferences.importModuleSpecifier": "relative"
}
```

## Contributing Workflow

1. Create feature branch from main
2. Make changes with proper tests
3. Run quality checks: `make lint test`
4. Commit with descriptive messages
5. Push and create pull request
6. Address review feedback
7. Merge after approval

## Getting Help

- Check this documentation first
- Review existing code patterns
- Check API documentation at http://localhost:8000/docs
- Look at component implementations in Storybook (planned)
- Ask questions in team discussions
