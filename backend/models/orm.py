"""
FormulaIQ — SQLAlchemy ORM Models
Full database schema for the F1 analytics platform.
Tables: circuits, constructors, drivers, races, qualifying,
        race_results, lap_times, pit_stops, telemetry,
        weather, model_predictions
"""
from datetime import date, datetime, time
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from database.db import Base


# ─────────────────────────────────────────────────────────────────────────────
# Helper mixin: timestamps
# ─────────────────────────────────────────────────────────────────────────────
class TimestampMixin:
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Circuit
# ─────────────────────────────────────────────────────────────────────────────
class Circuit(TimestampMixin, Base):
    __tablename__ = "circuits"

    id = Column(Integer, primary_key=True, index=True)
    circuit_key = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(150), nullable=False)
    location = Column(String(100))
    country = Column(String(100))
    latitude = Column(Float)
    longitude = Column(Float)
    altitude_m = Column(Integer)
    track_length_km = Column(Float)
    lap_record_seconds = Column(Float)
    lap_record_driver = Column(String(100))
    lap_record_year = Column(SmallInteger)
    track_type = Column(String(50))  # street, permanent, hybrid
    characteristics = Column(JSONB)  # {"high_speed": true, "overtaking_difficulty": "medium"}

    # Relationships
    races = relationship("Race", back_populates="circuit")


# ─────────────────────────────────────────────────────────────────────────────
# Constructor (Team)
# ─────────────────────────────────────────────────────────────────────────────
class Constructor(TimestampMixin, Base):
    __tablename__ = "constructors"

    id = Column(Integer, primary_key=True, index=True)
    constructor_key = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    nationality = Column(String(50))
    base = Column(String(100))
    team_principal = Column(String(100))
    power_unit = Column(String(100))
    color_hex = Column(String(7))  # Team color for charts

    # Relationships
    drivers = relationship("Driver", back_populates="constructor")
    race_results = relationship("RaceResult", back_populates="constructor")


# ─────────────────────────────────────────────────────────────────────────────
# Driver
# ─────────────────────────────────────────────────────────────────────────────
class Driver(TimestampMixin, Base):
    __tablename__ = "drivers"

    id = Column(Integer, primary_key=True, index=True)
    driver_number = Column(SmallInteger, nullable=False)
    driver_code = Column(String(3), nullable=False, index=True)  # e.g. VER, HAM
    full_name = Column(String(100), nullable=False)
    nationality = Column(String(50))
    date_of_birth = Column(Date)
    constructor_id = Column(Integer, ForeignKey("constructors.id"), nullable=True)
    season = Column(SmallInteger, nullable=False)

    # Career stats (aggregated)
    total_wins = Column(Integer, default=0)
    total_podiums = Column(Integer, default=0)
    total_poles = Column(Integer, default=0)
    total_championship_points = Column(Integer, default=0)
    championships = Column(SmallInteger, default=0)

    __table_args__ = (
        UniqueConstraint("driver_code", "season", name="uq_driver_season"),
    )

    # Relationships
    constructor = relationship("Constructor", back_populates="drivers")
    race_results = relationship("RaceResult", back_populates="driver")
    qualifying_results = relationship("Qualifying", back_populates="driver")
    lap_times = relationship("LapTime", back_populates="driver")
    pit_stops = relationship("PitStop", back_populates="driver")


