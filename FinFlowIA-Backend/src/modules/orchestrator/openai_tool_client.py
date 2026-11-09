import structlog

logger = structlog.get_logger(__name__)

ROUTING_SYSTEM_PROMPT = """Sos el router de un asistente financiero para dueños de pequeños
negocios. Tu única tarea es decidir a cuál de 4 procesos especializados corresponde cada
mensaje del usuario. No respondas el mensaje ni expliques nada: solo llamá a la función
correspondiente.

Si el mensaje no encaja claramente en ninguno pero menciona un gasto o un ingreso (por
ejemplo "gasté 500 en nafta" o "me pagaron 2000"), usá route_to_classification por defecto."""

ROUTING_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "route_to_classification",
            "description": (
                "El usuario quiere registrar un ingreso o un gasto a partir de un mensaje en "
                "lenguaje natural (ej: 'gasté 500 en nafta', 'cobré 2000 de una venta'). Hay que "
                "extraer descripción, monto, tipo, fecha y categoría; si falta el monto u otro "
                "dato obligatorio, se le pregunta por él antes de confirmar."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "route_to_period_summary",
            "description": (
                "El usuario pide un resumen de sus ingresos/gastos en un periodo (ej: '¿cómo me "
                "fue este mes?') o quiere comparar varios periodos entre sí (ej: 'comparame este "
                "mes con el anterior')."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "route_to_production_estimate",
            "description": (
                "El usuario quiere estimar cuánto le cuesta producir una cantidad de uno o más "
                "productos de su catálogo, a partir del costo de insumos por unidad (ej: "
                "'¿cuánto me cuesta hacer 10 tortas?'). También cubre cuando quiere calcular "
                "cuántas unidades mínimas de un producto tiene que vender para alcanzar una meta "
                "de ingresos, y cuánto necesita invertir en insumos para eso (ej: 'quiero vender "
                "2.000.000 en la feria', 'necesito juntar 500.000 vendiendo tortas')."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "route_to_financial_recommendation",
            "description": (
                "El usuario quiere una recomendación de cómo repartir el dinero de una venta o "
                "ingreso entre gastos, ahorro y utilidad, considerando sus deudas y gastos "
                "recurrentes (ej: 'vendí 5000, ¿cómo lo reparto?')."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
]

ROUTE_TOOL_NAMES: dict[str, str] = {
    "route_to_classification": "classification",
    "route_to_period_summary": "period_summary",
    "route_to_production_estimate": "production_estimate",
    "route_to_financial_recommendation": "financial_recommendation",
}


class OpenAIToolClient:
    """
    Dedicated client for intent-routing via OpenAI's native tool calling.

    Kept separate from the LLMProvider Protocol (src/modules/ai/providers/base.py):
    that one is a plain-text-completion abstraction with primary/fallback
    provider switching, a different shape from tool calling — which, per
    project decision, only runs against OpenAI for now.
    """

    def __init__(self, api_key: str, model: str = "gpt-5-nano") -> None:
        self._api_key = api_key
        self._model = model
        self._client = None

    def _get_client(self):  # type: ignore
        if self._client is None:
            import openai
            self._client = openai.AsyncOpenAI(api_key=self._api_key)
        return self._client

    async def route_intent(self, text: str) -> str:
        """
        Classify a user message into one of: classification | period_summary |
        production_estimate | financial_recommendation. Falls back to
        "classification" if the call fails — the safest default, since the
        classification agent already handles non-transaction text gracefully
        via the "not_a_transaction" error.
        """
        try:
            client = self._get_client()
            response = await client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": ROUTING_SYSTEM_PROMPT},
                    {"role": "user", "content": text},
                ],
                tools=ROUTING_TOOLS,
                tool_choice="required",
            )
            tool_call = response.choices[0].message.tool_calls[0]
            intent = ROUTE_TOOL_NAMES.get(tool_call.function.name, "classification")
            logger.debug("orchestrator_routed", intent=intent)
            return intent
        except Exception as e:
            logger.error("orchestrator_routing_failed", error=str(e))
            return "classification"
