"""Script to seed the database with sample data."""

import asyncio
import sys
from pathlib import Path

# Ensure src is in the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.infrastructure.database.seed import seed_database

if __name__ == "__main__":
    print("Seeding database with sample data...")
    asyncio.run(seed_database())
    print("Done!")