# ─────────────────────────────────────────────────────────────────────────────
# Race (Event)
# ─────────────────────────────────────────────────────────────────────────────
class Race(TimestampMixin, Base):
    __tablename__ = "races"

    id = Column(Integer, primary_key=True, index=True)
    season = Column(SmallInteger, nullable=False, index=True)
    round_number = Column(SmallInteger, nullable=False)
    grand_prix_name = Column(String(150), nullable=False)
    grand_prix_key = Column(String(100), nullable=False, index=True)
    circuit_id = Column(Integer, ForeignKey("circuits.id"), nullable=True)
    race_date = Column(Date, nullable=False)
    qualifying_date = Column(Date)
    sprint_date = Column(Date)
    total_laps = Column(SmallInteger)
    session_status = Column(String(20), default="scheduled")  # scheduled|completed|cancelled
    event_format = Column(String(20), default="conventional")  # conventional|sprint

    __table_args__ = (
        UniqueConstraint("season", "round_number", name="uq_race_season_round"),
    )

    # Relationships
    circuit = relationship("Circuit", back_populates="races")
    race_results = relationship("RaceResult", back_populates="race", cascade="all, delete-orphan")
    qualifying_results = relationship("Qualifying", back_populates="race", cascade="all, delete-orphan")
    lap_times = relationship("LapTime", back_populates="race", cascade="all, delete-orphan")
    pit_stops = relationship("PitStop", back_populates="race", cascade="all, delete-orphan")
    weather = relationship("Weather", back_populates="race", uselist=False, cascade="all, delete-orphan")
    telemetry = relationship("Telemetry", back_populates="race", cascade="all, delete-orphan")
    predictions = relationship("ModelPrediction", back_populates="race", cascade="all, delete-orphan")


# ─────────────────────────────────────────────────────────────────────────────
# Race Results
# ─────────────────────────────────────────────────────────────────────────────
class RaceResult(TimestampMixin, Base):
    __tablename__ = "race_results"

    id = Column(Integer, primary_key=True, index=True)
    race_id = Column(Integer, ForeignKey("races.id"), nullable=False, index=True)
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=False, index=True)
    constructor_id = Column(Integer, ForeignKey("constructors.id"), nullable=True)

    grid_position = Column(SmallInteger)
    finish_position = Column(SmallInteger)
    classified_position = Column(String(5))  # "1", "2", ... "DNF", "DSQ"
    points_scored = Column(Float, default=0.0)
    laps_completed = Column(SmallInteger)
    total_race_time_seconds = Column(Float)
    gap_to_leader_seconds = Column(Float)
    fastest_lap = Column(Boolean, default=False)
    fastest_lap_time_seconds = Column(Float)
    status = Column(String(50))  # "Finished", "+1 Lap", "Engine", etc.
    dnf = Column(Boolean, default=False)

    # Relationships
    race = relationship("Race", back_populates="race_results")
    driver = relationship("Driver", back_populates="race_results")
    constructor = relationship("Constructor", back_populates="race_results")


# ─────────────────────────────────────────────────────────────────────────────
# Qualifying
# ─────────────────────────────────────────────────────────────────────────────
class Qualifying(TimestampMixin, Base):
    __tablename__ = "qualifying"

    id = Column(Integer, primary_key=True, index=True)
    race_id = Column(Integer, ForeignKey("races.id"), nullable=False, index=True)
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=False, index=True)

    q1_time_seconds = Column(Float)
    q2_time_seconds = Column(Float)
    q3_time_seconds = Column(Float)
    best_qualifying_time_seconds = Column(Float)
    grid_position = Column(SmallInteger)
    q1_compound = Column(String(20))
    q2_compound = Column(String(20))
    q3_compound = Column(String(20))

    __table_args__ = (
        UniqueConstraint("race_id", "driver_id", name="uq_quali_race_driver"),
    )

    # Relationships
    race = relationship("Race", back_populates="qualifying_results")
    driver = relationship("Driver", back_populates="qualifying_results")


# ─────────────────────────────────────────────────────────────────────────────
# Lap Times
# ─────────────────────────────────────────────────────────────────────────────
class LapTime(TimestampMixin, Base):
    __tablename__ = "lap_times"

    id = Column(BigInteger, primary_key=True, index=True)
    race_id = Column(Integer, ForeignKey("races.id"), nullable=False, index=True)
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=False, index=True)

    lap_number = Column(SmallInteger, nullable=False)
    lap_time_seconds = Column(Float)
    sector1_seconds = Column(Float)
    sector2_seconds = Column(Float)
    sector3_seconds = Column(Float)
    compound = Column(String(20))
    tyre_life = Column(SmallInteger)
    is_pit_out_lap = Column(Boolean, default=False)
    is_pit_in_lap = Column(Boolean, default=False)
    is_personal_best = Column(Boolean, default=False)
    track_status = Column(String(10))  # "1"=clear, "2"=yellow, "4"=SC, "5"=red
    position = Column(SmallInteger)

    __table_args__ = (
        UniqueConstraint("race_id", "driver_id", "lap_number", name="uq_lap_race_driver_lap"),
    )

    # Relationships
    race = relationship("Race", back_populates="lap_times")
    driver = relationship("Driver", back_populates="lap_times")


