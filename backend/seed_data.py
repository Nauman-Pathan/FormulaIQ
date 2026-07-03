"""
FormulaIQ — Seed Script
Creates tables + inserts realistic 2024 F1 demo data.
Run: python seed_data.py
"""
import sys
from pathlib import Path
from datetime import date

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent))

from database.db import Base, sync_engine, SyncSessionLocal
from models.orm import (
    Circuit, Constructor, Driver, Race, RaceResult,
    Qualifying, LapTime, PitStop, Weather, ModelPrediction
)

# ── 2024 circuits ────────────────────────────────────────────────────────────
CIRCUITS_DATA = [
    dict(circuit_key="bahrain",     name="Bahrain International Circuit",  location="Sakhir",       country="Bahrain",     track_length_km=5.412, track_type="permanent"),
    dict(circuit_key="jeddah",      name="Jeddah Corniche Circuit",         location="Jeddah",       country="Saudi Arabia", track_length_km=6.174, track_type="street"),
    dict(circuit_key="albert_park", name="Albert Park Circuit",             location="Melbourne",    country="Australia",   track_length_km=5.278, track_type="permanent"),
    dict(circuit_key="suzuka",      name="Suzuka Circuit",                  location="Suzuka",       country="Japan",       track_length_km=5.807, track_type="permanent"),
    dict(circuit_key="shanghai",    name="Shanghai International Circuit",  location="Shanghai",     country="China",       track_length_km=5.451, track_type="permanent"),
    dict(circuit_key="miami",       name="Miami International Autodrome",   location="Miami",        country="USA",         track_length_km=5.412, track_type="street"),
    dict(circuit_key="imola",       name="Autodromo Enzo e Dino Ferrari",   location="Imola",        country="Italy",       track_length_km=4.909, track_type="permanent"),
    dict(circuit_key="monaco",      name="Circuit de Monaco",               location="Monaco",       country="Monaco",      track_length_km=3.337, track_type="street"),
    dict(circuit_key="canada",      name="Circuit Gilles Villeneuve",       location="Montreal",     country="Canada",      track_length_km=4.361, track_type="permanent"),
    dict(circuit_key="barcelona",   name="Circuit de Barcelona-Catalunya",  location="Barcelona",    country="Spain",       track_length_km=4.657, track_type="permanent"),
    dict(circuit_key="silverstone", name="Silverstone Circuit",             location="Silverstone",  country="UK",          track_length_km=5.891, track_type="permanent"),
    dict(circuit_key="hungaroring", name="Hungaroring",                     location="Budapest",     country="Hungary",     track_length_km=4.381, track_type="permanent"),
    dict(circuit_key="spa",         name="Circuit de Spa-Francorchamps",    location="Spa",          country="Belgium",     track_length_km=7.004, track_type="permanent"),
    dict(circuit_key="zandvoort",   name="Circuit Zandvoort",               location="Zandvoort",    country="Netherlands", track_length_km=4.259, track_type="permanent"),
    dict(circuit_key="monza",       name="Autodromo Nazionale Monza",       location="Monza",        country="Italy",       track_length_km=5.793, track_type="permanent"),
    dict(circuit_key="baku",        name="Baku City Circuit",               location="Baku",         country="Azerbaijan",  track_length_km=6.003, track_type="street"),
    dict(circuit_key="singapore",   name="Marina Bay Street Circuit",       location="Singapore",    country="Singapore",   track_length_km=5.063, track_type="street"),
    dict(circuit_key="austin",      name="Circuit of the Americas",         location="Austin",       country="USA",         track_length_km=5.513, track_type="permanent"),
    dict(circuit_key="mexico",      name="Autodromo Hermanos Rodriguez",    location="Mexico City",  country="Mexico",      track_length_km=4.304, track_type="permanent"),
    dict(circuit_key="brazil",      name="Autodromo Jose Carlos Pace",      location="São Paulo",    country="Brazil",      track_length_km=4.309, track_type="permanent"),
    dict(circuit_key="las_vegas",   name="Las Vegas Street Circuit",        location="Las Vegas",    country="USA",         track_length_km=6.201, track_type="street"),
    dict(circuit_key="qatar",       name="Lusail International Circuit",    location="Lusail",       country="Qatar",       track_length_km=5.419, track_type="permanent"),
    dict(circuit_key="abu_dhabi",   name="Yas Marina Circuit",              location="Abu Dhabi",    country="UAE",         track_length_km=5.281, track_type="permanent"),
]

