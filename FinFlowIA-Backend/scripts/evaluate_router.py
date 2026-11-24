"""
Offline evaluation of the chat orchestrator's language understanding, against
the real LLM (needs OPENAI_API_KEY in .env; a few cents per run).

Two measurements:
1. Routing: which agent each phrase is sent to (OpenAIToolClient.route_intent).
2. Extraction: for production phrases, whether the product names, quantities
   and goal amount are pulled out correctly (AIService.parse_production_estimate_text).

Phrases are written the way real users talk (informal, voseo, filler words,
typos), not as clean templates. Add every phrase that fails in real use.

Usage:
    python scripts/evaluate_router.py
    python scripts/evaluate_router.py --only routing
    python scripts/evaluate_router.py --only extraction
    python scripts/evaluate_router.py --only routing --repeat 5

The model is not deterministic, so a single run per phrase is noisy; use
--repeat to get a per-phrase pass rate before judging a prompt change.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.settings import settings  # noqa: E402
from src.modules.ai.providers.openai import OpenAIProvider  # noqa: E402
from src.modules.ai.service import AIService  # noqa: E402
from src.modules.orchestrator.openai_tool_client import OpenAIToolClient  # noqa: E402

ROUTING_CASES: list[tuple[str, str]] = [
    # classification: register an income/expense
    ("gasté 2500 en nafta", "classification"),
    ("me pagaron 80000 por el trabajo de ayer", "classification"),
    ("pagué la luz, 35 mil", "classification"),
    ("compré harina y huevos por 12000", "classification"),
    ("cobré una venta de 150000", "classification"),
    ("ayer le di 20000 al ayudante", "classification"),
    # period_summary
    ("cómo me fue este mes", "period_summary"),
    ("comparame este mes con el anterior", "period_summary"),
    ("cuánto gasté en octubre", "period_summary"),
    ("qué tal vengo este año vs el pasado", "period_summary"),
    ("dame un resumen del mes pasado", "period_summary"),
    ("estoy ganando más o menos que antes?", "period_summary"),
    # production_estimate: cost by quantity and sales goals
    ("cuánto me cuesta hacer 10 tortas", "production_estimate"),
    ("quiero vender 300000 en la feria dentro de 15 días", "production_estimate"),
    ("necesito juntar 500 mil vendiendo alfajores", "production_estimate"),
    ("cuánta plata de insumos necesito para 50 panes y 20 tortas", "production_estimate"),
    ("me gustaría llegar a 2 millones en la feria del sábado", "production_estimate"),
    ("cuántas tortas tengo que vender para sacar 400000", "production_estimate"),
    ("voy a hacer 30 alfajores, cuánto me sale", "production_estimate"),
    ("qué inversión necesito para vender 1000000", "production_estimate"),
    # financial_recommendation
    ("vendí 5000, cómo lo reparto?", "financial_recommendation"),
    ("cobré 200000 de tortas, qué hago con esa plata", "financial_recommendation"),
    ("me entraron 80 mil, cuánto debería ahorrar", "financial_recommendation"),
    ("cómo distribuyo lo que gané en la feria: 350000", "financial_recommendation"),
    ("tuve una venta de 120000 y quiero saber cuánto reinvertir", "financial_recommendation"),
    # ambiguous but with an expected default
    ("gasté 500 en nafta para ir a la feria", "classification"),
    ("pagué 15000 de insumos para las tortas", "classification"),
    ("cuánto gané con las tortas este mes", "period_summary"),
    ("hola", "classification"),
    ("vendí tortas por 90000 y gasté 30000 en insumos, cómo lo reparto", "financial_recommendation"),
]

# (phrase, expected goal amount or None, expected product names or None,
#  expected [(product, quantity)] or None)
EXTRACTION_CASES: list[tuple[str, Decimal | None, set[str] | None, set[tuple[str, int]] | None]] = [
    ("quiero vender 300000 en la feria", Decimal("300000"), set(), None),
    ("quiero vender 2000000 de alfajores y tortas", Decimal("2000000"), {"alfajor", "torta"}, None),
    # Real follow-up shape: the agent prepends the goal amount to the user's reply.
    ("quiero vender 300000. me gustaría vender tortas y alfajores", Decimal("300000"), {"torta", "alfajor"}, None),
    ("necesito juntar 500 mil vendiendo alfajores", Decimal("500000"), {"alfajor"}, None),
    ("quiero llegar a 1 millón con tortas, alfajores y panes", Decimal("1000000"), {"torta", "alfajor", "pan"}, None),
    ("cuánto me cuesta hacer 10 tortas", None, None, {("torta", 10)}),
    ("voy a hacer 30 alfajores y 12 tortas, cuánto me sale", None, None, {("alfajor", 30), ("torta", 12)}),
    ("cuánta plata necesito para 50 panes", None, None, {("pan", 50)}),
    ("si hago una torta cuánto me cuesta", None, None, {("torta", 1)}),
    ("hola cómo estás", None, None, None),
]


async def evaluate_routing(client: OpenAIToolClient, repeat: int) -> int:
    print(f"== Routing (x{repeat}) ==")
    results = await asyncio.gather(
        *(asyncio.gather(*(client.route_intent(text) for _ in range(repeat))) for text, _ in ROUTING_CASES)
    )
    passed_total = 0
    flaky = 0
    for (text, expected), gots in zip(ROUTING_CASES, results):
        passed = sum(g == expected for g in gots)
        passed_total += passed
        if passed == repeat:
            continue
        flaky += 1
        wrong = sorted({g for g in gots if g != expected})
        print(f"  XX {passed}/{repeat} {text!r:70} esperado={expected} obtuvo={wrong}")
    total = len(ROUTING_CASES) * repeat
    print(f"Routing accuracy: {passed_total}/{total} ({passed_total / total:.0%}); frases con fallos: {flaky}\n")
    return flaky


async def evaluate_extraction(ai: AIService) -> int:
    print("== Extraction (production) ==")
    failures = 0
    for text, goal, names, items in EXTRACTION_CASES:
        parsed = await ai.parse_production_estimate_text(text)
        problems: list[str] = []

        if goal is not None:
            if parsed.sales_goal is None:
                problems.append("no detectó meta de ventas")
            else:
                if goal > 0 and parsed.sales_goal.amount != goal:
                    problems.append(f"monto {parsed.sales_goal.amount} != {goal}")
                if names is not None and set(parsed.sales_goal.product_names) != names:
                    problems.append(f"productos {sorted(parsed.sales_goal.product_names)} != {sorted(names)}")
        elif items is not None:
            got = {(i.product_name, i.quantity) for i in parsed.items}
            if got != items:
                problems.append(f"items {sorted(got)} != {sorted(items)}")
        else:
            if parsed.sales_goal is not None or parsed.items:
                problems.append("debía rechazar el mensaje y extrajo algo")

        failures += bool(problems)
        print(f"  {'OK ' if not problems else 'XX '} {text!r:70}" + ("" if not problems else "  " + "; ".join(problems)))
    total = len(EXTRACTION_CASES)
    print(f"Extraction accuracy: {total - failures}/{total} ({(total - failures) / total:.0%})\n")
    return failures


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", choices=["routing", "extraction"])
    parser.add_argument("--repeat", type=int, default=1, help="runs per routing phrase")
    args = parser.parse_args()

    if not settings.openai_api_key:
        print("OPENAI_API_KEY is not set in .env")
        return 2

    failures = 0
    if args.only != "extraction":
        failures += await evaluate_routing(OpenAIToolClient(api_key=settings.openai_api_key), args.repeat)
    if args.only != "routing":
        # cache=None: every phrase must be a real, independent call.
        failures += await evaluate_extraction(
            AIService(primary=OpenAIProvider(api_key=settings.openai_api_key), fallback=None, cache=None)
        )
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
