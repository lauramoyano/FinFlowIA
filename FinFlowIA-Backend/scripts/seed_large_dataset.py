"""
Seed the local Postgres database with a large synthetic dataset spread across
several demo businesses, for exercising the dashboard, reports, and
transaction list under realistic volume (pagination, category breakdown,
month-over-month trends, etc.) instead of the ~15-row sample in seed.py.

This complements (does not replace) scripts/seed_db.py:
- seed_db.py            -> tiny, fast, deterministic sample for quick local checks
- seed_large_dataset.py -> ~1500+ transactions across 3 demo users, 12 months

Usage:
    python scripts/seed_large_dataset.py
    python scripts/seed_large_dataset.py --users 5 --per-user 500

Requires the backend's virtualenv (SQLAlchemy, asyncpg, passlib) and a
reachable DATABASE_URL, same as seed_db.py.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path
from random import uniform

sys.path.insert(0, str(Path(__file__).parent.parent))

from passlib.context import CryptContext  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine  # noqa: E402

from scripts.synthetic_data import generate_transactions  # noqa: E402
from src.config.settings import settings  # noqa: E402
from src.modules.auth.models import User  # noqa: E402
from src.modules.transactions.models import Transaction  # noqa: E402
from src.shared.domain.base_entity import Base  # noqa: E402

pwd_context = CryptContext(schemes=["bcrypt"], bcrypt__rounds=4)

DEMO_BUSINESSES = [
    ("owner1@finflowia.dev", "Panadería La Espiga", "demo1234"),
    ("owner2@finflowia.dev", "Taller Mecánico Rueda", "demo1234"),
    ("owner3@finflowia.dev", "Estudio Diseño Pixel", "demo1234"),
    ("owner4@finflowia.dev", "Consultoría Financiera Norte", "demo1234"),
    ("owner5@finflowia.dev", "Tienda de Insumos Andina", "demo1234"),
]


async def seed_large_dataset(num_users: int, per_user: int) -> None:
    engine = create_async_engine(settings.database_url, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    total_transactions = 0

    async with async_session() as session:
        businesses = DEMO_BUSINESSES[:num_users]

        for idx, (email, full_name, password) in enumerate(businesses):
            user = User(
                email=email,
                hashed_password=pwd_context.hash(password),
                full_name=full_name,
                is_active=True,
            )
            session.add(user)
            await session.flush()

            # Different seed per user so each business has a distinct but
            # reproducible transaction history.
            transactions = generate_transactions(per_user, seed=100 + idx)

            for t in transactions:
                session.add(
                    Transaction(
                        user_id=user.id,
                        description=t.description,
                        amount=t.amount,
                        transaction_type=t.transaction_type,
                        category=t.category,
                        ai_confidence=round(uniform(0.78, 0.99), 2),
                        transaction_date=t.transaction_date,
                        notes=None,
                    )
                )
            total_transactions += len(transactions)

            print(f"Queued {len(transactions)} transactions for {email} ({full_name})")

        await session.commit()

    await engine.dispose()
    print(f"\nDone. Seeded {num_users} demo businesses, {total_transactions} transactions total.")
    print("All demo users share the password: demo1234")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--users", type=int, default=3, help="Number of demo businesses (max 5)")
    parser.add_argument("--per-user", type=int, default=500, help="Transactions per business")
    args = parser.parse_args()

    num_users = min(args.users, len(DEMO_BUSINESSES))
    asyncio.run(seed_large_dataset(num_users, args.per_user))


if __name__ == "__main__":
    main()