# ── Constructors ─────────────────────────────────────────────────────────────
CONSTRUCTORS_DATA = [
    dict(constructor_key="red_bull",    name="Red Bull Racing",   nationality="Austrian",    color_hex="#3671C6"),
    dict(constructor_key="ferrari",     name="Ferrari",           nationality="Italian",     color_hex="#E8002D"),
    dict(constructor_key="mercedes",    name="Mercedes",          nationality="German",      color_hex="#27F4D2"),
    dict(constructor_key="mclaren",     name="McLaren",           nationality="British",     color_hex="#FF8000"),
    dict(constructor_key="aston",       name="Aston Martin",      nationality="British",     color_hex="#358C75"),
    dict(constructor_key="alpine",      name="Alpine",            nationality="French",      color_hex="#FF87BC"),
    dict(constructor_key="williams",    name="Williams",          nationality="British",     color_hex="#64C4FF"),
    dict(constructor_key="haas",        name="Haas F1 Team",      nationality="American",    color_hex="#B6BABD"),
    dict(constructor_key="rb",          name="RB",                nationality="Italian",     color_hex="#6692FF"),
    dict(constructor_key="sauber",      name="Kick Sauber",       nationality="Swiss",       color_hex="#52E252"),
]

# ── Drivers ───────────────────────────────────────────────────────────────────
DRIVERS_DATA = [
    dict(driver_code="VER", full_name="Max Verstappen",      driver_number=1,  constructor_key="red_bull",  nationality="Dutch",      season=2024, total_wins=54, total_podiums=99, total_poles=40),
    dict(driver_code="PER", full_name="Sergio Perez",        driver_number=11, constructor_key="red_bull",  nationality="Mexican",    season=2024),
    dict(driver_code="LEC", full_name="Charles Leclerc",     driver_number=16, constructor_key="ferrari",   nationality="Monegasque", season=2024, total_wins=7, total_podiums=34),
    dict(driver_code="SAI", full_name="Carlos Sainz",        driver_number=55, constructor_key="ferrari",   nationality="Spanish",    season=2024, total_wins=3),
    dict(driver_code="HAM", full_name="Lewis Hamilton",      driver_number=44, constructor_key="mercedes",  nationality="British",    season=2024, total_wins=103, total_podiums=197, championships=7),
    dict(driver_code="RUS", full_name="George Russell",      driver_number=63, constructor_key="mercedes",  nationality="British",    season=2024, total_wins=2),
    dict(driver_code="NOR", full_name="Lando Norris",        driver_number=4,  constructor_key="mclaren",   nationality="British",    season=2024, total_wins=4),
    dict(driver_code="PIA", full_name="Oscar Piastri",       driver_number=81, constructor_key="mclaren",   nationality="Australian", season=2024, total_wins=2),
    dict(driver_code="ALO", full_name="Fernando Alonso",     driver_number=14, constructor_key="aston",     nationality="Spanish",    season=2024, total_wins=32, championships=2),
    dict(driver_code="STR", full_name="Lance Stroll",        driver_number=18, constructor_key="aston",     nationality="Canadian",   season=2024),
    dict(driver_code="GAS", full_name="Pierre Gasly",        driver_number=10, constructor_key="alpine",    nationality="French",     season=2024),
    dict(driver_code="OCO", full_name="Esteban Ocon",        driver_number=31, constructor_key="alpine",    nationality="French",     season=2024),
    dict(driver_code="ALB", full_name="Alexander Albon",     driver_number=23, constructor_key="williams",  nationality="Thai",       season=2024),
    dict(driver_code="SAR", full_name="Logan Sargeant",      driver_number=2,  constructor_key="williams",  nationality="American",   season=2024),
    dict(driver_code="MAG", full_name="Kevin Magnussen",     driver_number=20, constructor_key="haas",      nationality="Danish",     season=2024),
    dict(driver_code="HUL", full_name="Nico Hulkenberg",     driver_number=27, constructor_key="haas",      nationality="German",     season=2024),
    dict(driver_code="TSU", full_name="Yuki Tsunoda",        driver_number=22, constructor_key="rb",        nationality="Japanese",   season=2024),
    dict(driver_code="RIC", full_name="Daniel Ricciardo",    driver_number=3,  constructor_key="rb",        nationality="Australian", season=2024, total_wins=8),
    dict(driver_code="BOT", full_name="Valtteri Bottas",     driver_number=77, constructor_key="sauber",    nationality="Finnish",    season=2024),
    dict(driver_code="ZHO", full_name="Guanyu Zhou",         driver_number=24, constructor_key="sauber",    nationality="Chinese",    season=2024),
]

