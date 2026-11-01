import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import Base, engine, SessionLocal
from app.services.seed_data import seed_database

if __name__ == "__main__":
    print("=" * 70)
    print("  [*] BhashaLok - Regional Language & Dialects Database Seeder")
    print("=" * 70)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db)
        print("  [+] Seeding completed successfully!")
    finally:
        db.close()
    print("=" * 70)
