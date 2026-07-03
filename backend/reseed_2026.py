"""
FormulaIQ — Clear 2026 data then re-seed with real results.
Run: python reseed_2026.py
"""
import sys
from pathlib import Path
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).parent))

from database.db import SyncSessionLocal
from models.orm import Race, RaceResult, Qualifying, Weather, Driver

def clear_and_reseed():
    print("🗑️  Clearing old 2026 data...")
    with SyncSessionLocal() as db:
        races_2026 = db.query(Race).filter_by(season=2026).all()
        race_ids = [r.id for r in races_2026]
        if race_ids:
            db.query(RaceResult).filter(RaceResult.race_id.in_(race_ids)).delete(synchronize_session=False)
            db.query(Qualifying).filter(Qualifying.race_id.in_(race_ids)).delete(synchronize_session=False)
            db.query(Weather).filter(Weather.race_id.in_(race_ids)).delete(synchronize_session=False)
        db.query(Race).filter_by(season=2026).delete(synchronize_session=False)
        db.query(Driver).filter_by(season=2026).delete(synchronize_session=False)
        db.commit()
        print(f"  Cleared {len(race_ids)} races and all related data")

    import seed_2026
    seed_2026.run()

if __name__ == "__main__":
    clear_and_reseed()
