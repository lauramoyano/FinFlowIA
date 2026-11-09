import re
from decimal import Decimal, InvalidOperation


def parse_decimal(text: str) -> Decimal | None:
    """
    Deterministically parse a free-text reply like "150", "$150", "1.500,50"
    into a positive Decimal. No LLM call needed — this is just a number.
    Shared by any agent's follow-up loop that asks the user for a plain
    amount (a cost, a price, a sale amount, ...).
    """
    cleaned = re.sub(r"[^\d.,]", "", text.strip())
    if not cleaned:
        return None
    if "," in cleaned and "." in cleaned:
        cleaned = cleaned.replace(",", "")
    elif "," in cleaned:
        cleaned = cleaned.replace(",", ".")
    try:
        value = Decimal(cleaned)
    except InvalidOperation:
        return None
    return value if value > 0 else None