# ── 2024 Race results (first 8 rounds) ───────────────────────────────────────
RACE_RESULTS_2024 = [
    # Round 1 Bahrain: VER wins
    (1, "bahrain", "VER", 1, 1, 25.0, False, "Finished"),
    (1, "bahrain", "SAI", 2, 2, 18.0, False, "Finished"),
    (1, "bahrain", "LEC", 3, 3, 15.0, False, "Finished"),
    (1, "bahrain", "PER", 5, 4, 12.0, False, "Finished"),
    (1, "bahrain", "NOR", 7, 5, 10.0, False, "Finished"),
    (1, "bahrain", "PIA", 9, 6, 8.0,  False, "Finished"),
    (1, "bahrain", "RUS", 8, 7, 6.0,  False, "Finished"),
    (1, "bahrain", "HAM", 6, 8, 4.0,  False, "Finished"),
    (1, "bahrain", "ALO", 10, 9, 2.0, False, "Finished"),
    (1, "bahrain", "GAS", 11, 10, 1.0,False, "Finished"),
    # Round 2 Saudi Arabia: SAI wins
    (2, "jeddah",  "SAI", 1, 1, 25.0, False, "Finished"),
    (2, "jeddah",  "VER", 2, 2, 18.0, False, "Finished"),
    (2, "jeddah",  "PER", 3, 3, 15.0, False, "Finished"),
    (2, "jeddah",  "LEC", 4, 4, 12.0, False, "Finished"),
    (2, "jeddah",  "NOR", 5, 5, 10.0, False, "Finished"),
    (2, "jeddah",  "HAM", 8, 6,  8.0, False, "Finished"),
    (2, "jeddah",  "PIA", 6, 7,  6.0, False, "Finished"),
    (2, "jeddah",  "RUS", 7, 8,  4.0, False, "Finished"),
    (2, "jeddah",  "ALO", 9, 9,  2.0, False, "Finished"),
    (2, "jeddah",  "HUL",10, 10, 1.0, False, "Finished"),
    # Round 3 Australia: SAI wins (VER DNF)
    (3, "albert_park", "SAI", 2, 1, 25.0, False, "Finished"),
    (3, "albert_park", "LEC", 3, 2, 18.0, False, "Finished"),
    (3, "albert_park", "NOR", 4, 3, 15.0, True,  "Finished"),
    (3, "albert_park", "PIA", 5, 4, 12.0, False, "Finished"),
    (3, "albert_park", "RUS", 6, 5, 10.0, False, "Finished"),
    (3, "albert_park", "HAM", 7, 6,  8.0, False, "Finished"),
    (3, "albert_park", "ALO", 8, 7,  6.0, False, "Finished"),
    (3, "albert_park", "VER", 1, 20, 0.0, True,  "Suspension"),
    # Round 4 Japan: VER wins
    (4, "suzuka", "VER", 1, 1, 25.0, False, "Finished"),
    (4, "suzuka", "SAI", 2, 2, 18.0, False, "Finished"),
    (4, "suzuka", "LEC", 3, 3, 15.0, False, "Finished"),
    (4, "suzuka", "PER", 4, 4, 12.0, False, "Finished"),
    (4, "suzuka", "NOR", 5, 5, 10.0, False, "Finished"),
    (4, "suzuka", "PIA", 6, 6,  8.0, False, "Finished"),
    (4, "suzuka", "RUS", 7, 7,  6.0, False, "Finished"),
    (4, "suzuka", "HAM", 8, 8,  4.0, False, "Finished"),
    (4, "suzuka", "ALO", 9, 9,  2.0, False, "Finished"),
    (4, "suzuka", "GAS",10, 10, 1.0, False, "Finished"),
    # Round 5 China: VER wins
    (5, "shanghai", "VER", 1, 1, 25.0, False, "Finished"),
    (5, "shanghai", "LEC", 3, 2, 18.0, False, "Finished"),
    (5, "shanghai", "NOR", 2, 3, 15.0, False, "Finished"),
    (5, "shanghai", "SAI", 4, 4, 12.0, False, "Finished"),
    (5, "shanghai", "PER", 5, 5, 10.0, False, "Finished"),
    (5, "shanghai", "RUS", 7, 6,  8.0, False, "Finished"),
    (5, "shanghai", "HAM", 6, 7,  6.0, False, "Finished"),
    (5, "shanghai", "PIA", 8, 8,  4.0, False, "Finished"),
    (5, "shanghai", "ALO",10, 9,  2.0, False, "Finished"),
    (5, "shanghai", "STR", 9, 10, 1.0, False, "Finished"),
    # Round 6 Miami: NOR wins
    (6, "miami", "NOR", 1, 1, 25.0, False, "Finished"),
    (6, "miami", "VER", 2, 2, 18.0, False, "Finished"),
    (6, "miami", "LEC", 4, 3, 15.0, False, "Finished"),
    (6, "miami", "PIA", 5, 4, 12.0, False, "Finished"),
    (6, "miami", "SAI", 3, 5, 10.0, False, "Finished"),
    (6, "miami", "RUS", 6, 6,  8.0, False, "Finished"),
    (6, "miami", "HAM", 8, 7,  6.0, False, "Finished"),
    (6, "miami", "ALO", 7, 8,  4.0, False, "Finished"),
    (6, "miami", "PER", 9, 9,  2.0, False, "Finished"),
    (6, "miami", "GAS",10, 10, 1.0, False, "Finished"),
    # Round 7 Imola: VER wins
    (7, "imola", "VER", 1, 1, 25.0, True, "Finished"),
    (7, "imola", "NOR", 2, 2, 18.0, False, "Finished"),
    (7, "imola", "PIA", 3, 3, 15.0, False, "Finished"),
    (7, "imola", "LEC", 5, 4, 12.0, False, "Finished"),
    (7, "imola", "SAI", 4, 5, 10.0, False, "Finished"),
    (7, "imola", "HAM", 6, 6,  8.0, False, "Finished"),
    (7, "imola", "RUS", 8, 7,  6.0, False, "Finished"),
    (7, "imola", "ALO",10, 8,  4.0, False, "Finished"),
    (7, "imola", "PER", 7, 9,  2.0, False, "Finished"),
    (7, "imola", "ALB", 9, 10, 1.0, False, "Finished"),
    # Round 8 Monaco: LEC wins
    (8, "monaco", "LEC", 1, 1, 25.0, False, "Finished"),
    (8, "monaco", "PIA", 4, 2, 18.0, False, "Finished"),
    (8, "monaco", "SAI", 2, 3, 15.0, False, "Finished"),
    (8, "monaco", "NOR", 3, 4, 12.0, False, "Finished"),
    (8, "monaco", "VER", 6, 5, 10.0, False, "Finished"),
    (8, "monaco", "RUS", 8, 6,  8.0, False, "Finished"),
    (8, "monaco", "HAM", 7, 7,  6.0, False, "Finished"),
    (8, "monaco", "ALO", 5, 8,  4.0, False, "Finished"),
    (8, "monaco", "PER", 9, 9,  2.0, False, "Finished"),
    (8, "monaco", "GAS",10, 10, 1.0, False, "Finished"),
]

