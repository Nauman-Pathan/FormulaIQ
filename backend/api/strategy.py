"""
FormulaIQ — Strategy Simulator API Router (Module 4)
POST /simulate-strategy
"""
from fastapi import APIRouter, HTTPException
from loguru import logger

from models.schemas import StrategySimRequest, StrategySimResponse
from services.strategy_service import simulate_strategy

router = APIRouter(prefix="/simulate-strategy", tags=["Strategy"])


@router.post(
    "",
    response_model=StrategySimResponse,
    summary="Simulate pit stop strategy",
    description=(
        "Rule-based strategy simulator. Given current race state (lap, tyre, weather), "
        "returns optimal pit lap, compound recommendation, and projected position impact."
    ),
)
async def simulate_pit_strategy(request: StrategySimRequest):
    """Run pit strategy simulation."""
    try:
        result = simulate_strategy(request)
        return result
    except Exception as exc:
        logger.error("Strategy simulation error | {}", exc)
        raise HTTPException(status_code=500, detail=f"Strategy simulation failed: {exc}")
