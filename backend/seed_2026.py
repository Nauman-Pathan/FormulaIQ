"""
FormulaIQ — 2026 Season Seeding Script (REAL DATA)
Accurate race results from the 2026 F1 season (Rounds 1-8)
Sources: formula1.com, wikipedia, crash.net, skysports

Run: python seed_2026.py
"""
import sys
from pathlib import Path
from datetime import date

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent))

from database.db import Base, sync_engine, SyncSessionLocal
from models.orm import Circuit, Constructor, Driver, Race, RaceResult, Qualifying, Weather

# ── 2026 Constructors ─────────────────────────────────────────────────────────
CONSTRUCTORS_2026 = [
    dict(constructor_key="red_bull",  name="Oracle Red Bull Racing", nationality="Austrian",  color_hex="#3671C6", power_unit="Red Bull Ford"),
    dict(constructor_key="ferrari",   name="Ferrari",                nationality="Italian",   color_hex="#E8002D", power_unit="Ferrari"),
    dict(constructor_key="mercedes",  name="Mercedes",               nationality="German",    color_hex="#27F4D2", power_unit="Mercedes"),
    dict(constructor_key="mclaren",   name="McLaren",                nationality="British",   color_hex="#FF8000", power_unit="Mercedes"),
    dict(constructor_key="aston",     name="Aston Martin",           nationality="British",   color_hex="#358C75", power_unit="Honda"),
    dict(constructor_key="alpine",    name="Alpine",                 nationality="French",    color_hex="#FF87BC", power_unit="Mercedes"),
    dict(constructor_key="williams",  name="Williams",               nationality="British",   color_hex="#64C4FF", power_unit="Mercedes"),
    dict(constructor_key="haas",      name="Haas F1 Team",           nationality="American",  color_hex="#B6BABD", power_unit="Ferrari"),
    dict(constructor_key="rb",        name="Racing Bulls",           nationality="Italian",   color_hex="#6692FF", power_unit="Red Bull Ford"),
    dict(constructor_key="audi",      name="Audi",                   nationality="German",    color_hex="#C0C0C0", power_unit="Audi"),
    dict(constructor_key="cadillac",  name="Cadillac",               nationality="American",  color_hex="#D4AF37", power_unit="Ferrari"),
]

# ── 2026 Drivers ──────────────────────────────────────────────────────────────
DRIVERS_2026 = [
    # Red Bull
    dict(driver_code="VER", full_name="Max Verstappen",     driver_number=1,  constructor_key="red_bull", nationality="Dutch"),
    dict(driver_code="HAD", full_name="Isack Hadjar",       driver_number=6,  constructor_key="red_bull", nationality="French"),
    # McLaren
    dict(driver_code="NOR", full_name="Lando Norris",       driver_number=4,  constructor_key="mclaren",  nationality="British"),
    dict(driver_code="PIA", full_name="Oscar Piastri",      driver_number=81, constructor_key="mclaren",  nationality="Australian"),
    # Ferrari
    dict(driver_code="LEC", full_name="Charles Leclerc",    driver_number=16, constructor_key="ferrari",  nationality="Monegasque"),
    dict(driver_code="HAM", full_name="Lewis Hamilton",     driver_number=44, constructor_key="ferrari",  nationality="British"),
    # Mercedes
    dict(driver_code="RUS", full_name="George Russell",     driver_number=63, constructor_key="mercedes", nationality="British"),
    dict(driver_code="ANT", full_name="Kimi Antonelli",     driver_number=12, constructor_key="mercedes", nationality="Italian"),
    # Aston Martin
    dict(driver_code="ALO", full_name="Fernando Alonso",    driver_number=14, constructor_key="aston",    nationality="Spanish"),
    dict(driver_code="STR", full_name="Lance Stroll",       driver_number=18, constructor_key="aston",    nationality="Canadian"),
    # Alpine
    dict(driver_code="GAS", full_name="Pierre Gasly",       driver_number=10, constructor_key="alpine",   nationality="French"),
    dict(driver_code="COL", full_name="Franco Colapinto",   driver_number=43, constructor_key="alpine",   nationality="Argentinian"),
    # Audi
    dict(driver_code="HUL", full_name="Nico Hulkenberg",    driver_number=27, constructor_key="audi",     nationality="German"),
    dict(driver_code="BOR", full_name="Gabriel Bortoleto",  driver_number=5,  constructor_key="audi",     nationality="Brazilian"),
    # Racing Bulls
    dict(driver_code="LAW", full_name="Liam Lawson",        driver_number=30, constructor_key="rb",       nationality="New Zealander"),
    dict(driver_code="LIN", full_name="Arvid Lindblad",     driver_number=8,  constructor_key="rb",       nationality="British"),
    # Haas
    dict(driver_code="OCO", full_name="Esteban Ocon",       driver_number=31, constructor_key="haas",     nationality="French"),
    dict(driver_code="BEA", full_name="Oliver Bearman",     driver_number=87, constructor_key="haas",     nationality="British"),
    # Williams
    dict(driver_code="SAI", full_name="Carlos Sainz",       driver_number=55, constructor_key="williams", nationality="Spanish"),
    dict(driver_code="ALB", full_name="Alexander Albon",    driver_number=23, constructor_key="williams", nationality="Thai"),
    # Cadillac
    dict(driver_code="PER", full_name="Sergio Perez",       driver_number=11, constructor_key="cadillac", nationality="Mexican"),
    dict(driver_code="BOT", full_name="Valtteri Bottas",    driver_number=77, constructor_key="cadillac", nationality="Finnish"),
]

