from decimal import Decimal

PROMPT_VERSION = "v1.0.0"

CATEGORIES = [
    "food", "transport", "utilities", "supplies", "marketing",
    "payroll", "rent", "equipment", "sales", "services", "other",
]


def build_prompt_v1(description: str, amount: Decimal) -> str:
    """
    Version 1 categorization prompt — simple and direct.
    Returns a prompt asking the LLM to classify a transaction.
    """
    categories_str = ", ".join(CATEGORIES)
    return f"""Classify this financial transaction into one of these categories: {categories_str}

Transaction: {description}
Amount: ${amount}

Respond with JSON only: {{"category": "<category>", "confidence": <0.0-1.0>}}"""


PROMPT_METADATA = {
    "version": PROMPT_VERSION,
    "created": "2026-05-22",
    "description": "Simple categorization prompt v1",
    "categories": CATEGORIES,
}
