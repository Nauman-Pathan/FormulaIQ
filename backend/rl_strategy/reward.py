"""
FormulaIQ — Reward System
Calculates step-by-step and terminal rewards for the Gymnasium strategy environment.
"""

def compute_step_reward(
    action: int,
    prev_state: dict,
    next_state: dict,
    pit_occurred: bool,
    was_safety_car: bool
) -> float:
    """
    Computes intermediate step reward based on action taken, tyre wear, and position changes.
    """
    reward = 0.0
    
    # Extract variables
    prev_degr = prev_state.get("tyre_degradation", 0.0)
    next_degr = next_state.get("tyre_degradation", 0.0)
    prev_pos = prev_state.get("current_position", 10)
    next_pos = next_state.get("current_position", 10)
    tyre_age = prev_state.get("tyre_age", 0)
    
    # 1. Position gain/loss reward
    pos_change = prev_pos - next_pos  # positive if position gained (e.g. 10 -> 8 is +2)
    reward += pos_change * 8.0
    
    # 2. Tyre degradation cliff penalty
    # If we stayed out on heavily degraded tyres
    if action == 0 and next_degr > 0.8:
        # Heavily penalize hit to the cliff
        cliff_severity = (next_degr - 0.8) / 0.2  # 0.0 to 1.0
        reward -= 25.0 * cliff_severity
        
    # 3. Pit stop efficiency and timing
    if pit_occurred:
        # Pit stop penalty (general overhead)
        # But if it's under Safety Car, the time loss is halved, so less penalty
        if was_safety_car:
            reward += 10.0  # Reward for capitalizing on Safety Car pit stop
        else:
            reward -= 5.0  # Normal pit lane entry cost
            
        # Pitting too early penalty (unnecessary pit stop)
        if tyre_age < 8:
            reward -= 20.0
        elif prev_degr < 0.3:
            reward -= 15.0
            
        # Pitting at sweet spot reward (degradation between 50% and 80%)
        if 0.5 <= prev_degr <= 0.8:
            reward += 15.0
            
    # 4. Extreme degradation penalty (prevent driving on bald tyres)
    if next_degr > 0.95:
        reward -= 50.0
        
    # 5. Small baseline reward for efficient running
    if action == 0 and next_degr < 0.5:
        reward += 1.0  # Encourage staying out when tyres are healthy
        
    return reward

def compute_terminal_reward(final_position: int, starting_position: int) -> float:
    """
    Computes final reward at the end of the race based on finish position and gains.
    """
    reward = 0.0
    
    # 1. Finishing Position reward (higher is better)
    # P1 gets 200, P2 gets 150, P3 gets 120, etc.
    if final_position == 1:
        reward += 200.0  # Win bonus
    elif final_position <= 3:
        reward += 100.0  # Podium bonus
    elif final_position <= 10:
        reward += 50.0   # Points finish bonus
        
    # Positional score: 21 - position (so P1 gets 20, P20 gets 1)
    pos_score = max(0, 21 - final_position)
    reward += pos_score * 10.0
    
    # 2. Positions gained over the race
    net_gained = starting_position - final_position
    reward += net_gained * 15.0
    
    return reward
