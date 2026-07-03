"""
FormulaIQ — Strategy Simulator Service (Module 4)
Rule-based pit strategy engine, RL-ready architecture.
"""
from typing import Any, Dict, List

import numpy as np
from loguru import logger

from models.schemas import StrategyOption, StrategySimRequest

# ── Tyre Stint Performance Model ─────────────────────────────────────────────
# Base lap time deltas relative to MEDIUM (seconds)
COMPOUND_PERFORMANCE = {
    "SOFT": -0.6,        # fastest but degrades quick
    "MEDIUM": 0.0,       # baseline
    "HARD": 0.5,         # slower but lasts longer
    "INTERMEDIATE": 3.0, # wet conditions
    "WET": 5.0,          # extreme wet
}

# Laps at which compound typically falls off cliff
COMPOUND_CLIFF_LAP = {
    "SOFT": 22,
    "MEDIUM": 38,
    "HARD": 52,
    "INTERMEDIATE": 25,
    "WET": 20,
}

# Mandatory tyre compounds for a standard race (at least 2 different dry compounds)
NEXT_COMPOUND = {
    "SOFT": ["MEDIUM", "HARD"],
    "MEDIUM": ["SOFT", "HARD"],
    "HARD": ["SOFT", "MEDIUM"],
    "INTERMEDIATE": ["SOFT", "MEDIUM"],
    "WET": ["INTERMEDIATE", "SOFT"],
}


def _degrade_lap_time(
    base_time: float,
    compound: str,
    tyre_age: int,
    degradation_rate: float,
) -> float:
    """Estimate lap time at given tyre age including cliff effect."""
    cliff = COMPOUND_CLIFF_LAP.get(compound, 35)
    perf_delta = COMPOUND_PERFORMANCE.get(compound, 0.0)

    if tyre_age >= cliff:
        # Exponential degradation past cliff
        extra = degradation_rate * (tyre_age - cliff) ** 1.5
    else:
        extra = degradation_rate * tyre_age

    return base_time + perf_delta + extra


def _simulate_stint(
    start_lap: int,
    end_lap: int,
    compound: str,
    start_tyre_age: int,
    degradation_rate: float,
    base_lap_time: float = 90.0,
) -> float:
    """Total time for a stint from start_lap to end_lap."""
    total = 0.0
    for lap_in_stint in range(end_lap - start_lap):
        age = start_tyre_age + lap_in_stint
        total += _degrade_lap_time(base_lap_time, compound, age, degradation_rate)
    return total


def _evaluate_strategy(
    request: StrategySimRequest,
    pit_lap: int,
    compound_out: str,
) -> StrategyOption:
    """Evaluate a single pit strategy."""
    current_lap = request.current_lap
    total_laps = request.total_laps
    tyre_compound = request.tyre_compound
    tyre_age = request.tyre_age_laps
    deg_rate = request.degradation_rate
    pit_loss = request.pit_lane_loss_seconds

    base_lap_time = 90.0  # assumed constant baseline

    # Stint 1: current_lap → pit_lap on current compound
    stint1_time = _simulate_stint(
        current_lap, pit_lap,
        tyre_compound, tyre_age, deg_rate, base_lap_time
    )

    # Pit stop loss
    pit_time = pit_loss

    # Safety car probability discount on pit loss
    if request.safety_car_probability > 0.3:
        pit_time *= 0.6  # SC reduces delta

    # Stint 2: pit_lap → total_laps on new compound
    stint2_time = _simulate_stint(
        pit_lap, total_laps,
        compound_out, 0, deg_rate, base_lap_time
    )

    total_time = stint1_time + pit_time + stint2_time

    # Position impact estimation (rough heuristic)
    optimal_pit = _optimal_pit_lap(request)
    deviation = abs(pit_lap - optimal_pit)
    pos_loss = min(deviation * 0.15, 3.0)  # max 3 positions lost from timing

    # Confidence based on tyre age relative to cliff
    cliff = COMPOUND_CLIFF_LAP.get(tyre_compound, 35)
    freshness = max(0, cliff - tyre_age) / cliff
    confidence = round(0.5 + freshness * 0.4, 2)

    strategy_name = f"1-stop: {tyre_compound[:3]} → {compound_out[:3]}"
    if pit_lap == current_lap:
        strategy_name = f"Box Now: → {compound_out[:3]}"

    return StrategyOption(
        strategy_name=strategy_name,
        pit_lap=pit_lap,
        compound_in=tyre_compound,
        compound_out=compound_out,
        projected_total_time_seconds=round(total_time, 2),
        position_gain_loss=round(-pos_loss, 2),
        confidence=confidence,
    )


