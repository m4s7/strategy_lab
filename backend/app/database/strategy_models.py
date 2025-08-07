from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


class ParameterType(str, Enum):
    NUMBER = "number"
    BOOLEAN = "boolean"
    STRING = "string"
    SELECT = "select"
    DATE = "date"
    RANGE = "range"


class ValidationRule(BaseModel):
    min: Optional[float] = None
    max: Optional[float] = None
    step: Optional[float] = None
    required: Optional[bool] = None
    pattern: Optional[str] = None


class ParameterDefinition(BaseModel):
    name: str
    type: ParameterType
    description: str
    required: bool = False
    default: Optional[Any] = None
    validation: Optional[ValidationRule] = None
    options: Optional[List[Any]] = None  # For select type
    dependencies: Optional[List[str]] = None  # Parameters this depends on


class Strategy(BaseModel):
    id: str
    name: str
    description: str
    version: str = "1.0.0"
    author: str = "Unknown"
    category: str = "General"
    parameters: List[ParameterDefinition]
    documentation: Optional[str] = None
    default_params: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class StrategyListResponse(BaseModel):
    strategies: List[Strategy]
    total: int


class ConfigurationTemplate(BaseModel):
    id: str
    name: str
    strategy_id: str
    parameters: Dict[str, Any]
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    last_used: Optional[datetime] = None


class ConfigurationTemplateCreate(BaseModel):
    name: str
    strategy_id: str
    parameters: Dict[str, Any]
    description: Optional[str] = None


class ConfigurationTemplateResponse(BaseModel):
    id: str
    name: str
    strategy_id: str
    parameters: Dict[str, Any]
    description: Optional[str] = None
    created_at: datetime
    last_used: Optional[datetime] = None


class ParameterValidationRequest(BaseModel):
    parameters: Dict[str, Any]


class ParameterValidationError(BaseModel):
    parameter: str
    error: str


class ParameterValidationResponse(BaseModel):
    valid: bool
    errors: List[ParameterValidationError] = []
