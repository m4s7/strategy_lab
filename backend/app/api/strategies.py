from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.dependencies import get_db
from ..database.strategy_models import (
    Strategy,
    StrategyListResponse,
    ConfigurationTemplate,
    ConfigurationTemplateCreate,
    ConfigurationTemplateResponse,
    ParameterValidationRequest,
    ParameterValidationResponse,
    ParameterValidationError,
    ParameterType,
    ParameterDefinition,
    ValidationRule
)
from datetime import datetime
import uuid

router = APIRouter(prefix="/strategies", tags=["strategies"])

# Mock strategy registry - in production this would come from a database or strategy registry
MOCK_STRATEGIES = {
    "order_book_scalper": Strategy(
        id="order_book_scalper",
        name="Order Book Scalper",
        description="A scalping strategy that uses Level 2 market data to identify short-term opportunities",
        version="2.1.0",
        author="Strategy Lab Team", 
        category="Scalping",
        documentation="Advanced order book analysis for high-frequency trading on MNQ futures",
        parameters=[
            ParameterDefinition(
                name="tick_threshold",
                type=ParameterType.NUMBER,
                description="Minimum tick movement to trigger entry",
                required=True,
                default=2,
                validation=ValidationRule(min=1, max=10, step=1)
            ),
            ParameterDefinition(
                name="position_size",
                type=ParameterType.NUMBER,
                description="Number of contracts per trade",
                required=True,
                default=1,
                validation=ValidationRule(min=1, max=10, step=1)
            ),
            ParameterDefinition(
                name="stop_loss_ticks",
                type=ParameterType.NUMBER,
                description="Stop loss in ticks",
                required=True,
                default=8,
                validation=ValidationRule(min=2, max=20, step=1)
            ),
            ParameterDefinition(
                name="take_profit_ticks",
                type=ParameterType.NUMBER,
                description="Take profit in ticks",
                required=True,
                default=6,
                validation=ValidationRule(min=2, max=20, step=1)
            ),
            ParameterDefinition(
                name="max_holding_seconds",
                type=ParameterType.NUMBER,
                description="Maximum seconds to hold a position",
                required=True,
                default=300,
                validation=ValidationRule(min=10, max=1800, step=10)
            ),
            ParameterDefinition(
                name="enable_short_trades",
                type=ParameterType.BOOLEAN,
                description="Allow short selling",
                required=False,
                default=True
            ),
            ParameterDefinition(
                name="trading_session",
                type=ParameterType.SELECT,
                description="Trading session to operate in",
                required=True,
                default="regular",
                options=["regular", "overnight", "pre_market", "all"]
            )
        ],
        default_params={
            "tick_threshold": 2,
            "position_size": 1,
            "stop_loss_ticks": 8,
            "take_profit_ticks": 6,
            "max_holding_seconds": 300,
            "enable_short_trades": True,
            "trading_session": "regular"
        }
    ),
    "momentum_breakout": Strategy(
        id="momentum_breakout",
        name="Momentum Breakout",
        description="Identifies momentum breakouts using volume and price action",
        version="1.5.0",
        author="Strategy Lab Team",
        category="Momentum",
        documentation="Volume-weighted momentum breakout strategy for trending markets",
        parameters=[
            ParameterDefinition(
                name="breakout_threshold",
                type=ParameterType.NUMBER,
                description="Price movement threshold for breakout detection",
                required=True,
                default=0.25,
                validation=ValidationRule(min=0.1, max=2.0, step=0.05)
            ),
            ParameterDefinition(
                name="volume_multiplier",
                type=ParameterType.NUMBER,
                description="Volume must be X times average volume",
                required=True,
                default=2.0,
                validation=ValidationRule(min=1.1, max=5.0, step=0.1)
            ),
            ParameterDefinition(
                name="lookback_period",
                type=ParameterType.NUMBER,
                description="Lookback period for average calculations (minutes)",
                required=True,
                default=15,
                validation=ValidationRule(min=5, max=60, step=5)
            ),
            ParameterDefinition(
                name="risk_percent",
                type=ParameterType.NUMBER,
                description="Risk percentage per trade",
                required=True,
                default=1.0,
                validation=ValidationRule(min=0.1, max=5.0, step=0.1)
            )
        ],
        default_params={
            "breakout_threshold": 0.25,
            "volume_multiplier": 2.0,
            "lookback_period": 15,
            "risk_percent": 1.0
        }
    ),
    "mean_reversion": Strategy(
        id="mean_reversion",
        name="Mean Reversion",
        description="Trades against short-term price deviations from mean",
        version="1.3.0",
        author="Strategy Lab Team",
        category="Mean Reversion",
        documentation="Statistical mean reversion strategy using Bollinger Bands and RSI",
        parameters=[
            ParameterDefinition(
                name="bb_period",
                type=ParameterType.NUMBER,
                description="Bollinger Bands period",
                required=True,
                default=20,
                validation=ValidationRule(min=10, max=50, step=5)
            ),
            ParameterDefinition(
                name="bb_std_dev",
                type=ParameterType.NUMBER,
                description="Bollinger Bands standard deviations",
                required=True,
                default=2.0,
                validation=ValidationRule(min=1.5, max=3.0, step=0.1)
            ),
            ParameterDefinition(
                name="rsi_period",
                type=ParameterType.NUMBER,
                description="RSI calculation period",
                required=True,
                default=14,
                validation=ValidationRule(min=7, max=30, step=1)
            ),
            ParameterDefinition(
                name="rsi_oversold",
                type=ParameterType.NUMBER,
                description="RSI oversold threshold",
                required=True,
                default=30,
                validation=ValidationRule(min=20, max=40, step=5)
            ),
            ParameterDefinition(
                name="rsi_overbought",
                type=ParameterType.NUMBER,
                description="RSI overbought threshold",
                required=True,
                default=70,
                validation=ValidationRule(min=60, max=80, step=5)
            )
        ],
        default_params={
            "bb_period": 20,
            "bb_std_dev": 2.0,
            "rsi_period": 14,
            "rsi_oversold": 30,
            "rsi_overbought": 70
        }
    )
}

