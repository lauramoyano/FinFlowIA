from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import get_db
from src.config.settings import settings
from src.infrastructure.cache.redis_client import get_redis
from src.modules.ai.cache import LLMCache
from src.modules.ai.providers.anthropic import AnthropicProvider
from src.modules.ai.providers.base import LLMProvider
from src.modules.ai.providers.openai import OpenAIProvider
from src.modules.ai.service import AIService
from src.modules.auth.dependencies import get_current_user
from src.modules.auth.models import User
from src.modules.orchestrator.agents.classification_agent import ClassificationAgent
from src.modules.orchestrator.agents.financial_recommendation_agent import FinancialRecommendationAgent
from src.modules.orchestrator.agents.period_summary_agent import PeriodSummaryAgent
from src.modules.orchestrator.agents.production_estimate_agent import ProductionEstimateAgent
from src.modules.orchestrator.conversation_store import ConversationStore
from src.modules.orchestrator.product_memory import ProductMemory
from src.modules.orchestrator.openai_tool_client import OpenAIToolClient
from src.modules.orchestrator.schemas import OrchestratorMessageRequest, OrchestratorMessageResponse
from src.modules.orchestrator.service import OrchestratorService
from src.modules.planning.repository import DistributionTemplateRepository, FinancialRecommendationRepository
from src.modules.planning.schemas import (
    FinancialRecommendationItemResponse,
    FinancialRecommendationResponse,
)
from src.modules.production.repository import ProductionEstimateRepository, ProductRepository
from src.modules.production.schemas import (
    ProductionEstimateItemResponse,
    ProductionEstimateResponse,
    SalesGoalItemResponse,
    SalesGoalResponse,
)
from src.modules.reports.repository import ReportRepository
from src.modules.reports.schemas import PeriodSummaryDataResponse, PeriodSummaryResponse
from src.modules.transactions.categorizer import TransactionTextParser
from src.modules.transactions.repository import TransactionRepository
from src.modules.transactions.schemas import ParsedTransactionResponse
from src.shared.schemas.response import ApiResponse

router = APIRouter(prefix="/orchestrator", tags=["Orchestrator"])


def get_orchestrator_service(
    session: AsyncSession = Depends(get_db),
    redis_client: Redis | None = Depends(get_redis),
) -> OrchestratorService:
    # Same primary/fallback AI provider wiring as transactions/router.py's
    # get_transaction_text_parser — reused here for both agents' AI calls.
    # No DI container in this project, so this block is duplicated rather
    # than shared.
    primary: LLMProvider
    fallback: LLMProvider | None
    if settings.llm_provider == "openai":
        primary = OpenAIProvider(api_key=settings.openai_api_key or "")
        fallback = (
            AnthropicProvider(api_key=settings.anthropic_api_key)
            if settings.anthropic_api_key
            else None
        )
    else:
        primary = AnthropicProvider(api_key=settings.anthropic_api_key)
        fallback = (
            OpenAIProvider(api_key=settings.openai_api_key) if settings.openai_api_key else None
        )

    ai_service = AIService(
        primary=primary,
        fallback=fallback,
        cache=LLMCache(redis_client=redis_client, ttl_seconds=settings.llm_cache_ttl_seconds),
    )
    parser = TransactionTextParser(ai_service=ai_service)
    store = ConversationStore(redis_client=redis_client)
    classification_agent = ClassificationAgent(parser=parser, store=store)
    product_repo = ProductRepository(session)
    estimate_repo = ProductionEstimateRepository(session)
    transaction_repo = TransactionRepository(session)
    # One shared memory so every agent recognises the same products,
    # estimates and past expenses.
    memory = ProductMemory(
        product_repo=product_repo, estimate_repo=estimate_repo, transaction_repo=transaction_repo
    )
    production_estimate_agent = ProductionEstimateAgent(
        ai_service=ai_service,
        product_repo=product_repo,
        estimate_repo=estimate_repo,
        memory=memory,
        store=store,
    )
    financial_recommendation_agent = FinancialRecommendationAgent(
        ai_service=ai_service,
        template_repo=DistributionTemplateRepository(session),
        recommendation_repo=FinancialRecommendationRepository(session),
        transaction_repo=transaction_repo,
        memory=memory,
        store=store,
    )
    period_summary_agent = PeriodSummaryAgent(
        ai_service=ai_service,
        report_repo=ReportRepository(session),
        store=store,
    )
    # Tool-calling-based routing is OpenAI-only by design, independent of
    # settings.llm_provider (which picks the primary for plain-text completion).
    tool_client = OpenAIToolClient(api_key=settings.openai_api_key or "")

    return OrchestratorService(
        tool_client=tool_client,
        conversation_store=store,
        classification_agent=classification_agent,
        production_estimate_agent=production_estimate_agent,
        financial_recommendation_agent=financial_recommendation_agent,
        period_summary_agent=period_summary_agent,
    )


