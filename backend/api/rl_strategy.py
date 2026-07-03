"""
FormulaIQ — RL Strategy API Router
Provides endpoints to trigger training, run simulations, and query real-time strategy recommendations.
"""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field
from loguru import logger
import os

from rl_strategy.train_agent import NumPyPPOAgent, train_numpy_fallback, CHECKPOINT_PATH
from rl_strategy.simulate_agent import simulate_race, get_hybrid_recommendation
from rl_strategy.config import ACTIONS, COMPOUNDS

router = APIRouter(prefix="/rl-strategy", tags=["RL Strategy"])

# Global training status tracker
training_status = {
    "is_training": False,
    "last_checkpoint": str(CHECKPOINT_PATH) if os.path.exists(CHECKPOINT_PATH) else None
}

# ── Pydantic Schemas ──────────────────────────────────────────────────────────
class RecommendRequest(BaseModel):
    current_lap: int = Field(..., ge=1, le=100, description="Current lap number")
    total_laps: int = Field(50, ge=1, le=100, description="Total race laps")
    tyre_compound: str = Field("Medium", description="Current tyre compound (Soft, Medium, Hard)")
    tyre_age: int = Field(0, ge=0, description="Age of current tyre set in laps")
    tyre_degradation: float = Field(0.0, ge=0.0, le=100.0, description="Tyre degradation percentage (0-100 or 0.0-1.0)")
    track_temp: float = Field(35.0, description="Track temperature in Celsius")
    weather_condition: str = Field("dry", description="Weather condition (dry, rain)")
    safety_car_prob: float = Field(0.05, ge=0.0, le=1.0, description="Base probability of a safety car")
    safety_car_active: bool = Field(False, description="Is there currently a safety car/VSC active?")
    competitor_avg_tyre_age: float = Field(5.0, description="Average tyre age of direct competitors")
    competitor_pit_status: bool = Field(False, description="Are competitors pitting this lap?")
    current_position: int = Field(10, ge=1, le=20, description="Current race position")
    lap_delta_ahead: float = Field(2.0, description="Lap time delta to the car ahead in seconds")
    lap_delta_behind: float = Field(2.0, description="Lap time delta to the car behind in seconds")
    fuel_load: float = Field(50.0, description="Current fuel load in kg")
    track_type: str = Field("permanent", description="Track classification (permanent, street)")

class RecommendResponse(BaseModel):
    recommended_action: str
    action_id: int
    predicted_finish_gain_loss: float
    confidence_score: float
    explanation: str

class SimulateRequest(BaseModel):
    total_laps: int = Field(50, ge=10, le=100)
    starting_position: int = Field(10, ge=1, le=20)
    track_temp: float = Field(35.0)
    weather: str = Field("dry")
    track_type: str = Field("permanent")
    safety_car_prob: float = Field(0.05)


# ── Training Endpoint ─────────────────────────────────────────────────────────
def bg_training_task():
    global training_status
    training_status["is_training"] = True
    try:
        train_numpy_fallback()
        training_status["last_checkpoint"] = str(CHECKPOINT_PATH)
    except Exception as e:
        logger.error("RL strategy training task failed | err={}", e)
    finally:
        training_status["is_training"] = False

@router.post("/train", summary="Train RL Strategy Agent")
async def train_agent(background_tasks: BackgroundTasks):
    """Triggers background training of the PPO actor-critic strategist."""
    if training_status["is_training"]:
        return {"status": "already_training", "message": "Agent training is already in progress."}
        
    background_tasks.add_task(bg_training_task)
    return {"status": "started", "message": "PPO reinforcement learning training started in background."}

@router.get("/status", summary="Get RL Strategy Training Status")
async def get_status():
    """Returns whether the model is training and the path of the last checkpoint."""
    return {
        "is_training": training_status["is_training"],
        "checkpoint_exists": os.path.exists(CHECKPOINT_PATH),
        "last_checkpoint": training_status["last_checkpoint"]
    }


# ── Recommendation Endpoint ───────────────────────────────────────────────────
@router.post("/recommend", response_model=RecommendResponse, summary="Get Optimal Strategy Recommendation")
async def get_recommendation(payload: RecommendRequest):
    """
    Evaluates the current race state and recommends the optimal action.
    """
    try:
        # Load agent
        agent = NumPyPPOAgent()
        if os.path.exists(CHECKPOINT_PATH):
            agent.load(str(CHECKPOINT_PATH))
            
        # Map payload to environment state format
        state_dict = payload.model_dump()
        
        # Call hybrid strategy selector
        action_id, confidence, explanation = get_hybrid_recommendation(agent, state_dict)
        
        # Calculate predicted gain/loss based on positions and action
        # Pitting loses track position temporarily but gains pace later.
        # Staying out preserves position but risks degradation cliff.
        degr = payload.tyre_degradation
        if degr > 1.0:
            degr /= 100.0
            
        if action_id == 0:  # Stay out
            if degr > 0.70:
                predicted_gain = -2.5  # Lose positions due to tyre cliff
            else:
                predicted_gain = 0.5   # Gain/maintain track position
        else:  # Pitting
            if degr > 0.65:
                predicted_gain = 1.5   # Gain positions in the long run (undercut)
            else:
                predicted_gain = -1.0  # Lose net positions (pitting too early)
                
        return RecommendResponse(
            recommended_action=ACTIONS[action_id],
            action_id=action_id,
            predicted_finish_gain_loss=round(predicted_gain, 1),
            confidence_score=round(confidence, 2),
            explanation=explanation
        )
    except Exception as e:
        logger.error("RL recommendation failed | err={}", e)
        raise HTTPException(status_code=500, detail=f"Strategy recommendation failed: {str(e)}")


# ── Simulation Endpoint ───────────────────────────────────────────────────────
@router.post("/simulate", response_model=List[Dict[str, Any]], summary="Simulate Full Race Strategy")
async def run_simulation(payload: SimulateRequest):
    """
    Simulates a full race lap-by-lap using the optimal policy and outputs the history.
    """
    try:
        config = payload.model_dump()
        history = simulate_race(config)
        return history
    except Exception as e:
        logger.error("RL simulation failed | err={}", e)
        raise HTTPException(status_code=500, detail=f"Strategy simulation failed: {str(e)}")