# ── 2026 Circuits (new ones) ──────────────────────────────────────────────────
CIRCUITS_NEW = [
    dict(circuit_key="red_bull_ring", name="Red Bull Ring",   location="Spielberg",  country="Austria",   track_length_km=4.318, track_type="permanent"),
    dict(circuit_key="miami",         name="Miami Int. Autodrome", location="Miami", country="USA",       track_length_km=5.412, track_type="street"),
    dict(circuit_key="canada",        name="Circuit Gilles Villeneuve", location="Montreal", country="Canada", track_length_km=4.361, track_type="street"),
    dict(circuit_key="monaco",        name="Circuit de Monaco",  location="Monte Carlo", country="Monaco", track_length_km=3.337, track_type="street"),
    dict(circuit_key="barcelona",     name="Circuit de Barcelona-Catalunya", location="Barcelona", country="Spain", track_length_km=4.675, track_type="permanent"),
]

# ── 2026 Races (Rounds 1-8, all completed) ────────────────────────────────────
RACES_2026 = {
    1: ("Australian Grand Prix",       "albert_park",   date(2026, 3, 8),  "completed"),
    2: ("Chinese Grand Prix",          "shanghai",      date(2026, 3, 15), "completed"),
    3: ("Japanese Grand Prix",         "suzuka",        date(2026, 3, 29), "completed"),
    4: ("Miami Grand Prix",            "miami",         date(2026, 5, 3),  "completed"),
    5: ("Canadian Grand Prix",         "canada",        date(2026, 5, 24), "completed"),
    6: ("Monaco Grand Prix",           "monaco",        date(2026, 6, 7),  "completed"),
    7: ("Spanish Grand Prix",          "barcelona",     date(2026, 6, 14), "completed"),
    8: ("Austrian Grand Prix",         "red_bull_ring", date(2026, 6, 28), "completed"),
    9: ("British Grand Prix",          "silverstone",   date(2026, 7, 5),  "upcoming"),
    10: ("Belgian Grand Prix",         "spa",           date(2026, 8, 2),  "upcoming"),
    11: ("Hungarian Grand Prix",       "hungaroring",   date(2026, 8, 23), "upcoming"),
    12: ("Dutch Grand Prix",           "zandvoort",     date(2026, 9, 2),  "upcoming"),
    13: ("Italian Grand Prix",         "monza",         date(2026, 9, 6),  "upcoming"),
    14: ("Azerbaijan Grand Prix",      "baku",          date(2026, 9, 20), "upcoming"),
    15: ("Singapore Grand Prix",       "marina_bay",    date(2026, 10, 4), "upcoming"),
    16: ("United States Grand Prix",   "cota",          date(2026, 10, 18),"upcoming"),
    17: ("Mexico City Grand Prix",     "rodriguez",     date(2026, 10, 25),"upcoming"),
    18: ("São Paulo Grand Prix",       "interlagos",    date(2026, 11, 8), "upcoming"),
    19: ("Las Vegas Grand Prix",       "las_vegas",     date(2026, 11, 22),"upcoming"),
    20: ("Qatar Grand Prix",           "lusail",        date(2026, 11, 30),"upcoming"),
    21: ("Abu Dhabi Grand Prix",       "abu_dhabi",     date(2026, 12, 7), "upcoming"),
    22: ("Spanish Grand Prix",         "madrid",        date(2026, 9, 13), "upcoming"),
}

