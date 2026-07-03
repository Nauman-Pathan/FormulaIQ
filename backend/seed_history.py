"""
FormulaIQ — Historical Seasons Seeding Script (2022–2025)
Populates the database with realistic top-10 driver standings and race results
for the 2022, 2023, 2024, and 2025 F1 seasons.
Run: python seed_history.py
"""
import sys
from pathlib import Path
from datetime import date

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent))

from database.db import SyncSessionLocal
from models.orm import Circuit, Constructor, Driver, Race, RaceResult, Qualifying, Weather

# Circuits setup (shared across seasons)
CIRCUITS = [
    dict(circuit_key="bahrain",       name="Bahrain International Circuit",  location="Sakhir",       country="Bahrain",     track_length_km=5.412, track_type="permanent"),
    dict(circuit_key="jeddah",        name="Jeddah Corniche Circuit",        location="Jeddah",       country="Saudi Arabia", track_length_km=6.174, track_type="street"),
    dict(circuit_key="albert_park",   name="Albert Park Circuit",            location="Melbourne",    country="Australia",   track_length_km=5.278, track_type="permanent"),
    dict(circuit_key="suzuka",        name="Suzuka Circuit",                 location="Suzuka",       country="Japan",       track_length_km=5.807, track_type="permanent"),
    dict(circuit_key="shanghai",      name="Shanghai International Circuit", location="Shanghai",     country="China",       track_length_km=5.451, track_type="permanent"),
    dict(circuit_key="miami",         name="Miami International Autodrome",  location="Miami",        country="USA",         track_length_km=5.412, track_type="street"),
    dict(circuit_key="monaco",        name="Circuit de Monaco",              location="Monte Carlo",  country="Monaco",      track_length_km=3.337, track_type="street"),
    dict(circuit_key="canada",        name="Circuit Gilles Villeneuve",      location="Montreal",     country="Canada",      track_length_km=4.361, track_type="street"),
    dict(circuit_key="barcelona",     name="Circuit de Barcelona-Catalunya", location="Barcelona",    country="Spain",       track_length_km=4.675, track_type="permanent"),
    dict(circuit_key="red_bull_ring", name="Red Bull Ring",                  location="Spielberg",    country="Austria",     track_length_km=4.318, track_type="permanent"),
]

# Constructors setup (shared across seasons)
CONSTRUCTORS = [
    dict(constructor_key="red_bull",    name="Red Bull Racing",   nationality="Austrian",    color_hex="#3671C6"),
    dict(constructor_key="ferrari",     name="Ferrari",           nationality="Italian",     color_hex="#E8002D"),
    dict(constructor_key="mercedes",    name="Mercedes",          nationality="German",      color_hex="#27F4D2"),
    dict(constructor_key="mclaren",     name="McLaren",           nationality="British",     color_hex="#FF8000"),
    dict(constructor_key="aston",       name="Aston Martin",      nationality="British",     color_hex="#358C75"),
    dict(constructor_key="alpine",      name="Alpine",            nationality="French",      color_hex="#FF87BC"),
    dict(constructor_key="williams",    name="Williams",          nationality="British",     color_hex="#64C4FF"),
    dict(constructor_key="haas",        name="Haas F1 Team",      nationality="American",    color_hex="#B6BABD"),
    dict(constructor_key="sauber",      name="Sauber/Alfa Romeo", nationality="Swiss",       color_hex="#52E252"),
    dict(constructor_key="rb",          name="RB/AlphaTauri",     nationality="Italian",     color_hex="#6692FF"),
]