@router.post(
    "/message",
    response_model=ApiResponse[OrchestratorMessageResponse],
    summary="Send a chat message to the orchestrator; routes it to the right agent",
)
async def send_message(
    request: OrchestratorMessageRequest,
    current_user: User = Depends(get_current_user),
    service: OrchestratorService = Depends(get_orchestrator_service),
) -> ApiResponse[OrchestratorMessageResponse]:
    conversation_id, result = await service.handle_message(
        text=request.text, conversation_id=request.conversation_id, user_id=current_user.id
    )

    draft = None
    if result.draft is not None:
        draft = ParsedTransactionResponse(
            description=result.draft.description,
            amount=result.draft.amount,
            transaction_type=result.draft.transaction_type,
            transaction_date=result.draft.transaction_date,
            category=result.draft.category,
            confidence=result.draft.confidence,
            error=result.draft.error,
        )

    estimate = None
    if result.estimate is not None:
        estimate = ProductionEstimateResponse(
            items=[
                ProductionEstimateItemResponse(
                    product_name=item.product_name,
                    quantity=item.quantity,
                    unit_cost=item.unit_cost,
                    subtotal=item.subtotal,
                )
                for item in result.estimate.items
            ],
            total_estimated_cost=result.estimate.total_estimated_cost,
            projected_revenue=result.estimate.projected_revenue,
            estimated_profit=result.estimate.estimated_profit,
        )

    sales_goal = None
    if result.sales_goal_result is not None:
        sg = result.sales_goal_result
        sales_goal = SalesGoalResponse(
            goal_amount=sg.goal_amount,
            items=[
                SalesGoalItemResponse(
                    product_name=i.product_name,
                    quantity_needed=i.quantity_needed,
                    unit_sale_price=i.unit_sale_price,
                    unit_insumos_cost=i.unit_insumos_cost,
                    insumos_investment=i.insumos_investment,
                    projected_revenue=i.projected_revenue,
                    estimated_profit=i.estimated_profit,
                )
                for i in sg.items
            ],
            insumos_investment=sg.insumos_investment,
            projected_revenue=sg.projected_revenue,
            estimated_profit=sg.estimated_profit,
        )

    financial_recommendation = None
    if result.financial_recommendation_result is not None:
        fr = result.financial_recommendation_result
        financial_recommendation = FinancialRecommendationResponse(
            items=[
                FinancialRecommendationItemResponse(
                    label=item.label, amount=item.amount, percentage=item.percentage
                )
                for item in fr.items
            ],
            sale_amount=fr.sale_amount,
            total_costs=fr.total_costs,
            net_amount=fr.net_amount,
            estimated_savings=fr.estimated_savings,
            estimated_business_balance=fr.estimated_business_balance,
            pending_debt_total=fr.pending_debt_total,
            insumos_linked_products=fr.insumos_linked_products,
        )

    period_summary = None
    if result.period_summary_result is not None:
        ps = result.period_summary_result
        previous = None
        if ps.previous is not None:
            previous = PeriodSummaryDataResponse(
                label=ps.previous.label,
                start_date=ps.previous.start_date,
                end_date=ps.previous.end_date,
                total_income=ps.previous.total_income,
                total_expenses=ps.previous.total_expenses,
                balance=ps.previous.balance,
            )
        period_summary = PeriodSummaryResponse(
            current=PeriodSummaryDataResponse(
                label=ps.current.label,
                start_date=ps.current.start_date,
                end_date=ps.current.end_date,
                total_income=ps.current.total_income,
                total_expenses=ps.current.total_expenses,
                balance=ps.current.balance,
            ),
            previous=previous,
        )

    return ApiResponse(
        data=OrchestratorMessageResponse(
            conversation_id=conversation_id,
            kind=result.kind,
            message=result.message,
            message_params=result.message_params,
            draft=draft,
            estimate=estimate,
            sales_goal=sales_goal,
            financial_recommendation=financial_recommendation,
            period_summary=period_summary,
            agent=result.agent,
            error_code=result.error_code,
        )
    )
