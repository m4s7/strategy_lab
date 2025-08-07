# Strategy Lab Backend API

FastAPI backend infrastructure for the Strategy Lab trading backtesting platform.

## Quick Start

1. **Install dependencies:**
   ```bash
   uv venv backend-env
   source backend-env/bin/activate
   uv pip install -r requirements.txt
   ```

2. **Set up environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Run development server:**
   ```bash
   python run_dev.py
   ```

4. **Access the API:**
   - API Server: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app initialization
│   ├── core/
│   │   ├── config.py        # Configuration management
│   │   ├── dependencies.py  # Dependency injection
│   │   └── middleware.py    # Custom middleware
│   ├── api/
│   │   ├── router.py        # Main API router
│   │   └── health.py        # Health check endpoints
│   └── models/
│       └── base.py          # Base Pydantic models
├── requirements.txt         # Production dependencies
├── requirements-dev.txt     # Development dependencies
└── .env.example            # Environment configuration template
```

## API Endpoints

### Health Check
- `GET /health` - Simple health check
- `GET /api/v1/health/` - Detailed health information
- `GET /api/v1/health/detailed` - Extended system information

### Documentation
- `GET /docs` - Interactive API documentation (Swagger UI)
- `GET /redoc` - Alternative API documentation (ReDoc)
- `GET /openapi.json` - OpenAPI schema

## Development

### Running Tests
```bash
# Install development dependencies
uv pip install -r requirements-dev.txt

# Run basic API test
python test_api.py
```

### Environment Variables

See `.env.example` for all available configuration options.

Key variables:
- `DEBUG`: Enable debug mode (default: True)
- `ENVIRONMENT`: Application environment (default: development)
- `PORT`: Server port (default: 8000)
- `CORS_ORIGINS`: Allowed CORS origins (default: ["http://localhost:3000"])

## Features

✅ **Completed:**
- FastAPI application setup with proper structure
- Health check endpoints with detailed system information
- CORS configuration for frontend integration
- Request/response logging middleware
- Environment-based configuration system
- Auto-generated API documentation
- Proper error handling with structured responses
- Request ID tracking for debugging

🚧 **Coming Next:**
- Database integration (UI_003)
- WebSocket support (UI_004)
- Strategy configuration endpoints (UI_012)
- Backtest execution APIs (UI_014)

## Architecture

The backend follows a modular architecture:

- **Core**: Configuration, middleware, and dependencies
- **API**: REST endpoints organized by feature
- **Models**: Pydantic models for request/response validation
- **Middleware**: Custom middleware for logging and CORS

All endpoints support:
- Automatic request/response validation
- Request ID tracking
- Structured error responses
- CORS for frontend integration