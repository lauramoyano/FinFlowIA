"""
Shared synthetic transaction data generator for FinFlowIA.

Used by:
- generate_eval_dataset.py  -> labeled dataset to evaluate categorization accuracy
- seed_large_dataset.py     -> larger dataset to populate the local dev database

Pure stdlib (no third-party deps) so it can run anywhere Python 3.10+ runs,
independent of whether the project's virtualenv is set up yet.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal

# Category -> (transaction_type, description templates, min amount, max amount)
# Descriptions intentionally mimic how a small business owner would type a
# transaction: informal, Spanish-first (matches the target market), sometimes
# with a client/vendor name appended for extra variety.
CATEGORY_TEMPLATES: dict[str, tuple[str, list[str], int, int]] = {
    "food": (
        "expense",
        [
            "Almuerzo equipo",
            "Cena con proveedor",
            "Café para reunión con clientes",
            "Snacks para la oficina",
            "Almuerzo delivery empleados",
            "Desayuno reunión de trabajo",
            "Catering evento pequeño",
        ],
        250,
        2500,
    ),
    "transport": (
        "expense",
        [
            "Combustible para reparto",
            "Taxi a reunión con cliente",
            "Peaje autopista",
            "Mantenimiento vehículo delivery",
            "Uber para mensajería",
            "Parqueadero centro",
            "Envío courier a cliente",
        ],
        150,
        3500,
    ),
    "utilities": (
        "expense",
        [
            "Factura de electricidad",
            "Pago de internet y telefonía",
            "Factura de agua",
            "Servicio de gas",
            "Recarga plan de datos línea negocio",
            "Factura de telefonía fija",
        ],
        400,
        6000,
    ),
    "supplies": (
        "expense",
        [
            "Compra de papelería",
            "Insumos de limpieza",
            "Material de embalaje",
            "Compra de resmas de papel",
            "Insumos para producción",
            "Bolsas y empaques",
            "Cartuchos de tinta",
        ],
        200,
        4000,
    ),
    "marketing": (
        "expense",
        [
            "Publicidad en redes sociales",
            "Campaña de Google Ads",
            "Diseño de folletos",
            "Impresión de banners",
            "Pago a influencer local",
            "Fotografía de productos",
        ],
        500,
        8000,
    ),
    "payroll": (
        "expense",
        [
            "Sueldo empleado administrativo",
            "Pago quincenal personal ventas",
            "Aguinaldo empleados",
            "Sueldo diseñador freelance",
            "Pago horas extra",
            "Nómina mensual equipo",
        ],
        8000,
        60000,
    ),
    "rent": (
        "expense",
        [
            "Alquiler local comercial",
            "Alquiler bodega",
            "Renta de oficina",
            "Alquiler depósito de mercancía",
        ],
        5000,
        20000,
    ),
    "equipment": (
        "expense",
        [
            "Compra de laptop",
            "Licencia software contable",
            "Compra de impresora",
            "Mantenimiento equipo de cómputo",
            "Compra de mobiliario",
            "Actualización POS",
        ],
        1000,
        15000,
    ),
    "sales": (
        "income",
        [
            "Venta de producto a cliente",
            "Venta mayorista",
            "Venta en tienda online",
            "Venta punto de venta",
            "Venta producto cliente frecuente",
            "Cobro pedido a domicilio",
        ],
        500,
        30000,
    ),
    "services": (
        "income",
        [
            "Honorarios por consultoría",
            "Servicio de mantenimiento a cliente",
            "Cobro por capacitación",
            "Servicio de diseño gráfico a cliente",
            "Honorarios proyecto freelance",
            "Cobro por asesoría",
        ],
        1000,
        40000,
    ),
    "other": (
        "expense",
        [
            "Comisión bancaria",
            "Ajuste contable",
            "Gasto varios",
            "Multa o recargo",
            "Donación local",
        ],
        50,
        3000,
    ),
}

CLIENT_SUFFIXES = [
    "", " - Cliente A", " - Cliente B", " cliente frecuente",
    " (proveedor habitual)", " zona norte", " sucursal centro", "",
]

# Weighted so the dataset roughly mirrors a real small business: lots of
# food/transport/supplies noise, payroll/rent are rarer but higher value.
CATEGORY_WEIGHTS: dict[str, float] = {
    "food": 14,
    "transport": 12,
    "utilities": 6,
    "supplies": 12,
    "marketing": 8,
    "payroll": 5,
    "rent": 3,
    "equipment": 6,
    "sales": 20,
    "services": 10,
    "other": 4,
}


@dataclass
class SyntheticTransaction:
    description: str
    amount: Decimal
    transaction_type: str
    category: str
    transaction_date: date


def _round_amount(value: float) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def generate_transactions(
    n: int,
    *,
    seed: int = 42,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[SyntheticTransaction]:
    """Generate `n` synthetic, labeled transactions spread across a date range."""
    rng = random.Random(seed)

    end_date = end_date or date.today()
    start_date = start_date or (end_date - timedelta(days=365))
    span_days = max((end_date - start_date).days, 1)

    categories = list(CATEGORY_WEIGHTS.keys())
    weights = [CATEGORY_WEIGHTS[c] for c in categories]

    transactions: list[SyntheticTransaction] = []
    for _ in range(n):
        category = rng.choices(categories, weights=weights, k=1)[0]
        tx_type, templates, min_amt, max_amt = CATEGORY_TEMPLATES[category]

        base_description = rng.choice(templates)
        suffix = rng.choice(CLIENT_SUFFIXES)
        description = f"{base_description}{suffix}".strip()

        amount = _round_amount(rng.uniform(min_amt, max_amt))
        tx_date = start_date + timedelta(days=rng.randint(0, span_days))

        transactions.append(
            SyntheticTransaction(
                description=description,
                amount=amount,
                transaction_type=tx_type,
                category=category,
                transaction_date=tx_date,
            )
        )

    transactions.sort(key=lambda t: t.transaction_date)
    return transactions
