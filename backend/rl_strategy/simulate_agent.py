"""
FormulaIQ — F1 Strategy Agent Simulator
Runs full race simulations using a hybrid RL Policy + Rule-based fallback constraint system.
"""
import sys
import os
import random
from pathlib import Path
from typing import List, Dict, Any, Tuple
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from rl_strategy.env import F1StrategyEnv
from rl_strategy.train_agent import NumPyPPOAgent, CHECKPOINT_PATH
from rl_strategy.config import ACTIONS, COMPOUNDS
from rl_strategy.state_encoder import encode_state

def get_hybrid_recommendation(agent: NumPyPPOAgent, state_dict: dict) -> Tuple[int, float, str]:
    """
    Combines RL policy logits with rule-based constraints (fallback)
    to produce extremely realistic, professional race strategy actions.
    """
    # 1. Get raw probabilities from RL agent
    obs = encode_state(state_dict)
    raw_probs, _ = agent.forward(obs)
    
    # 2. Extract state variables
    lap = int(state_dict.get("current_lap", 1))
    total_laps = int(state_dict.get("total_laps", 50))
    tyre_age = int(state_dict.get("tyre_age", 0))
    degr = float(state_dict.get("tyre_degradation", 0.0))
    if degr > 1.0:
        degr /= 100.0
    weather_raw = state_dict.get("weather_condition", 0)
    if isinstance(weather_raw, str):
        weather = 1.0 if weather_raw.lower() in ["rain", "wet"] else 0.0
    else:
        weather = float(weather_raw)
    
    remaining_laps = total_laps - lap
    
    # 3. Rule-based filters (fallbacks/constraints)
    probs = raw_probs.copy()
    explanation = "RL policy suggests staying out to conserve track position."
    
    # Rule A: Never pit in the first 8 laps of a stint or in the final 3 laps of a race
    if tyre_age < 8 or remaining_laps <= 3:
        probs = np.array([1.0, 0.0, 0.0, 0.0])
        explanation = f"Staying out. Stint age ({tyre_age} laps) is too fresh or too close to race finish ({remaining_laps} laps left)."
        action = 0
        confidence = 0.95
        return action, confidence, explanation
        
    # Rule D: Don't pit if tyres are still in good condition (degradation < 45%) unless wet weather or safety car
    is_safety_car = state_dict.get("safety_car_active", 0.0) > 0.5
    if degr < 0.45 and weather <= 0.5 and not is_safety_car:
        probs = np.array([1.0, 0.0, 0.0, 0.0])
        explanation = f"Staying out. Tyres are in good condition with only {degr * 100.0:.1f}% degradation."
        action = 0
        confidence = 0.95
        return action, confidence, explanation
        
    # Rule B: Extreme tyre wear / cliff (must pit)
    if degr >= 0.75:
        probs[0] = 0.0  # Cannot stay out
        explanation = f"Tyres are heavily degraded ({degr * 100.0:.1f}%). Must pit immediately to avoid a pace cliff."
        
    # Rule C: Rain / Wet track
    if weather > 0.5:
        probs[0] = 0.0  # Must pit for fresh compounds
        explanation = "Wet conditions detected. Pitting to adjust race strategy."
        
    # Re-normalize if we modified probs
    if np.sum(probs) > 0:
        probs = probs / np.sum(probs)
    else:
        probs = np.array([0.0, 0.33, 0.34, 0.33])  # Fallback pit
        
    # 4. Choose final action
    action = int(np.argmax(probs))
    confidence = float(probs[action])
    
    # Custom strategy explanations for pit stop recommendations
    if action > 0:
        target_compound = COMPOUNDS[action]
        if degr >= 0.75:
            explanation = f"Tyre degradation is critical ({degr * 100.0:.1f}%). Pitting for fresh {target_compound}s."
        elif remaining_laps < 15 and action == 1:
            explanation = f"Pitting for {target_compound}s to utilize high pace for the final sprint of {remaining_laps} laps."
        elif action == 2:
            explanation = f"Pitting for {target_compound}s for a balanced pace and durability profile to run for another {remaining_laps} laps."
        else:
            explanation = f"Pitting for {target_compound}s for maximum durability to finish the remaining {remaining_laps} laps."
            
    return action, confidence, explanation

def simulate_race(config: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """
    Simulates a full race using the hybrid RL-fallback strategy agent.
    """
    env = F1StrategyEnv(config)
    agent = NumPyPPOAgent()
    
    if os.path.exists(CHECKPOINT_PATH):
        logger.info("Loading trained checkpoint from: {}", CHECKPOINT_PATH)
        agent.load(str(CHECKPOINT_PATH))
    else:
        logger.warning("No checkpoint found. Using default policy.")
        
    state, _ = env.reset()
    done = False
    
    history = []
    
    while not done:
        # Get hybrid action recommendation
        action, confidence, explanation = get_hybrid_recommendation(agent, env.state)
        
        # Save pre-step state
        lap = env.state["current_lap"]
        compound = env.state["tyre_compound"]
        tyre_age = env.state["tyre_age"]
        degradation = env.state["tyre_degradation"]
        position = env.state["current_position"]
        fuel = env.state["fuel_load"]
        
        # Take step in the Gym env
        next_state, reward, terminated, truncated, _ = env.step(action)
        done = terminated or truncated
        
        history.append({
            "lap": lap,
            "action": action,
            "action_name": ACTIONS[action],
            "tyre_compound": COMPOUNDS[compound],
            "tyre_age": tyre_age,
            "tyre_degradation": float(degradation * 100.0), # Convert to %
            "position": int(position),
            "fuel_load": float(fuel),
            "reward": float(reward),
            "confidence": float(confidence),
            "explanation": explanation
        })
        
        state = next_state
        
    # Append final state details
    history.append({
        "lap": env.state["current_lap"],
        "action": 0,
        "action_name": "Finish",
        "tyre_compound": COMPOUNDS[env.state["tyre_compound"]],
        "tyre_age": env.state["tyre_age"],
        "tyre_degradation": float(env.state["tyre_degradation"] * 100.0),
        "position": int(env.state["current_position"]),
        "fuel_load": float(env.state["fuel_load"]),
        "reward": 0.0,
        "confidence": 1.0,
        "explanation": "Race finished."
    })
    
    logger.success("Simulation complete! Finished position: P{}", env.state["current_position"])
    return history

if __name__ == "__main__":
    test_config = {
        "total_laps": 50,
        "starting_position": 10,
        "track_temp": 33.5,
        "weather": "dry",
        "track_type": "permanent"
    }
    logger.info("Running hybrid test F1 strategy simulation...")
    results = simulate_race(test_config)
    for r in results:
        if r['action'] > 0 or r['lap'] % 10 == 0:
            print(f"Lap {r['lap']}: Position P{r['position']} | Action: {r['action_name']} | Tyre Wear: {r['tyre_degradation']:.1f}% | Explanation: {r['explanation']}")