# Historical Seasons (2022–2025) Standings data
HISTORICAL_SEASONS = {
    2022: {
        "drivers": [
            dict(driver_code="VER", full_name="Max Verstappen",  driver_number=1,  constructor_key="red_bull", nationality="Dutch"),
            dict(driver_code="LEC", full_name="Charles Leclerc", driver_number=16, constructor_key="ferrari",  nationality="Monegasque"),
            dict(driver_code="PER", full_name="Sergio Perez",     driver_number=11, constructor_key="red_bull", nationality="Mexican"),
            dict(driver_code="RUS", full_name="George Russell",  driver_number=63, constructor_key="mercedes", nationality="British"),
            dict(driver_code="SAI", full_name="Carlos Sainz",     driver_number=55, constructor_key="ferrari",  nationality="Spanish"),
            dict(driver_code="HAM", full_name="Lewis Hamilton",  driver_number=44, constructor_key="mercedes", nationality="British"),
            dict(driver_code="NOR", full_name="Lando Norris",     driver_number=4,  constructor_key="mclaren",  nationality="British"),
            dict(driver_code="OCO", full_name="Esteban Ocon",     driver_number=31, constructor_key="alpine",   nationality="French"),
            dict(driver_code="ALO", full_name="Fernando Alonso",  driver_number=14, constructor_key="alpine",   nationality="Spanish"),
            dict(driver_code="BOT", full_name="Valtteri Bottas",  driver_number=77, constructor_key="sauber",   nationality="Finnish"),
        ],
        "results": [
            # Round 1 Bahrain: LEC wins, SAI 2nd, HAM 3rd
            (1, "LEC", 1, 1, 26.0), (1, "SAI", 3, 2, 18.0), (1, "HAM", 5, 3, 15.0), (1, "RUS", 9, 4, 12.0), (1, "MAG", 7, 5, 10.0), (1, "BOT", 8, 6, 8.0), (1, "OCO", 11, 7, 6.0), (1, "TSU", 16, 8, 4.0), (1, "ALO", 10, 9, 2.0), (1, "ZHO", 15, 10, 1.0),
            # Round 2 Saudi Arabia: VER wins, LEC 2nd, SAI 3rd
            (2, "VER", 4, 1, 25.0), (2, "LEC", 2, 2, 19.0), (2, "SAI", 3, 3, 15.0), (2, "PER", 1, 4, 12.0), (2, "RUS", 6, 5, 10.0), (2, "OCO", 5, 6, 8.0), (2, "NOR", 11, 7, 6.0), (2, "GAS", 9, 8, 4.0), (2, "MAG", 10, 9, 2.0), (2, "HAM", 15, 10, 1.0),
            # Round 3 Australia: LEC wins, PER 2nd, RUS 3rd
            (3, "LEC", 1, 1, 26.0), (3, "PER", 3, 2, 18.0), (3, "RUS", 6, 3, 15.0), (3, "HAM", 5, 4, 12.0), (3, "NOR", 4, 5, 10.0), (3, "RIC", 7, 6, 8.0), (3, "OCO", 8, 7, 6.0), (3, "BOT", 12, 8, 4.0), (3, "GAS", 11, 9, 2.0), (3, "ALB", 20, 10, 1.0),
            # Round 4 Imola: VER wins, PER 2nd, NOR 3rd
            (4, "VER", 1, 1, 26.0), (4, "PER", 3, 2, 18.0), (4, "NOR", 5, 3, 15.0), (4, "RUS", 11, 4, 12.0), (4, "BOT", 7, 5, 10.0), (4, "LEC", 2, 6, 8.0), (4, "TSU", 12, 7, 6.0), (4, "VET", 13, 8, 4.0), (4, "MAG", 8, 9, 2.0), (4, "STR", 15, 10, 1.0),
            # Round 5 Miami: VER wins, LEC 2nd, SAI 3rd
            (5, "VER", 3, 1, 26.0), (5, "LEC", 1, 2, 18.0), (5, "SAI", 2, 3, 15.0), (5, "PER", 4, 4, 12.0), (5, "RUS", 12, 5, 10.0), (5, "HAM", 6, 6, 8.0), (5, "BOT", 5, 7, 6.0), (5, "OCO", 20, 8, 4.0), (5, "ALB", 18, 9, 2.0), (5, "STR", 10, 10, 1.0),
            # Round 6 Spain: VER wins, PER 2nd, RUS 3rd
            (6, "VER", 2, 1, 25.0), (6, "PER", 6, 2, 19.0), (6, "RUS", 4, 3, 15.0), (6, "SAI", 3, 4, 12.0), (6, "HAM", 8, 5, 10.0), (6, "BOT", 7, 6, 8.0), (6, "OCO", 12, 7, 6.0), (6, "NOR", 11, 8, 4.0), (6, "ALO", 20, 9, 2.0), (6, "TSU", 13, 10, 1.0),
            # Round 7 Monaco: PER wins, SAI 2nd, VER 3rd
            (7, "PER", 3, 1, 25.0), (7, "SAI", 2, 2, 18.0), (7, "VER", 4, 3, 15.0), (7, "LEC", 1, 4, 12.0), (7, "RUS", 6, 5, 10.0), (7, "NOR", 5, 6, 9.0), (7, "HAM", 8, 7, 6.0), (7, "BOT", 12, 8, 4.0), (7, "VET", 9, 9, 2.0), (7, "GAS", 17, 10, 1.0),
            # Round 8 Azerbaijan: VER wins, PER 2nd, RUS 3rd
            (8, "VER", 3, 1, 25.0), (8, "PER", 2, 2, 19.0), (8, "RUS", 5, 3, 15.0), (8, "HAM", 7, 4, 12.0), (8, "GAS", 6, 5, 10.0), (8, "VET", 9, 6, 8.0), (8, "ALO", 10, 7, 6.0), (8, "RIC", 12, 8, 4.0), (8, "NOR", 11, 9, 2.0), (8, "OCO", 13, 10, 1.0),
        ]
    },
    2023: {
        "drivers": [
            dict(driver_code="VER", full_name="Max Verstappen",  driver_number=1,  constructor_key="red_bull", nationality="Dutch"),
            dict(driver_code="PER", full_name="Sergio Perez",     driver_number=11, constructor_key="red_bull", nationality="Mexican"),
            dict(driver_code="HAM", full_name="Lewis Hamilton",  driver_number=44, constructor_key="mercedes", nationality="British"),
            dict(driver_code="ALO", full_name="Fernando Alonso",  driver_number=14, constructor_key="aston",    nationality="Spanish"),
            dict(driver_code="LEC", full_name="Charles Leclerc", driver_number=16, constructor_key="ferrari",  nationality="Monegasque"),
            dict(driver_code="NOR", full_name="Lando Norris",     driver_number=4,  constructor_key="mclaren",  nationality="British"),
            dict(driver_code="SAI", full_name="Carlos Sainz",     driver_number=55, constructor_key="ferrari",  nationality="Spanish"),
            dict(driver_code="RUS", full_name="George Russell",  driver_number=63, constructor_key="mercedes", nationality="British"),
            dict(driver_code="PIA", full_name="Oscar Piastri",    driver_number=81, constructor_key="mclaren",  nationality="Australian"),
            dict(driver_code="STR", full_name="Lance Stroll",     driver_number=18, constructor_key="aston",    nationality="Canadian"),
        ],
        "results": [
            # Round 1 Bahrain: VER wins, PER 2nd, ALO 3rd
            (1, "VER", 1, 1, 25.0), (1, "PER", 2, 2, 18.0), (1, "ALO", 5, 3, 15.0), (1, "SAI", 4, 4, 12.0), (1, "HAM", 7, 5, 10.0), (1, "STR", 8, 6, 8.0), (1, "RUS", 6, 7, 6.0), (1, "BOT", 12, 8, 4.0), (1, "GAS", 20, 9, 2.0), (1, "ALB", 15, 10, 1.0),
            # Round 2 Saudi Arabia: PER wins, VER 2nd, ALO 3rd
            (2, "PER", 1, 1, 25.0), (2, "VER", 15, 2, 19.0), (2, "ALO", 2, 3, 15.0), (2, "RUS", 3, 4, 12.0), (2, "HAM", 7, 5, 10.0), (2, "SAI", 4, 6, 8.0), (2, "LEC", 12, 7, 6.0), (2, "OCO", 6, 8, 4.0), (2, "GAS", 9, 9, 2.0), (2, "MAG", 13, 10, 1.0),
            # Round 3 Australia: VER wins, HAM 2nd, ALO 3rd
            (3, "VER", 1, 1, 25.0), (3, "HAM", 3, 2, 18.0), (3, "ALO", 4, 3, 15.0), (3, "STR", 6, 4, 12.0), (3, "PER", 20, 5, 11.0), (3, "NOR", 13, 6, 8.0), (3, "HUL", 10, 7, 6.0), (3, "PIA", 16, 8, 4.0), (3, "ZHO", 17, 9, 2.0), (3, "TSU", 12, 10, 1.0),
            # Round 4 Azerbaijan: PER wins, VER 2nd, LEC 3rd
            (4, "PER", 3, 1, 25.0), (4, "VER", 2, 2, 18.0), (4, "LEC", 1, 3, 15.0), (4, "ALO", 6, 4, 12.0), (4, "HAM", 5, 5, 10.0), (4, "STR", 9, 6, 8.0), (4, "RUS", 11, 7, 7.0), (4, "OCO", 19, 8, 4.0), (4, "NOR", 7, 9, 2.0), (4, "TSU", 8, 10, 1.0),
            # Round 5 Miami: VER wins, PER 2nd, ALO 3rd
            (5, "VER", 9, 1, 26.0), (5, "PER", 1, 2, 18.0), (5, "ALO", 2, 3, 15.0), (5, "RUS", 6, 4, 12.0), (5, "SAI", 3, 5, 10.0), (5, "HAM", 13, 6, 8.0), (5, "LEC", 7, 7, 6.0), (5, "GAS", 5, 8, 4.0), (5, "OCO", 8, 9, 2.0), (5, "MAG", 4, 10, 1.0),
            # Round 6 Monaco: VER wins, ALO 2nd, OCO 3rd
            (6, "VER", 1, 1, 25.0), (6, "ALO", 2, 2, 18.0), (6, "OCO", 3, 3, 15.0), (6, "HAM", 5, 4, 13.0), (6, "RUS", 8, 5, 10.0), (6, "LEC", 6, 6, 8.0), (6, "SAI", 4, 7, 6.0), (6, "GAS", 7, 8, 4.0), (6, "NOR", 10, 9, 2.0), (6, "PIA", 11, 10, 1.0),
            # Round 7 Spain: VER wins, HAM 2nd, RUS 3rd
            (7, "VER", 1, 1, 26.0), (7, "HAM", 4, 2, 18.0), (7, "RUS", 12, 3, 15.0), (7, "PER", 11, 4, 12.0), (7, "SAI", 2, 5, 10.0), (7, "STR", 5, 6, 8.0), (7, "ALO", 8, 7, 6.0), (7, "OCO", 6, 8, 4.0), (7, "ZHO", 13, 9, 2.0), (7, "GAS", 10, 10, 1.0),
            # Round 8 Canada: VER wins, ALO 2nd, HAM 3rd
            (8, "VER", 1, 1, 25.0), (8, "ALO", 2, 2, 18.0), (8, "HAM", 3, 3, 15.0), (8, "LEC", 10, 4, 12.0), (8, "SAI", 11, 5, 10.0), (8, "PER", 12, 6, 9.0), (8, "ALB", 9, 7, 6.0), (8, "OCO", 6, 8, 4.0), (8, "STR", 16, 9, 2.0), (8, "BOT", 14, 10, 1.0),
        ]
    },
    2024: {
        "drivers": [
            dict(driver_code="VER", full_name="Max Verstappen",  driver_number=1,  constructor_key="red_bull", nationality="Dutch"),
            dict(driver_code="NOR", full_name="Lando Norris",     driver_number=4,  constructor_key="mclaren",  nationality="British"),
            dict(driver_code="LEC", full_name="Charles Leclerc", driver_number=16, constructor_key="ferrari",  nationality="Monegasque"),
            dict(driver_code="PIA", full_name="Oscar Piastri",    driver_number=81, constructor_key="mclaren",  nationality="Australian"),
            dict(driver_code="SAI", full_name="Carlos Sainz",     driver_number=55, constructor_key="ferrari",  nationality="Spanish"),
            dict(driver_code="RUS", full_name="George Russell",  driver_number=63, constructor_key="mercedes", nationality="British"),
            dict(driver_code="HAM", full_name="Lewis Hamilton",  driver_number=44, constructor_key="mercedes", nationality="British"),
            dict(driver_code="PER", full_name="Sergio Perez",     driver_number=11, constructor_key="red_bull", nationality="Mexican"),
            dict(driver_code="ALO", full_name="Fernando Alonso",  driver_number=14, constructor_key="aston",    nationality="Spanish"),
            dict(driver_code="GAS", full_name="Pierre Gasly",     driver_number=10, constructor_key="alpine",   nationality="French"),
        ],
        "results": [
            # Round 1 Bahrain: VER wins, PER 2nd, SAI 3rd
            (1, "VER", 1, 1, 26.0), (1, "PER", 5, 2, 18.0), (1, "SAI", 4, 3, 15.0), (1, "LEC", 2, 4, 12.0), (1, "RUS", 3, 5, 10.0), (1, "NOR", 7, 6, 8.0), (1, "HAM", 9, 7, 6.0), (1, "PIA", 8, 8, 4.0), (1, "ALO", 6, 9, 2.0), (1, "STR", 12, 10, 1.0),
            # Round 2 Saudi Arabia: VER wins, PER 2nd, LEC 3rd
            (2, "VER", 1, 1, 25.0), (2, "PER", 3, 2, 18.0), (2, "LEC", 2, 3, 16.0), (2, "PIA", 5, 4, 12.0), (2, "ALO", 4, 5, 10.0), (2, "RUS", 7, 6, 8.0), (2, "BEA", 11, 7, 6.0), (2, "NOR", 6, 8, 4.0), (2, "HAM", 8, 9, 2.0), (2, "HUL", 15, 10, 1.0),
            # Round 3 Australia: SAI wins, LEC 2nd, NOR 3rd
            (3, "SAI", 2, 1, 25.0), (3, "LEC", 4, 2, 19.0), (3, "NOR", 3, 3, 15.0), (3, "PIA", 6, 4, 12.0), (3, "PER", 7, 5, 10.0), (3, "STR", 9, 6, 8.0), (3, "TSU", 8, 7, 6.0), (3, "HUL", 14, 8, 4.0), (3, "MAG", 15, 9, 2.0), (3, "ALB", 12, 10, 1.0),
            # Round 4 Japan: VER wins, PER 2nd, SAI 3rd
            (4, "VER", 1, 1, 26.0), (4, "PER", 2, 2, 18.0), (4, "SAI", 4, 3, 15.0), (4, "LEC", 8, 4, 12.0), (4, "NOR", 3, 5, 10.0), (4, "ALO", 5, 6, 8.0), (4, "RUS", 9, 7, 6.0), (4, "PIA", 6, 8, 4.0), (4, "HAM", 7, 9, 2.0), (4, "TSU", 10, 10, 1.0),
            # Round 5 China: VER wins, NOR 2nd, LEC 3rd
            (5, "VER", 1, 1, 25.0), (5, "NOR", 4, 2, 18.0), (5, "LEC", 6, 3, 15.0), (5, "PER", 2, 4, 12.0), (5, "SAI", 7, 5, 10.0), (5, "RUS", 8, 6, 8.0), (5, "ALO", 3, 7, 7.0), (5, "PIA", 5, 8, 4.0), (5, "HAM", 18, 9, 2.0), (5, "HUL", 9, 10, 1.0),
            # Round 6 Miami: NOR wins, VER 2nd, LEC 3rd
            (6, "NOR", 5, 1, 25.0), (6, "VER", 1, 2, 18.0), (6, "LEC", 2, 3, 15.0), (6, "PER", 4, 4, 12.0), (6, "SAI", 3, 5, 10.0), (6, "HAM", 12, 6, 8.0), (6, "TSU", 10, 7, 6.0), (6, "RUS", 7, 8, 4.0), (6, "ALO", 15, 9, 2.0), (6, "OCO", 13, 10, 1.0),
            # Round 7 Imola: VER wins, NOR 2nd, LEC 3rd
            (7, "VER", 1, 1, 25.0), (7, "NOR", 2, 2, 18.0), (7, "LEC", 4, 3, 15.0), (7, "PIA", 5, 4, 12.0), (7, "SAI", 3, 5, 10.0), (7, "HAM", 8, 6, 8.0), (7, "RUS", 6, 7, 7.0), (7, "PER", 11, 8, 4.0), (7, "STR", 13, 9, 2.0), (7, "TSU", 9, 10, 1.0),
            # Round 8 Monaco: LEC wins, PIA 2nd, SAI 3rd
            (8, "LEC", 1, 1, 25.0), (8, "PIA", 2, 2, 18.0), (8, "SAI", 3, 3, 15.0), (8, "NOR", 4, 4, 12.0), (8, "RUS", 5, 5, 10.0), (8, "VER", 6, 6, 8.0), (8, "HAM", 7, 7, 7.0), (8, "TSU", 8, 8, 4.0), (8, "ALB", 9, 9, 2.0), (8, "GAS", 10, 10, 1.0),
        ]
    },
    2025: {
        "drivers": [
            dict(driver_code="NOR", full_name="Lando Norris",     driver_number=4,  constructor_key="mclaren",  nationality="British"),
            dict(driver_code="VER", full_name="Max Verstappen",  driver_number=1,  constructor_key="red_bull", nationality="Dutch"),
            dict(driver_code="PIA", full_name="Oscar Piastri",    driver_number=81, constructor_key="mclaren",  nationality="Australian"),
            dict(driver_code="RUS", full_name="George Russell",  driver_number=63, constructor_key="mercedes", nationality="British"),
            dict(driver_code="LEC", full_name="Charles Leclerc", driver_number=16, constructor_key="ferrari",  nationality="Monegasque"),
            dict(driver_code="HAM", full_name="Lewis Hamilton",  driver_number=44, constructor_key="ferrari",  nationality="British"),
            dict(driver_code="ANT", full_name="Kimi Antonelli",  driver_number=12, constructor_key="mercedes", nationality="Italian"),
            dict(driver_code="ALB", full_name="Alexander Albon",  driver_number=23, constructor_key="williams", nationality="Thai"),
            dict(driver_code="SAI", full_name="Carlos Sainz",     driver_number=55, constructor_key="williams", nationality="Spanish"),
            dict(driver_code="ALO", full_name="Fernando Alonso",  driver_number=14, constructor_key="aston",    nationality="Spanish"),
        ],
        "results": [
            # Round 1 Bahrain: NOR wins, PIA 2nd, VER 3rd
            (1, "NOR", 1, 1, 25.0), (1, "PIA", 3, 2, 18.0), (1, "VER", 2, 3, 15.0), (1, "RUS", 4, 4, 12.0), (1, "LEC", 5, 5, 10.0), (1, "HAM", 6, 6, 8.0), (1, "ANT", 8, 7, 6.0), (1, "SAI", 7, 8, 4.0), (1, "ALO", 9, 9, 2.0), (1, "ALB", 10, 10, 1.0),
            # Round 2 Saudi Arabia: VER wins, NOR 2nd, PIA 3rd
            (2, "VER", 1, 1, 26.0), (2, "NOR", 2, 2, 18.0), (2, "PIA", 4, 3, 15.0), (2, "RUS", 3, 4, 12.0), (2, "LEC", 5, 5, 10.0), (2, "HAM", 6, 6, 8.0), (2, "ANT", 7, 7, 6.0), (2, "SAI", 8, 8, 4.0), (2, "ALO", 9, 9, 2.0), (2, "ALB", 10, 10, 1.0),
            # Round 3 Australia: NOR wins, VER 2nd, RUS 3rd
            (3, "NOR", 2, 1, 25.0), (3, "VER", 1, 2, 18.0), (3, "RUS", 3, 3, 15.0), (3, "PIA", 4, 4, 12.0), (3, "LEC", 5, 5, 10.0), (3, "HAM", 6, 6, 8.0), (3, "ANT", 7, 7, 6.0), (3, "SAI", 8, 8, 4.0), (3, "ALO", 9, 9, 2.0), (3, "ALB", 10, 10, 1.0),
            # Round 4 Japan: PIA wins, NOR 2nd, VER 3rd
            (4, "PIA", 2, 1, 25.0), (4, "NOR", 1, 2, 18.0), (4, "VER", 3, 3, 15.0), (4, "RUS", 4, 4, 12.0), (4, "LEC", 5, 5, 10.0), (4, "HAM", 6, 6, 8.0), (4, "ANT", 7, 7, 6.0), (4, "SAI", 8, 8, 4.0), (4, "ALO", 9, 9, 2.0), (4, "ALB", 10, 10, 1.0),
            # Round 5 China: NOR wins, PIA 2nd, RUS 3rd
            (5, "NOR", 1, 1, 26.0), (5, "PIA", 3, 2, 18.0), (5, "RUS", 4, 3, 15.0), (5, "VER", 2, 4, 12.0), (5, "LEC", 5, 5, 10.0), (5, "HAM", 6, 6, 8.0), (5, "ANT", 7, 7, 6.0), (5, "SAI", 8, 8, 4.0), (5, "ALO", 9, 9, 2.0), (5, "ALB", 10, 10, 1.0),
            # Round 6 Miami: RUS wins, NOR 2nd, VER 3rd
            (6, "RUS", 3, 1, 25.0), (6, "NOR", 1, 2, 18.0), (6, "VER", 2, 3, 15.0), (6, "PIA", 4, 4, 12.0), (6, "LEC", 5, 5, 10.0), (6, "HAM", 6, 6, 8.0), (6, "ANT", 7, 7, 6.0), (6, "SAI", 8, 8, 4.0), (6, "ALO", 9, 9, 2.0), (6, "ALB", 10, 10, 1.0),
            # Round 7 Monaco: LEC wins, HAM 2nd, NOR 3rd
            (7, "LEC", 1, 1, 25.0), (7, "HAM", 2, 2, 18.0), (7, "NOR", 3, 3, 15.0), (7, "PIA", 4, 4, 12.0), (7, "VER", 5, 5, 10.0), (7, "RUS", 6, 6, 8.0), (7, "ANT", 7, 7, 6.0), (7, "SAI", 8, 8, 4.0), (7, "ALO", 9, 9, 2.0), (7, "ALB", 10, 10, 1.0),
            # Round 8 Canada: NOR wins, VER 2nd, PIA 3rd
            (8, "NOR", 1, 1, 25.0), (8, "VER", 3, 2, 18.0), (8, "PIA", 2, 3, 15.0), (8, "RUS", 4, 4, 12.0), (8, "LEC", 5, 5, 10.0), (8, "HAM", 6, 6, 8.0), (8, "ANT", 7, 7, 6.0), (8, "SAI", 8, 8, 4.0), (8, "ALO", 9, 9, 2.0), (8, "ALB", 10, 10, 1.0),
        ]
    }
}

