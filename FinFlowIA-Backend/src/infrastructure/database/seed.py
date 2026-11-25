"""Database seed script with sample data for development and testing."""

import asyncio
import uuid
from datetime import date, timedelta
from decimal import Decimal
from random import choice, uniform

from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.config.settings import settings
from src.modules.auth.models import User
from src.modules.transactions.enums import CategoryType, TransactionType
from src.modules.transactions.models import Transaction
from src.shared.domain.base_entity import Base

pwd_context = CryptContext(schemes=["bcrypt"], bcrypt__rounds=4)

SAMPLE_TRANSACTIONS = [
    ("Almuerzo equipo", Decimal("850.00"), "expense", "food"),
    ("Factura internet", Decimal("2500.00"), "expense", "utilities"),
    ("Venta producto cliente A", Decimal("15000.00"), "income", "sales"),
    ("Combustible delivery", Decimal("1200.00"), "expense", "transport"),
    ("Materiales oficina", Decimal("450.00"), "expense", "supplies"),
    ("Honorarios consultoría", Decimal("25000.00"), "income", "services"),
    ("Alquiler local", Decimal("8000.00"), "expense", "rent"),
    ("Publicidad redes sociales", Decimal("3000.00"), "expense", "marketing"),
    ("Venta producto cliente B", Decimal("8500.00"), "income", "sales"),
    ("Servicio electricidad", Decimal("1800.00"), "expense", "utilities"),
    ("Sueldo empleado", Decimal("45000.00"), "expense", "payroll"),
    ("Consultoria cliente C", Decimal("12000.00"), "income", "services"),
    ("Café y snacks reunión", Decimal("350.00"), "expense", "food"),
    ("Taxi cliente", Decimal("650.00"), "expense", "transport"),
    ("Software herramienta", Decimal("2200.00"), "expense", "equipment"),
]


async def seed_database() -> None:
    engine = create_async_engine(settings.database_url, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Create demo user
        demo_user = User(
            email="demo@finflowia.com",
            hashed_password=pwd_context.hash("demo1234"),
            full_name="Demo User",
            is_active=True,
        )
        session.add(demo_user)
        await session.flush()

        # Create sample transactions over the last 30 days
        today = date.today()
        for i, (description, amount, tx_type, category) in enumerate(SAMPLE_TRANSACTIONS):
            tx_date = today - timedelta(days=i * 2)
            transaction = Transaction(
                user_id=demo_user.id,
                description=description,
                amount=amount,
                transaction_type=tx_type,
                category=category,
                ai_confidence=round(uniform(0.80, 0.99), 2),
                transaction_date=tx_date,
                notes=f"Sample transaction #{i + 1}",
            )
            session.add(transaction)

        await session.commit()
        print(f"Seeded demo user: demo@finflowia.com (password: demo1234)")
        print(f"Seeded {len(SAMPLE_TRANSACTIONS)} sample transactions")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_database())
