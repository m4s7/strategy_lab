from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
import random

router = APIRouter(prefix="/data", tags=["data"])

# Mock data availability - in production this would come from actual data index
MOCK_CONTRACTS = {
    "2024-03": {
        "start_date": "2024-01-15",
        "end_date": "2024-03-15",
        "level1_available": True,
        "level2_available": True,
        "quality_score": 98.5,
        "tick_count": 15234567,
        "file_size_mb": 1250.5,
        "volume_avg": 125000,
    },
    "2024-06": {
        "start_date": "2024-03-18",
        "end_date": "2024-06-21",
        "level1_available": True,
        "level2_available": True,
        "quality_score": 99.2,
        "tick_count": 18567890,
        "file_size_mb": 1480.2,
        "volume_avg": 145000,
    },
    "2024-09": {
        "start_date": "2024-06-17",
        "end_date": "2024-09-20",
        "level1_available": True,
        "level2_available": True,
        "quality_score": 99.1,
        "tick_count": 19234567,
        "file_size_mb": 1520.8,
        "volume_avg": 152000,
    },
    "2024-12": {
        "start_date": "2024-09-16",
        "end_date": "2024-12-20",
        "level1_available": True,
        "level2_available": True,
        "quality_score": 98.8,
        "tick_count": 17890123,
        "file_size_mb": 1390.4,
        "volume_avg": 138000,
    },
    "2025-03": {
        "start_date": "2024-12-16",
        "end_date": "2025-03-21",
        "level1_available": True,
        "level2_available": False,
        "quality_score": 97.5,
        "tick_count": 8234567,
        "file_size_mb": 680.3,
        "volume_avg": 115000,
    },
}


class DateRange(BaseModel):
    start: str
    end: str


class DataAvailability(BaseModel):
    contract: str
    start_date: str
    end_date: str
    level1_available: bool
    level2_available: bool
    quality_score: float
    tick_count: int
    file_size_mb: float
    data_gaps: List[DateRange] = []
    last_updated: str
    volume_avg: int


class DataConfiguration(BaseModel):
    date_range: DateRange
    contracts: List[str]
    data_level: str  # 'L1' or 'L2'
    include_holidays: bool = False
    time_zone: str = "America/Chicago"


class DataEstimate(BaseModel):
    estimated_duration_seconds: int
    estimated_memory_mb: int
    estimated_ticks: int
    estimated_file_size_mb: float
    warnings: List[str] = []
    recommendations: List[str] = []


class DataValidationResponse(BaseModel):
    valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    available_data: List[DataAvailability] = []


class ContractInfo(BaseModel):
    contract: str
    display_name: str
    start_date: str
    end_date: str
    is_front_month: bool
    roll_date: str
    data_quality: float
    tick_count: int
    volume_avg: int


@router.get("/availability", response_model=List[DataAvailability])
async def get_data_availability():
    """Get data availability index for all contracts."""
    availability = []

    for contract, info in MOCK_CONTRACTS.items():
        # Generate some mock data gaps
        gaps = []
        if random.random() > 0.8:  # 20% chance of having gaps
            gap_start = datetime.fromisoformat(info["start_date"]) + timedelta(
                days=random.randint(20, 60)
            )
            gap_end = gap_start + timedelta(hours=random.randint(1, 24))
            gaps.append(DateRange(start=gap_start.isoformat(), end=gap_end.isoformat()))

        availability.append(
            DataAvailability(
                contract=contract,
                start_date=info["start_date"],
                end_date=info["end_date"],
                level1_available=info["level1_available"],
                level2_available=info["level2_available"],
                quality_score=info["quality_score"],
                tick_count=info["tick_count"],
                file_size_mb=info["file_size_mb"],
                data_gaps=gaps,
                last_updated=datetime.now().isoformat(),
                volume_avg=info["volume_avg"],
            )
        )

    return availability


@router.get("/contracts", response_model=List[ContractInfo])
async def get_available_contracts():
    """Get list of available MNQ contracts with metadata."""
    contracts = []
    current_date = datetime.now()

    for i, (contract, info) in enumerate(MOCK_CONTRACTS.items()):
        end_date = datetime.fromisoformat(info["end_date"])
        is_front = (
            i == len(MOCK_CONTRACTS) - 2
        )  # Second to last is typically front month

        # Calculate roll date (typically Thursday before third Friday)
        roll_date = end_date - timedelta(days=7)

        contracts.append(
            ContractInfo(
                contract=contract,
                display_name=f"MNQ {contract}",
                start_date=info["start_date"],
                end_date=info["end_date"],
                is_front_month=is_front,
                roll_date=roll_date.isoformat()[:10],
                data_quality=info["quality_score"],
                tick_count=info["tick_count"],
                volume_avg=info["volume_avg"],
            )
        )

    return contracts