# Mock configuration templates storage
MOCK_TEMPLATES: Dict[str, ConfigurationTemplate] = {}


@router.get("/", response_model=StrategyListResponse)
async def get_strategies():
    """Get list of all available strategies."""
    strategies = list(MOCK_STRATEGIES.values())
    return StrategyListResponse(strategies=strategies, total=len(strategies))


@router.get("/{strategy_id}", response_model=Strategy)
async def get_strategy(strategy_id: str):
    """Get specific strategy by ID."""
    if strategy_id not in MOCK_STRATEGIES:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return MOCK_STRATEGIES[strategy_id]


@router.post("/{strategy_id}/validate", response_model=ParameterValidationResponse)
async def validate_strategy_parameters(
    strategy_id: str,
    request: ParameterValidationRequest
):
    """Validate strategy parameter configuration."""
    if strategy_id not in MOCK_STRATEGIES:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    strategy = MOCK_STRATEGIES[strategy_id]
    errors = []
    
    # Validate each parameter
    for param in strategy.parameters:
        value = request.parameters.get(param.name)
        
        # Check required parameters
        if param.required and (value is None or value == ""):
            errors.append(ParameterValidationError(
                parameter=param.name,
                error=f"{param.name} is required"
            ))
            continue
        
        # Skip validation if parameter is not provided and not required
        if value is None:
            continue
            
        # Type-specific validation
        if param.type == ParameterType.NUMBER and param.validation:
            try:
                num_value = float(value)
                if param.validation.min is not None and num_value < param.validation.min:
                    errors.append(ParameterValidationError(
                        parameter=param.name,
                        error=f"{param.name} must be at least {param.validation.min}"
                    ))
                if param.validation.max is not None and num_value > param.validation.max:
                    errors.append(ParameterValidationError(
                        parameter=param.name,
                        error=f"{param.name} must be at most {param.validation.max}"
                    ))
            except (ValueError, TypeError):
                errors.append(ParameterValidationError(
                    parameter=param.name,
                    error=f"{param.name} must be a valid number"
                ))
        
        elif param.type == ParameterType.SELECT and param.options:
            if value not in param.options:
                errors.append(ParameterValidationError(
                    parameter=param.name,
                    error=f"{param.name} must be one of: {', '.join(map(str, param.options))}"
                ))
    
    return ParameterValidationResponse(
        valid=len(errors) == 0,
        errors=errors
    )


@router.get("/{strategy_id}/templates", response_model=List[ConfigurationTemplateResponse])
async def get_strategy_templates(strategy_id: str):
    """Get configuration templates for a strategy."""
    if strategy_id not in MOCK_STRATEGIES:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    templates = [
        template for template in MOCK_TEMPLATES.values()
        if template.strategy_id == strategy_id
    ]
    
    return [
        ConfigurationTemplateResponse(
            id=template.id,
            name=template.name,
            strategy_id=template.strategy_id,
            parameters=template.parameters,
            description=template.description,
            created_at=template.created_at,
            last_used=template.last_used
        )
        for template in templates
    ]


@router.post("/{strategy_id}/templates", response_model=ConfigurationTemplateResponse)
async def create_strategy_template(
    strategy_id: str,
    template_data: ConfigurationTemplateCreate
):
    """Create a new configuration template."""
    if strategy_id not in MOCK_STRATEGIES:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    template_id = str(uuid.uuid4())
    template = ConfigurationTemplate(
        id=template_id,
        name=template_data.name,
        strategy_id=strategy_id,
        parameters=template_data.parameters,
        description=template_data.description,
        created_at=datetime.now()
    )
    
    MOCK_TEMPLATES[template_id] = template
    
    return ConfigurationTemplateResponse(
        id=template.id,
        name=template.name,
        strategy_id=template.strategy_id,
        parameters=template.parameters,
        description=template.description,
        created_at=template.created_at,
        last_used=template.last_used
    )


@router.get("/templates/{template_id}", response_model=ConfigurationTemplateResponse)
async def get_template(template_id: str):
    """Get specific configuration template."""
    if template_id not in MOCK_TEMPLATES:
        raise HTTPException(status_code=404, detail="Template not found")
    
    template = MOCK_TEMPLATES[template_id]
    # Update last used timestamp
    template.last_used = datetime.now()
    
    return ConfigurationTemplateResponse(
        id=template.id,
        name=template.name,
        strategy_id=template.strategy_id,
        parameters=template.parameters,
        description=template.description,
        created_at=template.created_at,
        last_used=template.last_used
    )


@router.delete("/templates/{template_id}")
async def delete_template(template_id: str):
    """Delete a configuration template."""
    if template_id not in MOCK_TEMPLATES:
        raise HTTPException(status_code=404, detail="Template not found")
    
    del MOCK_TEMPLATES[template_id]
    return {"message": "Template deleted successfully"}