import difflib
import re
import uuid
from dataclasses import dataclass
from decimal import Decimal

from src.modules.production.models import Product
from src.modules.production.repository import ProductionEstimateRepository, ProductRepository
from src.modules.transactions.repository import TransactionRepository
from src.shared.utils.text_utils import singularize

FUZZY_MATCH_CUTOFF = 0.85


@dataclass
class ExpenseHistory:
    """Past expenses that mention a preparation by name."""

    count: int
    total: Decimal


@dataclass
class LinkedInsumos:
    """Insumos cost recalled from the latest estimate of products a message mentions."""

    product_names: list[str]
    insumos_cost: Decimal


class ProductMemory:
    """
    What the system already knows about the user's preparations, shared by
    every agent so they all recognise the same things: catalog products
    (tolerating plural/typo variants), costs from earlier estimates, and
    earlier expenses mentioning the preparation. Read-only; agents decide
    what to do with it.
    """

    def __init__(
        self,
        product_repo: ProductRepository,
        estimate_repo: ProductionEstimateRepository,
        transaction_repo: TransactionRepository,
    ) -> None:
        self._product_repo = product_repo
        self._estimate_repo = estimate_repo
        self._transaction_repo = transaction_repo

    async def find_product(self, user_id: uuid.UUID, name: str) -> Product | None:
        product = await self._product_repo.get_by_name(user_id, name)
        if product is not None:
            return product

        stem = singularize(name)
        for variant in (stem, f"{stem}s", f"{stem}es"):
            if variant == name.strip().lower():
                continue
            product = await self._product_repo.get_by_name(user_id, variant)
            if product is not None:
                return product

        catalog = await self._product_repo.list_for_user(user_id)
        by_stem = {singularize(p.name): p for p in catalog}
        close = difflib.get_close_matches(stem, list(by_stem), n=1, cutoff=FUZZY_MATCH_CUTOFF)
        return by_stem[close[0]] if close else None

    async def find_mentioned_products(self, user_id: uuid.UUID, text: str) -> list[Product]:
        """Catalog products named anywhere in free text (whole-word, plural-tolerant)."""
        lowered = text.lower()
        mentioned: list[Product] = []
        for product in await self._product_repo.list_for_user(user_id):
            stem = re.escape(singularize(product.name))
            if re.search(rf"\b{stem}(?:e?s)?\b", lowered):
                mentioned.append(product)
        return mentioned

    async def expense_history(self, user_id: uuid.UUID, name: str) -> ExpenseHistory | None:
        expenses = await self._transaction_repo.search_expenses_by_description(user_id, singularize(name))
        if not expenses:
            return None
        return ExpenseHistory(
            count=len(expenses), total=sum((e.amount for e in expenses), Decimal("0"))
        )

    async def linked_insumos(self, user_id: uuid.UUID, text: str) -> LinkedInsumos | None:
        """
        If `text` mentions products with a previous estimate, the insumos cost
        of that latest estimate (only the mentioned products' lines).
        """
        products = await self.find_mentioned_products(user_id, text)
        if not products:
            return None
        items = await self._estimate_repo.latest_items_for_products(user_id, [p.id for p in products])
        if not items:
            return None
        covered = {i.product_id for i in items}
        return LinkedInsumos(
            product_names=[p.name for p in products if p.id in covered],
            insumos_cost=sum((i.subtotal for i in items), Decimal("0")),
        )
