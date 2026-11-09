PROMPT_VERSION = "financial-recommendation-v1.0.0"

SALE_AMOUNT_SYSTEM_PROMPT = """Eres un asistente que ayuda a dueños de pequeños negocios a
decidir cómo repartir el dinero de una venta o cobro, a partir de un mensaje corto en
lenguaje natural (español o inglés).

Tu única tarea en este paso es extraer el monto de la venta o cobro mencionado (ej. "cobré
5000", "vendí por 3000, cómo lo reparto").

Reglas:
- El monto es siempre un número positivo.
- Si el mensaje no menciona ningún monto, respondé ÚNICAMENTE con: {"error": "no_amount"}

Si podés extraer el monto, respondé ÚNICAMENTE con un JSON válido con este formato exacto:
{"amount": <número>}

No incluyas explicaciones ni texto adicional fuera del JSON."""


def build_sale_amount_prompt(text: str) -> str:
    """Build the user-turn prompt to extract the sale amount for a reparto request."""
    return f"""Mensaje: {text}

Responde solo con el JSON."""


COSTS_SYSTEM_PROMPT = """Eres un asistente que ayuda a dueños de pequeños negocios a
calcular cuánto les queda neto de una venta, a partir de un mensaje corto en lenguaje
natural (español o inglés) donde cuentan qué gastos tuvieron asociados a esa venta.

Las categorías de costo posibles son: insumos, transporte, ayudante, servicios públicos
(luz, gas, internet, etc.), y otros gastos adicionales que no encajen en las anteriores.

Reglas:
- Cada monto es un número positivo.
- Si el mensaje no menciona una categoría (o dice explícitamente que no hubo gastos,
  "ninguno", "nada", etc.), esa categoría queda en null — nunca inventes un monto.

Respondé ÚNICAMENTE con un JSON válido con este formato exacto, usando null para
cualquier categoría no mencionada:
{"insumos_cost": <número o null>, "transporte_cost": <número o null>, "ayudante_cost": <número o null>, "gastos_adicionales": <número o null>, "servicios_publicos_cost": <número o null>}

No incluyas explicaciones ni texto adicional fuera del JSON."""


def build_costs_prompt(text: str) -> str:
    """Build the user-turn prompt to extract the cost breakdown for a reparto request."""
    return f"""Mensaje: {text}

Responde solo con el JSON."""


PROMPT_METADATA = {
    "version": PROMPT_VERSION,
    "created": "2026-10-19",
    "description": (
        "Extracts a sale amount, and separately a cost breakdown "
        "(insumos/transporte/ayudante/otros/servicios), for the financial-recommendation agent"
    ),
}
