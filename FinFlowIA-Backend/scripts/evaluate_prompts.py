"""
Offline prompt/model accuracy evaluation — RFC section 8.5 ("Evaluación de
Precisión").

Runs every row of a labeled CSV dataset (description, amount, transaction_type,
expected_category) through the real categorization pipeline (AIService ->
provider -> prompt v2) and reports accuracy, a confusion breakdown, and
average confidence — split by correct vs incorrect predictions.

Usage:
    # Real evaluation against Claude Haiku (needs ANTHROPIC_API_KEY in .env)
    python scripts/evaluate_prompts.py

    # Evaluate against the OpenAI fallback provider instead
    python scripts/evaluate_prompts.py --provider openai

    # Smoke-test the evaluation harness itself with no API key / no network,
    # using a deterministic keyword-matching fake provider
    python scripts/evaluate_prompts.py --provider dry-run

    # Quick sample instead of the full dataset
    python scripts/evaluate_prompts.py --limit 25

Caching is intentionally disabled (redis_client=None) so every row is a real,
independent categorization call — this is an accuracy measurement, not a
cost/latency benchmark (that's covered by the llm_* Prometheus metrics in
normal operation, see RFC section 7).
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import re
import sys
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

DEFAULT_DATASET = Path(__file__).parent.parent / "data" / "synthetic" / "eval_dataset.csv"


class DryRunProvider:
    """
    Deterministic, offline stand-in for a real LLM provider.

    Guesses a category via keyword matching so the evaluation harness
    (dataset loading, scoring, reporting) can be exercised and verified
    without an API key, network access, or incurring any cost. Do not use
    this to draw conclusions about real model accuracy — swap in
    AnthropicProvider/OpenAIProvider for that.
    """

    KEYWORDS: dict[str, list[str]] = {
        "food": ["almuerzo", "cena", "café", "snack", "desayuno", "catering"],
        "transport": ["combustible", "taxi", "peaje", "vehículo", "uber", "parqueadero", "courier"],
        "utilities": ["electricidad", "internet", "agua", "gas", "telefonía", "recarga"],
        "supplies": ["papelería", "limpieza", "embalaje", "resmas", "insumos", "tinta"],
        "marketing": ["publicidad", "ads", "folletos", "banners", "influencer", "fotografía"],
        "payroll": ["sueldo", "nómina", "aguinaldo", "horas extra"],
        "rent": ["alquiler", "renta", "bodega"],
        "equipment": ["laptop", "software", "impresora", "mobiliario", "pos"],
        "sales": ["venta", "pedido"],
        "services": ["honorarios", "consultoría", "capacitación", "diseño gráfico", "asesoría"],
    }

    async def complete(
        self,
        prompt: str,
        max_tokens: int = 128,
        temperature: float = 0.0,
    ) -> object:
        from src.modules.ai.providers.base import LLMResponse

        match = re.search(r"Descripci[oó]n:\s*(.+)", prompt)
        description = match.group(1).lower() if match else ""

        category = "other"
        for cat, keywords in self.KEYWORDS.items():
            if any(kw in description for kw in keywords):
                category = cat
                break

        content = f'{{"category": "{category}", "confidence": 0.9}}'
        return LLMResponse(
            content=content,
            tokens_input=len(prompt) // 4,
            tokens_output=len(content) // 4,
            model="dry-run",
            provider="dry-run",
        )


def load_dataset(path: Path, limit: int | None) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if limit:
        rows = rows[:limit]
    return rows


def build_ai_service(provider_name: str):  # noqa: ANN201
    from src.modules.ai.cache import LLMCache
    from src.modules.ai.service import AIService

    if provider_name == "dry-run":
        primary = DryRunProvider()
    else:
        from src.config.settings import settings

        if provider_name == "anthropic":
            from src.modules.ai.providers.anthropic import AnthropicProvider

            primary = AnthropicProvider(api_key=settings.anthropic_api_key)
        elif provider_name == "openai":
            from src.modules.ai.providers.openai import OpenAIProvider

            if not settings.openai_api_key:
                raise SystemExit("OPENAI_API_KEY is not set; cannot evaluate the openai provider.")
            primary = OpenAIProvider(api_key=settings.openai_api_key)
        else:
            raise SystemExit(f"Unknown provider: {provider_name}")

    return AIService(primary=primary, fallback=None, cache=LLMCache(redis_client=None))


async def evaluate(
    dataset: list[dict[str, str]],
    ai_service,  # noqa: ANN001
    concurrency: int,
) -> dict:
    semaphore = asyncio.Semaphore(concurrency)
    results: list[dict] = []

    async def run_one(row: dict[str, str]) -> None:
        async with semaphore:
            result = await ai_service.categorize_transaction(
                description=row["description"],
                amount=Decimal(row["amount"]),
            )
            results.append(
                {
                    "description": row["description"],
                    "expected": row["expected_category"],
                    "predicted": result.category,
                    "confidence": result.confidence,
                    "correct": result.category == row["expected_category"],
                }
            )

    await asyncio.gather(*(run_one(row) for row in dataset))

    correct = sum(1 for r in results if r["correct"])
    total = len(results)
    accuracy = correct / total if total else 0.0

    per_category_total: Counter[str] = Counter()
    per_category_correct: Counter[str] = Counter()
    confusions: defaultdict[tuple[str, str], int] = defaultdict(int)
    confidences_correct: list[float] = []
    confidences_incorrect: list[float] = []

    for r in results:
        per_category_total[r["expected"]] += 1
        if r["correct"]:
            per_category_correct[r["expected"]] += 1
            confidences_correct.append(r["confidence"])
        else:
            confusions[(r["expected"], r["predicted"])] += 1
            confidences_incorrect.append(r["confidence"])

    return {
        "total": total,
        "correct": correct,
        "accuracy": accuracy,
        "per_category_total": per_category_total,
        "per_category_correct": per_category_correct,
        "confusions": confusions,
        "avg_confidence_correct": (
            sum(confidences_correct) / len(confidences_correct) if confidences_correct else 0.0
        ),
        "avg_confidence_incorrect": (
            sum(confidences_incorrect) / len(confidences_incorrect) if confidences_incorrect else 0.0
        ),
        "misclassified": [r for r in results if not r["correct"]],
    }


def print_report(report: dict, provider_name: str) -> None:
    print()
    print("=" * 60)
    print(f"  Prompt evaluation — provider: {provider_name}")
    print("=" * 60)
    print(f"Total cases:        {report['total']}")
    print(f"Correct:            {report['correct']}")
    print(f"Accuracy:           {report['accuracy']:.2%}")
    print(f"Avg confidence (correct predictions):   {report['avg_confidence_correct']:.2f}")
    print(f"Avg confidence (incorrect predictions): {report['avg_confidence_incorrect']:.2f}")

    print("\nPer-category accuracy:")
    for category in sorted(report["per_category_total"]):
        total = report["per_category_total"][category]
        correct = report["per_category_correct"].get(category, 0)
        acc = correct / total if total else 0.0
        print(f"  {category:<12} {correct:>4}/{total:<4} ({acc:.1%})")

    if report["confusions"]:
        print("\nTop confusions (expected -> predicted):")
        top = sorted(report["confusions"].items(), key=lambda kv: -kv[1])[:10]
        for (expected, predicted), count in top:
            print(f"  {expected:<12} -> {predicted:<12} x{count}")

    print()
    if report["accuracy"] >= 0.90:
        print("Result: meets the RFC target (>= 90% accuracy, see PROMPT_METADATA in categorization_v2.py).")
    else:
        print("Result: below the RFC target of 90% accuracy — consider revising the prompt or the model.")
    print("=" * 60)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET, help="Path to labeled CSV dataset")
    parser.add_argument(
        "--provider",
        choices=["anthropic", "openai", "dry-run"],
        default="anthropic",
        help="Which provider to evaluate (default: anthropic / Claude Haiku)",
    )
    parser.add_argument("--limit", type=int, default=None, help="Evaluate only the first N rows")
    parser.add_argument("--concurrency", type=int, default=5, help="Max concurrent categorization calls")
    args = parser.parse_args()

    if not args.dataset.exists():
        raise SystemExit(
            f"Dataset not found at {args.dataset}. "
            "Generate it first with: python scripts/generate_eval_dataset.py"
        )

    dataset = load_dataset(args.dataset, args.limit)
    ai_service = build_ai_service(args.provider)

    report = asyncio.run(evaluate(dataset, ai_service, args.concurrency))
    print_report(report, args.provider)


if __name__ == "__main__":
    main()