# ─────────────────────────────────────────────────────────────────────────────
# Pit Stops
# ─────────────────────────────────────────────────────────────────────────────
class PitStop(TimestampMixin, Base):
    __tablename__ = "pit_stops"

    id = Column(Integer, primary_key=True, index=True)
    race_id = Column(Integer, ForeignKey("races.id"), nullable=False, index=True)
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=False, index=True)

    stop_number = Column(SmallInteger)
    lap_number = Column(SmallInteger)
    pit_duration_seconds = Column(Float)
    compound_in = Column(String(20))
    compound_out = Column(String(20))
    stationary_time_seconds = Column(Float)

    # Relationships
    race = relationship("Race", back_populates="pit_stops")
    driver = relationship("Driver", back_populates="pit_stops")


# ─────────────────────────────────────────────────────────────────────────────
# Weather
# ─────────────────────────────────────────────────────────────────────────────
class Weather(TimestampMixin, Base):
    __tablename__ = "weather"

    id = Column(Integer, primary_key=True, index=True)
    race_id = Column(Integer, ForeignKey("races.id"), nullable=False, unique=True, index=True)

    air_temp_avg = Column(Float)
    air_temp_min = Column(Float)
    air_temp_max = Column(Float)
    track_temp_avg = Column(Float)
    track_temp_max = Column(Float)
    humidity_avg = Column(Float)
    wind_speed_avg = Column(Float)
    wind_direction_avg = Column(Float)
    rainfall = Column(Boolean, default=False)
    pressure_avg = Column(Float)
    condition = Column(String(30))  # dry, wet, mixed

    # Relationships
    race = relationship("Race", back_populates="weather")


# ─────────────────────────────────────────────────────────────────────────────
# Telemetry (high-frequency car data, stored as JSONB arrays)
# ─────────────────────────────────────────────────────────────────────────────
class Telemetry(TimestampMixin, Base):
    __tablename__ = "telemetry"

    id = Column(BigInteger, primary_key=True, index=True)
    race_id = Column(Integer, ForeignKey("races.id"), nullable=False, index=True)
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=False, index=True)
    lap_number = Column(SmallInteger, nullable=False)

    # Stored as compressed JSON arrays (one value per telemetry sample)
    speed_kmh = Column(JSONB)          # [298, 302, 305, ...]
    throttle_pct = Column(JSONB)       # [0, 50, 100, ...]
    brake = Column(JSONB)              # [True, False, ...]
    gear = Column(JSONB)               # [7, 8, 8, ...]
    rpm = Column(JSONB)                # [12000, 12500, ...]
    drs = Column(JSONB)                # [0, 12, 14, ...]
    x_pos = Column(JSONB)              # track x coordinates
    y_pos = Column(JSONB)              # track y coordinates
    session_time = Column(JSONB)       # timestamps in seconds
    distance = Column(JSONB)           # distance from lap start (m)

    __table_args__ = (
        UniqueConstraint("race_id", "driver_id", "lap_number", name="uq_telemetry_race_driver_lap"),
    )

    # Relationships
    race = relationship("Race", back_populates="telemetry")


# ─────────────────────────────────────────────────────────────────────────────
# Model Predictions
# ─────────────────────────────────────────────────────────────────────────────
class ModelPrediction(TimestampMixin, Base):
    __tablename__ = "model_predictions"

    id = Column(Integer, primary_key=True, index=True)
    race_id = Column(Integer, ForeignKey("races.id"), nullable=False, index=True)
    model_version = Column(String(20), nullable=False)
    predicted_at = Column(DateTime(timezone=True), server_default=func.now())

    # Per-driver predictions stored as JSONB
    predictions = Column(JSONB)  # [{driver_code, win_prob, podium_prob, top10_prob, dnf_prob, predicted_position}]
    feature_importances = Column(JSONB)
    accuracy_score = Column(Float)  # Post-race accuracy if available
    mae_positions = Column(Float)   # Mean absolute error in positions

    # Relationships
    race = relationship("Race", back_populates="predictions")
