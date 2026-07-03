"""
FormulaIQ — Pydantic Request/Response Schemas
All API input validation and output serialization models.
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


# ─────────────────────────────────────────────────────────────────────────────
# Common
# ─────────────────────────────────────────────────────────────────────────────
class PaginatedResponse(BaseModel):
    total: int
    page: int
    page_size: int
    results: List[Any]


# ─────────────────────────────────────────────────────────────────────────────
# Circuit Schemas
# ─────────────────────────────────────────────────────────────────────────────
class CircuitOut(BaseModel):
    id: int
    circuit_key: str
    name: str
    location: Optional[str]
    country: Optional[str]
    track_length_km: Optional[float]
    track_type: Optional[str]

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────────────────────────────────────
# Race Schemas
# ─────────────────────────────────────────────────────────────────────────────
class RaceOut(BaseModel):
    id: int
    season: int
    round_number: int
    grand_prix_name: str
    grand_prix_key: str
    race_date: Any
    session_status: str
    circuit: Optional[CircuitOut]

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────────────────────────────────────
# Driver Schemas
# ─────────────────────────────────────────────────────────────────────────────
class DriverOut(BaseModel):
    id: int
    driver_code: str
    full_name: str
    nationality: Optional[str]
    driver_number: Optional[int]
    season: int

    model_config = {"from_attributes": True}


class DriverStatsOut(BaseModel):
    driver_code: str
    full_name: str
    season: int
    total_wins: int
    total_podiums: int
    total_poles: int
    total_championship_points: int
    championships: int

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────────────────────────────────────
# Race Result Schemas
# ─────────────────────────────────────────────────────────────────────────────
class RaceResultOut(BaseModel):
    driver_code: str
    driver_name: str
    constructor_name: Optional[str]
    grid_position: Optional[int]
    finish_position: Optional[int]
    classified_position: Optional[str]
    points_scored: float
    fastest_lap: bool
    status: Optional[str]
    dnf: bool
    total_race_time_seconds: Optional[float]
    gap_to_leader_seconds: Optional[float]

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────────────────────────────────────
# Telemetry Schemas
# ─────────────────────────────────────────────────────────────────────────────
class TelemetryDriverData(BaseModel):
    driver_code: str
    lap_number: int
    speed_kmh: List[float]
    throttle_pct: List[float]
    brake: List[bool]
    gear: List[int]
    rpm: List[float]
    drs: List[int]
    x_pos: List[float]
    y_pos: List[float]
    session_time: List[float]
    distance: List[float]


class TelemetryComparisonOut(BaseModel):
    year: int
    grand_prix: str
    driver1: TelemetryDriverData
    driver2: TelemetryDriverData
    lap_delta: Optional[List[float]] = None  # delta time across distance
    sector_comparison: Optional[Dict[str, Any]] = None


class TelemetryQueryParams(BaseModel):
    lap_number: Optional[int] = Field(None, ge=1, le=78)


# ─────────────────────────────────────────────────────────────────────────────
# Race Prediction Schemas
# ─────────────────────────────────────────────────────────────────────────────
class DriverInputFeatures(BaseModel):
    driver_code: str = Field(..., min_length=2, max_length=4)
    driver_name: str = ""
    constructor: str = ""
    grid_position: int = Field(..., ge=1, le=20)
    best_qualifying_time_seconds: float = Field(..., gt=0)
    consistency_score: float = Field(50.0, ge=0, le=100)
    avg_lap_time: float = Field(90.0, gt=0)
    prev3_avg_finish: float = Field(10.0, ge=1, le=20)
    cumulative_points: float = Field(0.0, ge=0)
    num_pit_stops: int = Field(2, ge=0, le=5)
    avg_pit_duration: float = Field(25.0, gt=0)
    weather_code: int = Field(0, ge=0, le=2)  # 0=dry, 1=mixed, 2=wet
    rainfall: int = Field(0, ge=0, le=1)
    air_temp_avg: float = Field(25.0)
    track_temp_avg: float = Field(40.0)
    humidity_avg: float = Field(50.0)
    grid_delta: int = Field(0)
    laps_completed: float = Field(50.0, ge=0)

    @field_validator("driver_code")
    @classmethod
    def uppercase_code(cls, v: str) -> str:
        return v.upper()


class RacePredictionRequest(BaseModel):
    race_id: Optional[int] = None
    year: Optional[int] = None
    grand_prix: Optional[str] = None
    model_version: str = "v1"
    drivers: List[DriverInputFeatures] = Field(..., min_length=2, max_length=20)


class DriverPredictionResult(BaseModel):
    driver_code: str
    driver_name: str
    constructor: str
    predicted_position: float
    predicted_position_int: int
    win_probability: float
    podium_probability: float
    top10_probability: float
    dnf_probability: float


class RacePredictionResponse(BaseModel):
    race_id: Optional[int]
    year: Optional[int]
    grand_prix: Optional[str]
    model_version: str
    predictions: List[DriverPredictionResult]
    feature_importances: Optional[Dict[str, float]] = None


# ─────────────────────────────────────────────────────────────────────────────
# Strategy Simulator Schemas
# ─────────────────────────────────────────────────────────────────────────────
class StrategySimRequest(BaseModel):
    current_lap: int = Field(..., ge=1, le=78)
    total_laps: int = Field(..., ge=20, le=78)
    tyre_compound: str = Field(..., pattern="^(SOFT|MEDIUM|HARD|INTERMEDIATE|WET)$")
    tyre_age_laps: int = Field(..., ge=0, le=50)
    current_position: int = Field(..., ge=1, le=20)
    weather_condition: str = Field("dry", pattern="^(dry|mixed|wet)$")
    safety_car_probability: float = Field(0.15, ge=0.0, le=1.0)
    pit_lane_loss_seconds: float = Field(20.0, ge=15.0, le=35.0)
    degradation_rate: float = Field(0.08, ge=0.01, le=1.0)  # seconds per lap
    circuit_type: str = Field("permanent", pattern="^(permanent|street|hybrid)$")

    @field_validator("tyre_compound")
    @classmethod
    def uppercase_compound(cls, v: str) -> str:
        return v.upper()


class StrategyOption(BaseModel):
    strategy_name: str
    pit_lap: int
    compound_in: str
    compound_out: str
    projected_total_time_seconds: float
    position_gain_loss: float
    confidence: float


class StrategySimResponse(BaseModel):
    recommended_strategy: StrategyOption
    all_strategies: List[StrategyOption]
    current_tyre_degradation_pct: float
    laps_to_pit_window_open: int
    laps_to_pit_window_close: int
    notes: str


# ─────────────────────────────────────────────────────────────────────────────
# Driver Analytics Schemas
# ─────────────────────────────────────────────────────────────────────────────
class DriverAnalyticsOut(BaseModel):
    driver_code: str
    full_name: str
    season: int
    consistency_score: float
    overtaking_efficiency: float
    tyre_management_score: float
    average_pace_delta_ms: float
    qualifying_performance: float
    racecraft_score: float
    avg_grid_position: float
    avg_finish_position: float
    avg_positions_gained: float
    dnf_rate: float
    podium_rate: float
    win_rate: float
    races_analyzed: int
    recent_form: List[Dict[str, Any]]
