"""
FormulaIQ — Telemetry Service (Module 2)
Fetches FastF1 telemetry live or from DB for two-driver comparison.
"""
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import fastf1
import numpy as np
import pandas as pd
from loguru import logger

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings

CACHE_DIR = Path(settings.FASTF1_CACHE_DIR)
CACHE_DIR.mkdir(parents=True, exist_ok=True)
fastf1.Cache.enable_cache(str(CACHE_DIR))


def _get_fastest_or_nth_lap(
    session: fastf1.core.Session,
    driver_code: str,
    lap_number: Optional[int] = None,
):
    """Return the target lap object for a driver."""
    driver_laps = session.laps.pick_driver(driver_code)
    if driver_laps.empty:
        raise ValueError(f"Driver {driver_code} not found in session")

    if lap_number is not None:
        laps = driver_laps[driver_laps["LapNumber"] == lap_number]
        if laps.empty:
            raise ValueError(f"Lap {lap_number} not found for driver {driver_code}")
        return laps.iloc[0]

    # Default: fastest lap
    return driver_laps.pick_fastest()


def _extract_telemetry(lap) -> Dict[str, Any]:
    """Convert a FastF1 lap's telemetry into JSON-serializable dict."""
    tel = lap.get_telemetry()
    if tel is None or tel.empty:
        return {}

    return {
        "speed_kmh": tel["Speed"].fillna(0).tolist(),
        "throttle_pct": tel["Throttle"].fillna(0).tolist(),
        "brake": tel["Brake"].fillna(False).tolist(),
        "gear": tel["nGear"].fillna(0).astype(int).tolist(),
        "rpm": tel["RPM"].fillna(0).tolist(),
        "drs": tel["DRS"].fillna(0).astype(int).tolist(),
        "x_pos": tel["X"].fillna(0).tolist(),
        "y_pos": tel["Y"].fillna(0).tolist(),
        "session_time": [t.total_seconds() for t in tel["SessionTime"]],
        "distance": tel["Distance"].fillna(0).tolist(),
    }


def _compute_lap_delta(tel1: Dict, tel2: Dict) -> List[float]:
    """
    Compute cumulative lap delta time between two drivers over distance.
    Positive = driver2 is ahead (faster), negative = driver1 is ahead.
    """
    dist1 = np.array(tel1.get("distance", []))
    time1 = np.array(tel1.get("session_time", []))
    dist2 = np.array(tel2.get("distance", []))
    time2 = np.array(tel2.get("session_time", []))

    if len(dist1) == 0 or len(dist2) == 0:
        return []

    # Interpolate time2 at dist1 points
    common_dist = np.linspace(max(dist1.min(), dist2.min()), min(dist1.max(), dist2.max()), 200)
    interp_time1 = np.interp(common_dist, dist1, time1)
    interp_time2 = np.interp(common_dist, dist2, time2)

    delta = (interp_time2 - interp_time1).tolist()
    return [round(d, 4) for d in delta]


def _compute_sector_comparison(lap1, lap2, driver1: str, driver2: str) -> Dict[str, Any]:
    """Compare sector times between two drivers."""
    def safe_seconds(td) -> Optional[float]:
        try:
            return round(td.total_seconds(), 3)
        except Exception:
            return None

    sectors = {}
    for s in ["Sector1Time", "Sector2Time", "Sector3Time"]:
        s1 = safe_seconds(getattr(lap1, s, None))
        s2 = safe_seconds(getattr(lap2, s, None))
        if s1 and s2:
            sectors[s] = {
                driver1: s1,
                driver2: s2,
                "delta": round(s2 - s1, 3),
                "fastest": driver1 if s1 <= s2 else driver2,
            }
    return sectors


def get_telemetry_comparison(
    year: int,
    grand_prix: str,
    driver1: str,
    driver2: str,
    lap_number: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Main telemetry comparison function.
    Fetches FastF1 race session and extracts telemetry for two drivers.
    """
    logger.info(
        "Telemetry comparison | year={} gp={} d1={} d2={} lap={}",
        year, grand_prix, driver1, driver2, lap_number
    )

    try:
        session = fastf1.get_session(year, grand_prix, "R")
        session.load(laps=True, telemetry=True, weather=False, messages=False)
    except Exception as exc:
        raise ValueError(f"Could not load session {year} {grand_prix}: {exc}")

    d1 = driver1.upper()
    d2 = driver2.upper()

    lap1 = _get_fastest_or_nth_lap(session, d1, lap_number)
    lap2 = _get_fastest_or_nth_lap(session, d2, lap_number)

    tel1 = _extract_telemetry(lap1)
    tel2 = _extract_telemetry(lap2)

    lap_delta = _compute_lap_delta(tel1, tel2)
    sector_comparison = _compute_sector_comparison(lap1, lap2, d1, d2)

    def lap_time_seconds(lap) -> Optional[float]:
        try:
            return round(lap["LapTime"].total_seconds(), 3)
        except Exception:
            return None

    return {
        "year": year,
        "grand_prix": grand_prix,
        "lap_number": int(lap1["LapNumber"]) if lap_number is None else lap_number,
        "driver1": {
            "driver_code": d1,
            "lap_number": int(lap1["LapNumber"]),
            "lap_time_seconds": lap_time_seconds(lap1),
            "compound": str(lap1.get("Compound", "UNKNOWN")),
            **tel1,
        },
        "driver2": {
            "driver_code": d2,
            "lap_number": int(lap2["LapNumber"]),
            "lap_time_seconds": lap_time_seconds(lap2),
            "compound": str(lap2.get("Compound", "UNKNOWN")),
            **tel2,
        },
        "lap_delta": lap_delta,
        "sector_comparison": sector_comparison,
    }