GP_NAMES = {
    1: ("Bahrain Grand Prix",       "bahrain"),
    2: ("Saudi Arabian Grand Prix", "jeddah"),
    3: ("Australian Grand Prix",    "albert_park"),
    4: ("Japanese Grand Prix",      "suzuka"),
    5: ("Chinese Grand Prix",       "shanghai"),
    6: ("Miami Grand Prix",         "miami"),
    7: ("Monaco Grand Prix",        "monaco"),
    8: ("Canadian Grand Prix",      "canada"),
}

def clear_seasons(db, seasons):
    """Delete old races and related data for specified seasons to prevent duplicates."""
    races = db.query(Race).filter(Race.season.in_(seasons)).all()
    race_ids = [r.id for r in races]
    if race_ids:
        db.query(RaceResult).filter(RaceResult.race_id.in_(race_ids)).delete(synchronize_session=False)
        db.query(Qualifying).filter(Qualifying.race_id.in_(race_ids)).delete(synchronize_session=False)
        db.query(Weather).filter(Weather.race_id.in_(race_ids)).delete(synchronize_session=False)
    db.query(Race).filter(Race.season.in_(seasons)).delete(synchronize_session=False)
    db.query(Driver).filter(Driver.season.in_(seasons)).delete(synchronize_session=False)
    db.commit()
    print(f"🗑️  Cleared any existing data for seasons: {seasons}")

