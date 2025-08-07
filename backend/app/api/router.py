from fastapi import APIRouter
from .health import router as health_router
from .backtests import router as backtests_router
from .system import router as system_router
from .strategies import router as strategies_router
from .data import router as data_router
from .execution import router as execution_router
from .results import router as results_router

# Create the main API router
api_router = APIRouter(prefix="/api/v1")

# Include all sub-routers
api_router.include_router(health_router)
api_router.include_router(backtests_router)
api_router.include_router(system_router, prefix="/system", tags=["system"])
api_router.include_router(strategies_router, tags=["strategies"])
api_router.include_router(data_router, tags=["data"])
api_router.include_router(execution_router, tags=["execution"])
api_router.include_router(results_router, tags=["results"])
