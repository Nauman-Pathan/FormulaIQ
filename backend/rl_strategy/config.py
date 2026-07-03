"""
FormulaIQ — RL Strategy Configuration
Defines constants, compound mappings, simulation parameters, and training config.
"""

# Tyre Compound Constants
COMPOUNDS = {
    0: "None", # Default/No tyre (e.g. before start)
    1: "Soft",
    2: "Medium",
    3: "Hard"
}

COMPOUND_KEYS = {v: k for k, v in COMPOUNDS.items()}

# Action Mappings
ACTIONS = {
    0: "Stay Out",
    1: "Pit for Soft",
    2: "Pit for Medium",
    3: "Pit for Hard"
}

# Simulation Coefficients
TYRE_DEGRADATION_RATES = {
    1: 0.05,  # Soft: degrades by ~5% per lap
    2: 0.03,  # Medium: degrades by ~3% per lap
    3: 0.018  # Hard: degrades by ~1.8% per lap
}

# Base pace (seconds per lap on a fresh tyre)
TYRE_BASE_PACING = {
    1: 80.0,  # Soft: fastest base pace
    2: 80.8,  # Medium: mid base pace
    3: 81.6   # Hard: slowest base pace
}

# Degradation penalty coefficient: time penalty = degradation_percent^2 * coefficient
TYRE_DEGR_PENALTY_COEFF = 4.5  # Up to 4.5s penalty when fully degraded

# Pit stop overhead (seconds)
PIT_LANE_LOSS_SECONDS = 22.0
TYRE_WARMUP_PENALTY_SECONDS = 1.5  # Outlap is slower by 1.5s

# Training Configurations
TRAIN_EPISODES = 1000
LEARNING_RATE = 3e-4
GAMMA = 0.99
GAE_LAMBDA = 0.95
PPO_CLIP = 0.2
PPO_EPOCHS = 10
BATCH_SIZE = 64
