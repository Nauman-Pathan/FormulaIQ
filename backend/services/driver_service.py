"""
FormulaIQ — Driver Analytics Service (Module 5)
Computes advanced driver performance metrics from historical DB data.
"""
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from loguru import logger
from sqlalchemy import text
from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).parent.parent))

from models.orm import Driver, LapTime, PitStop, Qualifying, Race, RaceResult


def compute_driver_analytics(
    db: Session,
    driver_code: str,
    season: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Compute comprehensive driver analytics metrics.
    """
    driver_code = driver_code.upper()

    # ── Find driver ────────────────────────────────────────────────────────
    driver_query = db.query(Driver).filter(Driver.driver_code == driver_code)
    if season:
        driver_query = driver_query.filter(Driver.season == season)
    driver_query = driver_query.order_by(Driver.season.desc())
    driver = driver_query.first()

    if not driver:
        raise ValueError(f"Driver {driver_code} not found")

    seasons_clause = f"AND r.season = {season}" if season else "AND r.season >= 2022"

    # ── Race Results ───────────────────────────────────────────────────────
    rr_sql = text(f"""
        SELECT rr.grid_position, rr.finish_position, rr.points_scored,
               rr.dnf, rr.fastest_lap, r.season, r.round_number,
               r.grand_prix_name, c.name as constructor_name
        FROM race_results rr
        JOIN races r ON r.id = rr.race_id
        JOIN drivers d ON d.id = rr.driver_id
        LEFT JOIN constructors c ON c.id = rr.constructor_id
        WHERE d.driver_code = :code {seasons_clause}
        ORDER BY r.season, r.round_number
    """)
    rr_rows = db.execute(rr_sql, {"code": driver_code}).fetchall()

    if not rr_rows:
        raise ValueError(f"No race data found for driver {driver_code}")

    rr_df = pd.DataFrame(rr_rows, columns=[
        "grid_position", "finish_position", "points_scored", "dnf",
        "fastest_lap", "season", "round_number", "grand_prix_name", "constructor_name"
    ])

    # ── Qualifying ─────────────────────────────────────────────────────────
    q_sql = text(f"""
        SELECT q.best_qualifying_time_seconds, q.grid_position,
               r.round_number, r.season
        FROM qualifying q
        JOIN races r ON r.id = q.race_id
        JOIN drivers d ON d.id = q.driver_id
        WHERE d.driver_code = :code {seasons_clause}
    """)
    q_rows = db.execute(q_sql, {"code": driver_code}).fetchall()
    q_df = pd.DataFrame(q_rows, columns=["best_q_time", "q_position", "round_number", "season"])

    # ── Lap Times ──────────────────────────────────────────────────────────
    lt_sql = text(f"""
        SELECT lt.lap_time_seconds, lt.sector1_seconds, lt.sector2_seconds,
               lt.sector3_seconds, lt.compound, lt.tyre_life, r.round_number
        FROM lap_times lt
        JOIN races r ON r.id = lt.race_id
        JOIN drivers d ON d.id = lt.driver_id
        WHERE d.driver_code = :code
        AND lt.lap_time_seconds BETWEEN 60 AND 130
        {seasons_clause}
    """)
    lt_rows = db.execute(lt_sql, {"code": driver_code}).fetchall()
    lt_df = pd.DataFrame(lt_rows, columns=[
        "lap_time", "s1", "s2", "s3", "compound", "tyre_life", "round_number"
    ])

    # ─────────────────────────────────────────────────────────────────────
    # Metric Calculations
    # ─────────────────────────────────────────────────────────────────────
    total_races = len(rr_df)
    wins = int((rr_df["finish_position"] == 1).sum())
    podiums = int((rr_df["finish_position"] <= 3).sum())
    dnfs = int(rr_df["dnf"].sum())

    avg_grid = float(rr_df["grid_position"].mean())
    avg_finish = float(rr_df["finish_position"].mean())
    avg_positions_gained = float((rr_df["grid_position"] - rr_df["finish_position"]).mean())

    # Consistency score: 100 - (std_dev of finish position / max_range * 100)
    finish_std = float(rr_df["finish_position"].std())
    consistency_score = round(max(0.0, 100.0 - (finish_std / 20.0 * 100)), 2)

    # Overtaking efficiency: avg positions gained per race (normalized)
    overtaking_eff = round(min(100.0, max(0.0, (avg_positions_gained + 10) / 20 * 100)), 2)

    # Tyre management: how well pace holds in last 10 laps of stint
    tyre_mgmt_score = 50.0
    if not lt_df.empty:
        # Compare early stint (laps 1-10) vs late stint (laps 20+) pace delta
        early_pace = lt_df[lt_df["tyre_life"] <= 10]["lap_time"].mean()
        late_pace = lt_df[lt_df["tyre_life"] >= 20]["lap_time"].mean()
        if early_pace and late_pace:
            degradation = (late_pace - early_pace) / early_pace * 100
            tyre_mgmt_score = round(max(0.0, 100.0 - degradation * 10), 2)

    # Average pace delta (ms vs field median)
    avg_pace_delta = 0.0
    if not lt_df.empty:
        driver_avg = lt_df["lap_time"].mean()
        avg_pace_delta = round((driver_avg - 90.0) * 1000, 1)  # ms delta vs 90s baseline

    # Qualifying performance: avg Q position normalized
    q_perf = 50.0
    if not q_df.empty:
        avg_q_pos = q_df["q_position"].mean()
        q_perf = round(max(0.0, (20.0 - avg_q_pos) / 19.0 * 100), 2)

    # Racecraft score: composite
    racecraft_score = round(
        (consistency_score * 0.3 + overtaking_eff * 0.3 +
         tyre_mgmt_score * 0.2 + q_perf * 0.2), 2
    )

    # Recent form: last 5 races
    recent_form = rr_df.tail(5)[
        ["season", "round_number", "grand_prix_name", "grid_position",
         "finish_position", "points_scored", "dnf"]
    ].to_dict(orient="records")

    return {
        "driver_code": driver_code,
        "full_name": driver.full_name,
        "season": season or int(rr_df["season"].max()),
        "consistency_score": consistency_score,
        "overtaking_efficiency": overtaking_eff,
        "tyre_management_score": tyre_mgmt_score,
        "average_pace_delta_ms": avg_pace_delta,
        "qualifying_performance": q_perf,
        "racecraft_score": racecraft_score,
        "avg_grid_position": round(avg_grid, 2),
        "avg_finish_position": round(avg_finish, 2),
        "avg_positions_gained": round(avg_positions_gained, 2),
        "dnf_rate": round(dnfs / total_races, 4),
        "podium_rate": round(podiums / total_races, 4),
        "win_rate": round(wins / total_races, 4),
        "races_analyzed": total_races,
        "recent_form": recent_form,
    }