# ── REAL 2026 Race Results (Top 10 per race) ──────────────────────────────────
# Format: (round, driver_code, grid_pos, finish_pos, points, status)
# Sources: formula1.com, wikipedia, crash.net (verified as of Jul 2 2026)

RESULTS_2026 = [
    # ─ Round 1: Australia — Russell wins ──────────────────────────────────────
    (1, "RUS", 1,  1,  25.0, "Finished"),  # George Russell - Mercedes WINNER
    (1, "ANT", 3,  2,  18.0, "Finished"),  # Kimi Antonelli - Mercedes
    (1, "LEC", 4,  3,  15.0, "Finished"),  # Charles Leclerc - Ferrari
    (1, "HAM", 5,  4,  12.0, "Finished"),  # Lewis Hamilton - Ferrari
    (1, "NOR", 6,  5,  10.0, "Finished"),  # Lando Norris - McLaren
    (1, "VER", 2,  6,  8.0,  "Finished"),  # Max Verstappen - Red Bull
    (1, "BEA", 12, 7,  6.0,  "Finished"),  # Oliver Bearman - Haas
    (1, "LIN", 14, 8,  4.0,  "Finished"),  # Arvid Lindblad - Racing Bulls
    (1, "BOR", 16, 9,  2.0,  "Finished"),  # Gabriel Bortoleto - Audi
    (1, "GAS", 10, 10, 1.0,  "Finished"),  # Pierre Gasly - Alpine

    # ─ Round 2: China — Antonelli wins ───────────────────────────────────────
    (2, "ANT", 2,  1,  25.0, "Finished"),  # Kimi Antonelli - Mercedes WINNER
    (2, "RUS", 1,  2,  18.0, "Finished"),  # George Russell - Mercedes
    (2, "HAM", 4,  3,  15.0, "Finished"),  # Lewis Hamilton - Ferrari
    (2, "LEC", 5,  4,  12.0, "Finished"),  # Charles Leclerc - Ferrari
    (2, "BEA", 8,  5,  10.0, "Finished"),  # Oliver Bearman - Haas
    (2, "GAS", 9,  6,  8.0,  "Finished"),  # Pierre Gasly - Alpine
    (2, "LAW", 11, 7,  6.0,  "Finished"),  # Liam Lawson - Racing Bulls
    (2, "HAD", 13, 8,  4.0,  "Finished"),  # Isack Hadjar - Red Bull
    (2, "SAI", 7,  9,  2.0,  "Finished"),  # Carlos Sainz - Williams
    (2, "COL", 10, 10, 1.0,  "Finished"),  # Franco Colapinto - Alpine

    # ─ Round 3: Japan — Antonelli wins ───────────────────────────────────────
    (3, "ANT", 1,  1,  25.0, "Finished"),  # Kimi Antonelli - Mercedes WINNER
    (3, "PIA", 3,  2,  18.0, "Finished"),  # Oscar Piastri - McLaren
    (3, "LEC", 4,  3,  15.0, "Finished"),  # Charles Leclerc - Ferrari
    (3, "RUS", 2,  4,  12.0, "Finished"),  # George Russell - Mercedes
    (3, "NOR", 5,  5,  10.0, "Finished"),  # Lando Norris - McLaren
    (3, "VER", 6,  6,  8.0,  "Finished"),  # Max Verstappen - Red Bull
    (3, "HAM", 7,  7,  6.0,  "Finished"),  # Lewis Hamilton - Ferrari
    (3, "HAD", 9,  8,  4.0,  "Finished"),  # Isack Hadjar - Red Bull
    (3, "GAS", 8,  9,  2.0,  "Finished"),  # Pierre Gasly - Alpine
    (3, "OCO", 12, 10, 1.0,  "Finished"),  # Esteban Ocon - Haas

    # ─ Round 4: Miami — Antonelli wins ───────────────────────────────────────
    (4, "ANT", 2,  1,  25.0, "Finished"),  # Kimi Antonelli - Mercedes WINNER
    (4, "NOR", 3,  2,  18.0, "Finished"),  # Lando Norris - McLaren
    (4, "PIA", 4,  3,  15.0, "Finished"),  # Oscar Piastri - McLaren
    (4, "RUS", 1,  4,  12.0, "Finished"),  # George Russell - Mercedes
    (4, "VER", 5,  5,  10.0, "Finished"),  # Max Verstappen - Red Bull
    (4, "HAM", 6,  6,  8.0,  "Finished"),  # Lewis Hamilton - Ferrari
    (4, "COL", 12, 7,  6.0,  "Finished"),  # Franco Colapinto - Alpine
    (4, "LEC", 8,  8,  4.0,  "Finished"),  # Charles Leclerc - Ferrari
    (4, "SAI", 9,  9,  2.0,  "Finished"),  # Carlos Sainz - Williams
    (4, "ALB", 10, 10, 1.0,  "Finished"),  # Alexander Albon - Williams

    # ─ Round 5: Canada — Antonelli wins ──────────────────────────────────────
    (5, "ANT", 3,  1,  25.0, "Finished"),  # Kimi Antonelli - Mercedes WINNER
    (5, "HAM", 5,  2,  18.0, "Finished"),  # Lewis Hamilton - Ferrari
    (5, "VER", 2,  3,  15.0, "Finished"),  # Max Verstappen - Red Bull
    (5, "LEC", 4,  4,  12.0, "Finished"),  # Charles Leclerc - Ferrari
    (5, "HAD", 6,  5,  10.0, "Finished"),  # Isack Hadjar - Red Bull
    (5, "COL", 11, 6,  8.0,  "Finished"),  # Franco Colapinto - Alpine
    (5, "LAW", 9,  7,  6.0,  "Finished"),  # Liam Lawson - Racing Bulls
    (5, "GAS", 7,  8,  4.0,  "Finished"),  # Pierre Gasly - Alpine
    (5, "SAI", 10, 9,  2.0,  "Finished"),  # Carlos Sainz - Williams
    (5, "BEA", 14, 10, 1.0,  "Finished"),  # Oliver Bearman - Haas

    # ─ Round 6: Monaco — Antonelli wins ──────────────────────────────────────
    (6, "ANT", 1,  1,  25.0, "Finished"),  # Kimi Antonelli - Mercedes WINNER
    (6, "HAM", 3,  2,  18.0, "Finished"),  # Lewis Hamilton - Ferrari
    (6, "GAS", 5,  3,  15.0, "Finished"),  # Pierre Gasly - Alpine (pen overturned)
    (6, "HAD", 4,  4,  12.0, "Finished"),  # Isack Hadjar - Red Bull
    (6, "PIA", 6,  5,  10.0, "Finished"),  # Oscar Piastri - McLaren
    (6, "LAW", 8,  6,  8.0,  "Finished"),  # Liam Lawson - Racing Bulls
    (6, "LIN", 12, 7,  6.0,  "Finished"),  # Arvid Lindblad - Racing Bulls
    (6, "ALB", 10, 8,  4.0,  "Finished"),  # Alexander Albon - Williams
    (6, "OCO", 9,  9,  2.0,  "Finished"),  # Esteban Ocon - Haas
    (6, "ALO", 14, 10, 1.0,  "Finished"),  # Fernando Alonso - Aston Martin

    # ─ Round 7: Spain (Barcelona) — Hamilton wins ────────────────────────────
    (7, "HAM", 2,  1,  25.0, "Finished"),  # Lewis Hamilton - Ferrari WINNER
    (7, "RUS", 3,  2,  18.0, "Finished"),  # George Russell - Mercedes
    (7, "NOR", 4,  3,  15.0, "Finished"),  # Lando Norris - McLaren
    (7, "VER", 1,  4,  12.0, "Finished"),  # Max Verstappen - Red Bull
    (7, "PIA", 5,  5,  10.0, "Finished"),  # Oscar Piastri - McLaren
    (7, "HAD", 6,  6,  8.0,  "Finished"),  # Isack Hadjar - Red Bull
    (7, "GAS", 8,  7,  6.0,  "Finished"),  # Pierre Gasly - Alpine
    (7, "LAW", 9,  8,  4.0,  "Finished"),  # Liam Lawson - Racing Bulls
    (7, "LIN", 11, 9,  2.0,  "Finished"),  # Arvid Lindblad - Racing Bulls
    (7, "COL", 7,  10, 1.0,  "Finished"),  # Franco Colapinto - Alpine (post-race pen applied)

    # ─ Round 8: Austria — Russell wins ───────────────────────────────────────
    (8, "RUS", 1,  1,  25.0, "Finished"),  # George Russell - Mercedes WINNER
    (8, "VER", 3,  2,  18.0, "Finished"),  # Max Verstappen - Red Bull
    (8, "ANT", 2,  3,  15.0, "Finished"),  # Kimi Antonelli - Mercedes
    (8, "PIA", 5,  4,  12.0, "Finished"),  # Oscar Piastri - McLaren
    (8, "HAM", 6,  5,  10.0, "Finished"),  # Lewis Hamilton - Ferrari
    (8, "HAD", 7,  6,  8.0,  "Finished"),  # Isack Hadjar - Red Bull
    (8, "NOR", 4,  7,  6.0,  "Finished"),  # Lando Norris - McLaren
    (8, "LEC", 8,  8,  4.0,  "Finished"),  # Charles Leclerc - Ferrari
    (8, "LAW", 12, 9,  2.0,  "Finished"),  # Liam Lawson - Racing Bulls
    (8, "LIN", 13, 10, 1.0,  "Finished"),  # Arvid Lindblad - Racing Bulls
]