def _optimal_pit_lap(request: StrategySimRequest) -> int:
    """Find optimal pit lap using degradation model."""
    compound = request.tyre_compound
    cliff = COMPOUND_CLIFF_LAP.get(compound, 35)
    remaining_cliff = cliff - request.tyre_age_laps
    optimal = request.current_lap + max(1, remaining_cliff - 3)
    return min(optimal, request.total_laps - 5)


def simulate_strategy(request: StrategySimRequest) -> Dict[str, Any]:
    """Main strategy simulator entry point."""
    logger.info(
        "Strategy sim | lap={}/{} compound={} age={}",
        request.current_lap, request.total_laps,
        request.tyre_compound, request.tyre_age_laps
    )

    possible_compounds = NEXT_COMPOUND.get(request.tyre_compound, ["MEDIUM"])
    optimal_lap = _optimal_pit_lap(request)
    remaining_laps = request.total_laps - request.current_lap

    # Generate pit window options: optimal ± 5 laps
    pit_laps = sorted(set([
        max(request.current_lap + 1, optimal_lap - 5),
        max(request.current_lap + 1, optimal_lap - 2),
        optimal_lap,
        min(request.total_laps - 5, optimal_lap + 3),
        min(request.total_laps - 5, optimal_lap + 6),
    ]))
    pit_laps = [p for p in pit_laps if request.current_lap < p < request.total_laps - 3]

    all_strategies: List[StrategyOption] = []
    for pit_lap in pit_laps:
        for compound_out in possible_compounds:
            strategy = _evaluate_strategy(request, pit_lap, compound_out)
            all_strategies.append(strategy)

    # Best = lowest projected time
    all_strategies.sort(key=lambda s: s.projected_total_time_seconds)
    recommended = all_strategies[0] if all_strategies else None

    # Tyre degradation percent
    cliff = COMPOUND_CLIFF_LAP.get(request.tyre_compound, 35)
    degradation_pct = round(min(request.tyre_age_laps / cliff * 100, 100), 1)

    # Pit window
    window_open = max(0, optimal_lap - request.current_lap - 3)
    window_close = max(0, optimal_lap - request.current_lap + 5)

    notes = _generate_strategy_notes(request, recommended, degradation_pct)

    return {
        "recommended_strategy": recommended,
        "all_strategies": all_strategies[:6],  # top 6
        "current_tyre_degradation_pct": degradation_pct,
        "laps_to_pit_window_open": window_open,
        "laps_to_pit_window_close": window_close,
        "notes": notes,
    }


def _generate_strategy_notes(request: StrategySimRequest, best, deg_pct: float) -> str:
    """Generate human-readable strategy insight."""
    notes = []

    if deg_pct > 80:
        notes.append(f"⚠️ {request.tyre_compound} tyres critically worn ({deg_pct:.0f}%). Box immediately.")
    elif deg_pct > 60:
        notes.append(f"🔶 Tyres at {deg_pct:.0f}% degradation — pit window opening.")

    if request.safety_car_probability > 0.4:
        notes.append("🚗 High SC probability — consider boxing early to convert Safety Car.")

    if request.weather_condition == "wet":
        notes.append("🌧️ Wet conditions — monitor for dry line before switching to slicks.")
    elif request.weather_condition == "mixed":
        notes.append("🌦️ Mixed conditions — stay on intermediates until track dries completely.")

    if best and best.pit_lap <= request.current_lap + 2:
        notes.append(f"✅ Recommended: Box this lap onto {best.compound_out}.")

    return " | ".join(notes) if notes else "✅ Strategy nominal. Continue current stint."
