from datetime import datetime
from typing import Optional, Any, Dict
from pydantic import BaseModel, ConfigDict


class BaseResponse(BaseModel):
    """Base response model for all API responses."""

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)


class HealthResponse(BaseResponse):
    """Health check response model."""

    status: str
    timestamp: datetime
    version: str
    environment: str
    app_name: str
    database: Optional[str] = None
    system_info: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseResponse):
    """Standard error response model."""

    error: str
    message: str
    detail: Optional[str] = None
    timestamp: datetime
    request_id: Optional[str] = None


class SuccessResponse(BaseResponse):
    """Generic success response model."""

    message: str
    data: Optional[Any] = None
    timestamp: datetime