@router.post("/validate", response_model=DataValidationResponse)
async def validate_data_configuration(config: DataConfiguration):
    """Validate data configuration and check availability."""
    errors = []
    warnings = []
    available_data = []

    # Parse dates
    try:
        start_date = datetime.fromisoformat(config.date_range.start)
        end_date = datetime.fromisoformat(config.date_range.end)
    except:
        errors.append("Invalid date format. Use ISO format (YYYY-MM-DD)")
        return DataValidationResponse(valid=False, errors=errors)

    # Validate date range
    if start_date >= end_date:
        errors.append("End date must be after start date")

    if (end_date - start_date).days > 365:
        warnings.append("Date range exceeds 1 year. This may impact performance.")

    # Check contract availability
    for contract in config.contracts:
        if contract not in MOCK_CONTRACTS:
            errors.append(f"Contract {contract} not found")
            continue

        contract_info = MOCK_CONTRACTS[contract]
        contract_start = datetime.fromisoformat(contract_info["start_date"])
        contract_end = datetime.fromisoformat(contract_info["end_date"])

        # Check date overlap
        if end_date < contract_start or start_date > contract_end:
            warnings.append(f"Contract {contract} has no data in selected date range")

        # Check data level availability
        if config.data_level == "L2" and not contract_info["level2_available"]:
            errors.append(f"Level 2 data not available for contract {contract}")

        # Add to available data
        available_data.append(
            DataAvailability(
                contract=contract,
                start_date=contract_info["start_date"],
                end_date=contract_info["end_date"],
                level1_available=contract_info["level1_available"],
                level2_available=contract_info["level2_available"],
                quality_score=contract_info["quality_score"],
                tick_count=contract_info["tick_count"],
                file_size_mb=contract_info["file_size_mb"],
                data_gaps=[],
                last_updated=datetime.now().isoformat(),
                volume_avg=contract_info["volume_avg"],
            )
        )

    # Additional validations
    if len(config.contracts) == 0:
        errors.append("At least one contract must be selected")

    if len(config.contracts) > 5:
        warnings.append(
            "Selecting more than 5 contracts may significantly increase processing time"
        )

    return DataValidationResponse(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        available_data=available_data,
    )


@router.post("/estimate", response_model=DataEstimate)
async def estimate_performance(config: DataConfiguration):
    """Estimate performance metrics for data configuration."""

    # Calculate total ticks and file size
    total_ticks = 0
    total_size_mb = 0

    for contract in config.contracts:
        if contract in MOCK_CONTRACTS:
            info = MOCK_CONTRACTS[contract]
            # Estimate based on date range overlap
            contract_start = datetime.fromisoformat(info["start_date"])
            contract_end = datetime.fromisoformat(info["end_date"])
            config_start = datetime.fromisoformat(config.date_range.start)
            config_end = datetime.fromisoformat(config.date_range.end)

            # Calculate overlap
            overlap_start = max(contract_start, config_start)
            overlap_end = min(contract_end, config_end)

            if overlap_end > overlap_start:
                overlap_days = (overlap_end - overlap_start).days
                total_days = (contract_end - contract_start).days
                overlap_ratio = overlap_days / total_days if total_days > 0 else 0

                total_ticks += int(info["tick_count"] * overlap_ratio)
                total_size_mb += info["file_size_mb"] * overlap_ratio

    # Estimate processing metrics
    if config.data_level == "L2":
        # Level 2 data is more intensive
        ticks_per_second = 50000
        memory_multiplier = 2.5
    else:
        ticks_per_second = 100000
        memory_multiplier = 1.0

    estimated_duration = int(total_ticks / ticks_per_second)
    estimated_memory = int(total_size_mb * memory_multiplier)

    warnings = []
    recommendations = []

    # Generate warnings and recommendations
    if estimated_duration > 3600:
        warnings.append(
            f"Estimated processing time exceeds 1 hour ({estimated_duration // 3600}h {(estimated_duration % 3600) // 60}m)"
        )

    if estimated_memory > 8000:
        warnings.append(
            f"Estimated memory usage ({estimated_memory}MB) may require a high-memory system"
        )

    if total_ticks > 50000000:
        recommendations.append("Consider using Level 1 data for faster processing")
        recommendations.append("Consider reducing date range or number of contracts")

    if len(config.contracts) > 3:
        recommendations.append(
            "Consider processing contracts separately for better performance"
        )

    return DataEstimate(
        estimated_duration_seconds=estimated_duration,
        estimated_memory_mb=estimated_memory,
        estimated_ticks=total_ticks,
        estimated_file_size_mb=round(total_size_mb, 2),
        warnings=warnings,
        recommendations=recommendations,
    )


@router.get("/sample/{contract}")
async def get_sample_data(contract: str, data_level: str = "L1", limit: int = 100):
    """Get sample data for preview."""
    if contract not in MOCK_CONTRACTS:
        raise HTTPException(status_code=404, detail="Contract not found")

    # Generate mock sample data
    samples = []
    base_price = 15000.0

    for i in range(limit):
        timestamp = datetime.now() - timedelta(seconds=i * 0.1)
        price_change = random.uniform(-2, 2)

        if data_level == "L1":
            sample = {
                "timestamp": timestamp.isoformat(),
                "bid": base_price + price_change - 0.25,
                "ask": base_price + price_change + 0.25,
                "last": base_price + price_change,
                "volume": random.randint(1, 10),
            }
        else:
            # Level 2 includes order book
            sample = {
                "timestamp": timestamp.isoformat(),
                "bid": base_price + price_change - 0.25,
                "ask": base_price + price_change + 0.25,
                "last": base_price + price_change,
                "volume": random.randint(1, 10),
                "bid_depth": [
                    {
                        "price": base_price + price_change - 0.25 - i * 0.25,
                        "size": random.randint(5, 20),
                    }
                    for i in range(5)
                ],
                "ask_depth": [
                    {
                        "price": base_price + price_change + 0.25 + i * 0.25,
                        "size": random.randint(5, 20),
                    }
                    for i in range(5)
                ],
            }

        samples.append(sample)
        base_price += price_change

    return {
        "contract": contract,
        "data_level": data_level,
        "sample_count": len(samples),
        "samples": samples,
    }