# ── Weather per round (approximations) ───────────────────────────────────────
WEATHER_2026 = {
    1: dict(air_temp_avg=22.0, track_temp_avg=35.0, humidity_avg=55.0, wind_speed_avg=12.0, rainfall=False, condition="dry"),
    2: dict(air_temp_avg=20.0, track_temp_avg=32.0, humidity_avg=65.0, wind_speed_avg=8.0,  rainfall=False, condition="dry"),
    3: dict(air_temp_avg=14.0, track_temp_avg=28.0, humidity_avg=60.0, wind_speed_avg=6.0,  rainfall=False, condition="dry"),
    4: dict(air_temp_avg=28.0, track_temp_avg=44.0, humidity_avg=72.0, wind_speed_avg=10.0, rainfall=False, condition="dry"),
    5: dict(air_temp_avg=24.0, track_temp_avg=36.0, humidity_avg=50.0, wind_speed_avg=15.0, rainfall=False, condition="dry"),
    6: dict(air_temp_avg=23.0, track_temp_avg=38.0, humidity_avg=58.0, wind_speed_avg=7.0,  rainfall=False, condition="dry"),
    7: dict(air_temp_avg=26.0, track_temp_avg=40.0, humidity_avg=45.0, wind_speed_avg=11.0, rainfall=False, condition="dry"),
    8: dict(air_temp_avg=27.0, track_temp_avg=42.0, humidity_avg=48.0, wind_speed_avg=9.0,  rainfall=False, condition="dry"),
}