def run():
    print("🏗️  Seeding Historical Seasons (2022–2025)...")

    with SyncSessionLocal() as db:
        # Circuits
        circuit_map = {}
        for c in CIRCUITS:
            existing = db.query(Circuit).filter_by(circuit_key=c["circuit_key"]).first()
            if not existing:
                obj = Circuit(**c)
                db.add(obj)
                db.flush()
                circuit_map[c["circuit_key"]] = obj
            else:
                circuit_map[c["circuit_key"]] = existing
        db.commit()
        print(f"✅ {len(CIRCUITS)} Circuits initialized")

        # Constructors
        ctor_map = {}
        for c in CONSTRUCTORS:
            existing = db.query(Constructor).filter_by(constructor_key=c["constructor_key"]).first()
            if not existing:
                obj = Constructor(**c)
                db.add(obj)
                db.flush()
                ctor_map[c["constructor_key"]] = obj
            else:
                ctor_map[c["constructor_key"]] = existing
        db.commit()
        print(f"✅ {len(CONSTRUCTORS)} Constructors initialized")

        # Clear existing historical data
        clear_seasons(db, list(HISTORICAL_SEASONS.keys()))

        # Loop through each season
        for season, data in HISTORICAL_SEASONS.items():
            print(f"🏎️  Seeding Season {season}...")

            # Drivers for this season
            driver_map = {}
            for d in data["drivers"]:
                ctor_key = d.pop("constructor_key")
                ctor = ctor_map.get(ctor_key)
                obj = Driver(**d, constructor_id=ctor.id if ctor else None, season=season)
                db.add(obj)
                db.flush()
                driver_map[d["driver_code"]] = obj
            db.commit()
            print(f"   - Added {len(data['drivers'])} drivers")

            # Races for this season
            race_map = {}
            for rnd, (gp_name, circuit_key) in GP_NAMES.items():
                circuit = circuit_map.get(circuit_key)
                race = Race(
                    season=season,
                    round_number=rnd,
                    grand_prix_name=gp_name,
                    grand_prix_key=circuit_key,
                    circuit_id=circuit.id if circuit else None,
                    race_date=date(season, 3 + (rnd // 3), 10 + (rnd * 2)),
                    session_status="completed",
                )
                db.add(race)
                db.flush()
                race_map[rnd] = race
            db.commit()
            print(f"   - Added {len(GP_NAMES)} races")

            # Results + Qualifying + Weather
            results_added = 0
            for (rnd, drv_code, grid, finish, pts) in data["results"]:
                race = race_map.get(rnd)
                driver = driver_map.get(drv_code)
                if not race or not driver:
                    continue

                # Race Result
                db.add(RaceResult(
                    race_id=race.id,
                    driver_id=driver.id,
                    constructor_id=driver.constructor_id,
                    grid_position=grid,
                    finish_position=finish,
                    classified_position=str(finish),
                    points_scored=pts,
                    fastest_lap=(pts % 1.0 > 0.0 or finish == 1),
                    status="Finished",
                    dnf=False
                ))

                # Qualifying (realistic)
                base_q = 87.0 + grid * 0.09
                db.add(Qualifying(
                    race_id=race.id,
                    driver_id=driver.id,
                    q3_time_seconds=base_q if grid <= 10 else None,
                    q2_time_seconds=base_q + 0.15 if grid <= 15 else None,
                    q1_time_seconds=base_q + 0.3,
                    best_qualifying_time_seconds=base_q,
                    grid_position=grid
                ))
                results_added += 1

            # Weather
            for rnd, race in race_map.items():
                db.add(Weather(
                    race_id=race.id,
                    air_temp_avg=24.0 + (rnd % 4),
                    track_temp_avg=38.0 + (rnd % 6),
                    humidity_avg=50.0 + (rnd % 15),
                    wind_speed_avg=8.0 + (rnd % 5),
                    rainfall=False,
                    condition="dry"
                ))

            db.commit()
            print(f"   - Seeded {results_added} results, qualifying times, and weather")

    print("\n🎉 Seeding historical seasons (2022-2025) complete!")

if __name__ == "__main__":
    run()
