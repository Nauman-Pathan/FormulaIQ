"""
FormulaIQ — State Encoder
Encodes raw race states into NumPy observation vectors for Gym env and models.
"""
import numpy as np
from rl_strategy.config import COMPOUND_KEYS

def encode_state(state_dict: dict) -> np.ndarray:
    """
    Encodes raw race state dict into a 15-dimensional observation array.
    
    Expected keys:
      - current_lap: int
      - total_laps: int
      - tyre_compound: str/int ("Soft", "Medium", "Hard" or 1, 2, 3)
      - tyre_age: int
      - tyre_degradation: float (0.0 to 1.0 or 0 to 100)
      - track_temp: float
      - weather_condition: str/int ("dry", "rain" or 0, 1)
      - safety_car_prob: float (0.0 to 1.0)
      - competitor_avg_tyre_age: float
      - competitor_pit_status: int/bool
      - current_position: int (1 to 20)
      - lap_delta_ahead: float
      - lap_delta_behind: float
      - fuel_load: float
      - track_type: str/int ("permanent", "street" or 0, 1)
    """
    # 1. current_lap
    current_lap = float(state_dict.get("current_lap", 1))
    
    # 2. total_laps
    total_laps = float(state_dict.get("total_laps", 50))
    
    # 3. tyre_compound
    comp_raw = state_dict.get("tyre_compound", "Medium")
    if isinstance(comp_raw, str):
        tyre_compound = float(COMPOUND_KEYS.get(comp_raw, 2))
    else:
        tyre_compound = float(comp_raw)
        
    # 4. tyre_age
    tyre_age = float(state_dict.get("tyre_age", 0))
    
    # 5. tyre_degradation
    degr = float(state_dict.get("tyre_degradation", 0.0))
    # Normalize if given as percentage 0-100
    if degr > 1.0:
        degr = degr / 100.0
    tyre_degradation = np.clip(degr, 0.0, 1.0)
    
    # 6. track_temp
    track_temp = float(state_dict.get("track_temp", 35.0))
    
    # 7. weather_condition
    weather_raw = state_dict.get("weather_condition", "dry")
    if isinstance(weather_raw, str):
        weather_condition = 1.0 if weather_raw.lower() in ["rain", "wet"] else 0.0
    else:
        weather_condition = float(weather_raw)
        
    # 8. safety_car_prob
    safety_car_prob = float(state_dict.get("safety_car_prob", 0.05))
    
    # 9. competitor_avg_tyre_age
    competitor_avg_tyre_age = float(state_dict.get("competitor_avg_tyre_age", 5.0))
    
    # 10. competitor_pit_status
    comp_pit = state_dict.get("competitor_pit_status", 0)
    competitor_pit_status = 1.0 if comp_pit else 0.0
    
    # 11. current_position
    current_position = float(state_dict.get("current_position", 10))
    
    # 12. lap_delta_ahead
    lap_delta_ahead = float(state_dict.get("lap_delta_ahead", 2.0))
    
    # 13. lap_delta_behind
    lap_delta_behind = float(state_dict.get("lap_delta_behind", 2.0))
    
    # 14. fuel_load
    fuel_load = float(state_dict.get("fuel_load", 100.0))
    
    # 15. track_type
    tt_raw = state_dict.get("track_type", "permanent")
    if isinstance(tt_raw, str):
        track_type = 1.0 if tt_raw.lower() == "street" else 0.0
    else:
        track_type = float(tt_raw)
        
    return np.array([
        current_lap,
        total_laps,
        tyre_compound,
        tyre_age,
        tyre_degradation,
        track_temp,
        weather_condition,
        safety_car_prob,
        competitor_avg_tyre_age,
        competitor_pit_status,
        current_position,
        lap_delta_ahead,
        lap_delta_behind,
        fuel_load,
        track_type
    ], dtype=np.float32)