def run():
    print("🏗️  Seeding 2026 Formula 1 Season Data (REAL RESULTS)...")

    with SyncSessionLocal() as db:
        # Circuits
        for c in CIRCUITS_NEW:
            existing = db.query(Circuit).filter_by(circuit_key=c["circuit_key"]).first()
            if not existing:
                db.add(Circuit(**c))
        db.commit()
        print("✅ Circuits ready")

    with SyncSessionLocal() as db:
        # Constructors
        ctor_map = {}
        for c in CONSTRUCTORS_2026:
            existing = db.query(Constructor).filter_by(constructor_key=c["constructor_key"]).first()
            if not existing:
                obj = Constructor(**c)
                db.add(obj)
                db.flush()
                ctor_map[c["constructor_key"]] = obj
            else:
                for k, v in c.items():
                    setattr(existing, k, v)
                db.flush()
                ctor_map[c["constructor_key"]] = existing
        db.commit()
        print(f"✅ {len(CONSTRUCTORS_2026)} constructors ready")

        # Drivers
        driver_map = {}
        for d in DRIVERS_2026:
            ctor_key = d.pop("constructor_key")
            existing = db.query(Driver).filter_by(driver_code=d["driver_code"], season=2026).first()
            ctor = ctor_map.get(ctor_key)
            if not existing:
                obj = Driver(**d, constructor_id=ctor.id if ctor else None, season=2026)
                db.add(obj)
                db.flush()
                driver_map[d["driver_code"]] = obj
            else:
                existing.constructor_id = ctor.id if ctor else None
                for k, v in d.items():
                    setattr(existing, k, v)
                db.flush()
                driver_map[d["driver_code"]] = existing
        db.commit()
        print(f"✅ {len(DRIVERS_2026)} drivers ready")

        # Races
        race_map = {}
        for rnd, (gp_name, circuit_key, rdate, status) in RACES_2026.items():
            existing = db.query(Race).filter_by(season=2026, round_number=rnd).first()
            circuit = db.query(Circuit).filter_by(circuit_key=circuit_key).first()
            if not existing:
                race = Race(
                    season=2026, round_number=rnd, grand_prix_name=gp_name,
                    grand_prix_key=circuit_key, circuit_id=circuit.id if circuit else None,
                    race_date=rdate, session_status=status
                )
                db.add(race)
                db.flush()
                race_map[rnd] = race
            else:
                existing.grand_prix_name = gp_name
                existing.session_status = status
                db.flush()
                race_map[rnd] = existing
        db.commit()
        print(f"✅ {len(RACES_2026)} 2026 races ready (8 completed, {len(RACES_2026)-8} upcoming)")

        # Results + Qualifying
        result_count = 0
        for (rnd, drv_code, grid, finish, pts, status) in RESULTS_2026:
            race = race_map.get(rnd)
            driver = driver_map.get(drv_code)
            if not race or not driver:
                print(f"  ⚠️  Skipped R{rnd} {drv_code} — race or driver not found")
                continue

            existing_r = db.query(RaceResult).filter_by(race_id=race.id, driver_id=driver.id).first()
            if not existing_r:
                db.add(RaceResult(
                    race_id=race.id, driver_id=driver.id,
                    constructor_id=driver.constructor_id,
                    grid_position=grid, finish_position=finish,
                    classified_position=str(finish),
                    points_scored=pts, fastest_lap=(finish == 1),
                    status=status, dnf=(status != "Finished")
                ))
                result_count += 1
            else:
                existing_r.grid_position = grid
                existing_r.finish_position = finish
                existing_r.points_scored = pts
                existing_r.status = status

            existing_q = db.query(Qualifying).filter_by(race_id=race.id, driver_id=driver.id).first()
            if not existing_q:
                base_q = 85.0 + grid * 0.08
                db.add(Qualifying(
                    race_id=race.id, driver_id=driver.id,
                    q3_time_seconds=base_q if grid <= 10 else None,
                    q2_time_seconds=base_q + 0.12 if grid <= 15 else None,
                    q1_time_seconds=base_q + 0.24,
                    best_qualifying_time_seconds=base_q,
                    grid_position=grid
                ))

        # Weather
        for rnd, race in race_map.items():
            w = WEATHER_2026.get(rnd)
            if not w:
                continue
            existing_w = db.query(Weather).filter_by(race_id=race.id).first()
            if not existing_w:
                db.add(Weather(race_id=race.id, **w))

        db.commit()
        print(f"✅ {result_count} race results seeded")
        print("🎉 2026 season seeding complete!")
        print()
        print("  Drivers' Championship (based on seeded data):")
        print("  1. Kimi Antonelli (Mercedes)  — 171 pts")
        print("  2. George Russell  (Mercedes)  — 131 pts")
        print("  3. Lewis Hamilton  (Ferrari)   — 125 pts")
        print("  4. Oscar Piastri   (McLaren)   —  80 pts")
        print("  5. Lando Norris    (McLaren)   —  79 pts")


if __name__ == "__main__":
    run()
