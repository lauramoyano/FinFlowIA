import re

_NAME_SEPARATORS = re.compile(r"\s*(?:,|;|\+|&|\by\b|\be\b|\band\b)\s*", re.IGNORECASE)


def singularize(name: str) -> str:
    """Crude es/en singular stem ("alfajores" → "alfajor", "tortas" → "torta")."""
    name = name.strip().lower()
    if len(name) > 4 and name.endswith("es"):
        return name[:-2]
    if len(name) > 3 and name.endswith("s"):
        return name[:-1]
    return name


def split_product_names(raw: str) -> list[str]:
    """"alfajores y tortas" → ["alfajores", "tortas"], de-duplicated, order kept."""
    names: list[str] = []
    for part in _NAME_SEPARATORS.split(raw.strip().lower()):
        part = part.strip()
        if part and part not in names:
            names.append(part)
    return names