GP_NAMES = {
    1: ("Bahrain Grand Prix",     "bahrain"),
    2: ("Saudi Arabian Grand Prix","jeddah"),
    3: ("Australian Grand Prix",  "albert_park"),
    4: ("Japanese Grand Prix",    "suzuka"),
    5: ("Chinese Grand Prix",     "shanghai"),
    6: ("Miami Grand Prix",       "miami"),
    7: ("Emilia Romagna Grand Prix","imola"),
    8: ("Monaco Grand Prix",      "monaco"),
}

RACE_DATES = {
    1: date(2024, 3, 2),   2: date(2024, 3, 9),
    3: date(2024, 3, 24),  4: date(2024, 4, 7),
    5: date(2024, 4, 21),  6: date(2024, 5, 5),
    7: date(2024, 5, 19),  8: date(2024, 5, 26),
}


def run():
    print("🏗️  Creating database schema...")
    Base.metadata.create_all(bind=sync_engine)
    print("✅ Schema created")

    with SyncSessionLocal() as db:
        # Circuits
        circuit_map = {}
        for c in CIRCUITS_DATA:
            existing = db.query(Circuit).filter_by(circuit_key=c["circuit_key"]).first()
            if not existing:
                obj = Circuit(**c)
                db.add(obj)
                db.flush()
                circuit_map[c["circuit_key"]] = obj
            else:
                circuit_map[c["circuit_key"]] = existing
        db.commit()
        print(f"✅ {len(CIRCUITS_DATA)} circuits seeded")

        # Constructors
        ctor_map = {}
        for c in CONSTRUCTORS_DATA:
            existing = db.query(Constructor).filter_by(constructor_key=c["constructor_key"]).first()
            if not existing:
                obj = Constructor(**c)
                db.add(obj)
                db.flush()
                ctor_map[c["constructor_key"]] = obj
            else:
                ctor_map[c["constructor_key"]] = existing
        db.commit()
        print(f"✅ {len(CONSTRUCTORS_DATA)} constructors seeded")

        # Drivers
        driver_map = {}
        for d in DRIVERS_DATA:
            ctor_key = d.pop("constructor_key")
            existing = db.query(Driver).filter_by(driver_code=d["driver_code"], season=d["season"]).first()
            if not existing:
                ctor = ctor_map.get(ctor_key)
                obj = Driver(**d, constructor_id=ctor.id if ctor else None)
                db.add(obj)
                db.flush()
                driver_map[d["driver_code"]] = obj
            else:
                driver_map[d["driver_code"]] = existing
        db.commit()
        print(f"✅ {len(DRIVERS_DATA)} drivers seeded")

        # Races + Race Results
        race_map = {}
        for rnd, (gp_name, circuit_key) in GP_NAMES.items():
            existing = db.query(Race).filter_by(season=2024, round_number=rnd).first()
            if not existing:
                circuit = circuit_map.get(circuit_key)
                race = Race(
                    season=2024,
                    round_number=rnd,
                    grand_prix_name=gp_name,
                    grand_prix_key=circuit_key,
                    circuit_id=circuit.id if circuit else None,
                    race_date=RACE_DATES[rnd],
                    session_status="completed",
                )
                db.add(race)
                db.flush()
                race_map[rnd] = race
            else:
                race_map[rnd] = existing
        db.commit()
        print(f"✅ {len(GP_NAMES)} races seeded")

        # Race Results + Qualifying (synthetic)
        result_count = 0
        for (rnd, circuit_key, drv_code, grid, finish, pts, fl, status) in RACE_RESULTS_2024:
            race = race_map.get(rnd)
            driver = driver_map.get(drv_code)
            if not race or not driver:
                continue

            existing = db.query(RaceResult).filter_by(race_id=race.id, driver_id=driver.id).first()
            if not existing:
                db.add(RaceResult(
                    race_id=race.id,
                    driver_id=driver.id,
                    constructor_id=driver.constructor_id,
                    grid_position=grid,
                    finish_position=finish,
                    classified_position=str(finish) if status == "Finished" else status[:3],
                    points_scored=pts,
                    fastest_lap=fl,
                    status=status,
                    dnf=(status != "Finished"),
                ))
                result_count += 1

            # Qualifying (synthetic — grid position used)
            existing_q = db.query(Qualifying).filter_by(race_id=race.id, driver_id=driver.id).first()
            if not existing_q:
                base_q = 88.0 + grid * 0.08
                db.add(Qualifying(
                    race_id=race.id,
                    driver_id=driver.id,
                    q3_time_seconds=base_q if grid <= 10 else None,
                    q2_time_seconds=base_q + 0.1 if grid <= 15 else None,
                    q1_time_seconds=base_q + 0.2,
                    best_qualifying_time_seconds=base_q,
                    grid_position=grid,
                ))

            # Weather (per race)
        for rnd, race in race_map.items():
            existing_w = db.query(Weather).filter_by(race_id=race.id).first()
            if not existing_w:
                db.add(Weather(
                    race_id=race.id,
                    air_temp_avg=28.0, track_temp_avg=42.0, humidity_avg=55.0,
                    wind_speed_avg=12.0, rainfall=False, condition="dry",
                ))

        db.commit()
        print(f"✅ {result_count} race results seeded")
        print()
        print("🎉 Seed complete! FormulaIQ database is ready.")


if __name__ == "__main__":
    run()
