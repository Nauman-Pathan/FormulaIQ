"""
FormulaIQ — F1 Strategy Gymnasium Environment
Simulates a full F1 race and enables RL agents to learn optimal pit strategy.
"""
import random
from typing import Tuple, Dict, Any, Optional

import numpy as np
import gymnasium as gym
from gymnasium import spaces

from rl_strategy.config import (
    ACTIONS, COMPOUNDS, TYRE_DEGRADATION_RATES,
    TYRE_BASE_PACING, TYRE_DEGR_PENALTY_COEFF,
    PIT_LANE_LOSS_SECONDS, TYRE_WARMUP_PENALTY_SECONDS
)
from rl_strategy.state_encoder import encode_state
from rl_strategy.reward import compute_step_reward, compute_terminal_reward

class F1StrategyEnv(gym.Env):
    """
    Gymnasium environment simulating F1 race strategy decisions.
    """
    metadata = {"render_modes": ["human"]}

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.config = config or {}
        
        # Action Space: 0=Stay Out, 1=Soft, 2=Medium, 3=Hard
        self.action_space = spaces.Discrete(4)
        
        # Observation Space: 15 continuous features
        # [current_lap, total_laps, tyre_compound, tyre_age, tyre_degradation,
        #  track_temp, weather, safety_car_prob, competitor_avg_tyre_age, competitor_pit_status,
        #  current_position, lap_delta_ahead, lap_delta_behind, fuel_load, track_type]
        lows = np.array([
            0, 0, 0, 0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0,
            1.0, 0.0, 0.0, 0.0, 0.0
        ], dtype=np.float32)
        
        highs = np.array([
            100, 100, 4, 100, 1.0,
            60.0, 1.0, 1.0, 100.0, 1.0,
            20.0, 60.0, 60.0, 110.0, 1.0
        ], dtype=np.float32)
        
        self.observation_space = spaces.Box(low=lows, high=highs, dtype=np.float32)
        
        # Initialize state variables
        self.state = {}
        self.reset()

    def reset(
        self,
        *,
        seed: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        super().reset(seed=seed)
        
        # Initialize race parameters
        total_laps = int(self.config.get("total_laps", random.choice([44, 53, 58, 70])))
        starting_position = int(self.config.get("starting_position", random.randint(1, 20)))
        track_temp = float(self.config.get("track_temp", random.uniform(25.0, 45.0)))
        weather = 1.0 if self.config.get("weather", "dry") == "rain" else 0.0
        track_type = 1.0 if self.config.get("track_type", "permanent") == "street" else 0.0
        safety_car_base_prob = float(self.config.get("safety_car_prob", 0.05))
        
        # Setup initial state dictionary
        self.state = {
            "current_lap": 1,
            "total_laps": total_laps,
            "tyre_compound": 2,  # Start on Mediums by default
            "tyre_age": 0,
            "tyre_degradation": 0.0,
            "track_temp": track_temp,
            "weather_condition": weather,
            "safety_car_prob": safety_car_base_prob,
            "safety_car_active": 0.0,
            "competitor_avg_tyre_age": 0.0,
            "competitor_pit_status": 0.0,
            "current_position": starting_position,
            "lap_delta_ahead": 2.0,
            "lap_delta_behind": 2.0,
            "fuel_load": 100.0,  # 100kg starting fuel
            "track_type": track_type,
            "starting_position": starting_position
        }
        
        # Track outlap state
        self.just_pitted = False
        
        return self._get_obs(), {}

    def _get_obs(self) -> np.ndarray:
        return encode_state(self.state)

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        """
        Step through one lap of the race simulation.
        """
        prev_state = self.state.copy()
        
        # 1. Check if safety car triggers
        safety_car_active = random.random() < self.state["safety_car_prob"]
        self.state["safety_car_active"] = 1.0 if safety_car_active else 0.0
        
        # 2. Process Action (Pit Stop or Stay Out)
        pit_occurred = False
        outlap_penalty = 0.0
        
        if action > 0:  # Action: Pit for Soft (1), Medium (2), or Hard (3)
            self.state["tyre_compound"] = action
            self.state["tyre_age"] = 0
            self.state["tyre_degradation"] = 0.0
            pit_occurred = True
            self.just_pitted = True
            
            # Position loss from pit stop
            # Under safety car, position loss is much less
            if safety_car_active:
                pit_loss = PIT_LANE_LOSS_SECONDS * 0.55
                pos_lost = max(1, int(pit_loss / 3.0))
            else:
                pit_loss = PIT_LANE_LOSS_SECONDS
                pos_lost = max(2, int(pit_loss / 2.0))
                
            self.state["current_position"] = min(20.0, self.state["current_position"] + pos_lost)
            self.state["lap_delta_ahead"] = 1.0 + random.uniform(1.0, 5.0)
            self.state["lap_delta_behind"] = 1.0 + random.uniform(1.0, 3.0)
        else:
            # Stay out, increment age
            self.state["tyre_age"] += 1
            if self.just_pitted:
                outlap_penalty = TYRE_WARMUP_PENALTY_SECONDS
                self.just_pitted = False

        # 3. Simulate Tyre Degradation
        current_comp = self.state["tyre_compound"]
        base_degr_rate = TYRE_DEGRADATION_RATES.get(current_comp, 0.03)
        
        # Weather / temp modification to wear
        temp_mod = 1.0 + max(0, (self.state["track_temp"] - 35.0) * 0.01)
        weather_mod = 1.8 if self.state["weather_condition"] > 0 else 1.0  # Rain shreds slicks
        
        # Increment degradation
        wear = base_degr_rate * temp_mod * weather_mod
        self.state["tyre_degradation"] = min(1.0, self.state["tyre_degradation"] + wear)
        
        # 4. Calculate Lap Time
        base_pace = TYRE_BASE_PACING.get(current_comp, 80.8)
        # Fuel weight effect (0.03s benefit per kg fuel burned)
        fuel_effect = - (self.state["fuel_load"] * 0.03)
        # Degradation penalty
        degr_pct = self.state["tyre_degradation"]
        degr_effect = (degr_pct ** 2) * TYRE_DEGR_PENALTY_COEFF
        
        # Safety car speed reduction
        sc_effect = 40.0 if safety_car_active else 0.0
        
        # Total Lap Time
        our_lap_time = base_pace + fuel_effect + degr_effect + outlap_penalty + sc_effect + random.normalvariate(0.0, 0.15)
        
        # 5. Fuel consumption
        self.state["fuel_load"] = max(0.0, self.state["fuel_load"] - 1.6) # Burn 1.6kg per lap
        
        # 6. Competitor simulation (simple pace modeling)
        competitor_degr = min(1.0, self.state["competitor_avg_tyre_age"] * 0.03)
        comp_pace = 80.8 - (self.state["fuel_load"] * 0.03) + (competitor_degr ** 2) * TYRE_DEGR_PENALTY_COEFF + sc_effect
        
        # Competitor pit strategy
        competitor_pitted = False
        if self.state["competitor_avg_tyre_age"] > 18 or competitor_degr > 0.6:
            if random.random() < 0.3:
                self.state["competitor_avg_tyre_age"] = 0.0
                competitor_pitted = True
        else:
            self.state["competitor_avg_tyre_age"] += 1.0
            
        self.state["competitor_pit_status"] = 1.0 if competitor_pitted else 0.0
        
        # 7. Position update based on pace comparisons
        if not pit_occurred:
            pace_diff = our_lap_time - comp_pace
            if pace_diff < -0.6 and self.state["current_position"] > 1:
                # Overtake!
                if random.random() < 0.4:
                    self.state["current_position"] = max(1.0, self.state["current_position"] - 1)
            elif pace_diff > 1.2 and self.state["current_position"] < 20:
                # Get overtaken
                if random.random() < 0.4:
                    self.state["current_position"] = min(20.0, self.state["current_position"] + 1)
                    
        # 8. Increment Lap
        self.state["current_lap"] += 1
        
        # Check termination / truncation
        terminated = self.state["current_lap"] >= self.state["total_laps"]
        truncated = False
        
        # 9. Compute Rewards
        reward = compute_step_reward(action, prev_state, self.state, pit_occurred, safety_car_active)
        
        if terminated:
            reward += compute_terminal_reward(int(self.state["current_position"]), int(self.state["starting_position"]))
            
        return self._get_obs(), reward, terminated, truncated, {}
