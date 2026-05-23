# RFC: Arquitectura y Estrategia Técnica — FinanceAI para Pequeños Negocios

**Autor:** Laura Moyano  
**Fecha:** 2026-05-22  
**Estado:** Borrador  
**Versión:** 1.0.0

---

## Tabla de Contenidos

1. [Contexto y Alcance](#1-contexto-y-alcance)
2. [Decisión Arquitectónica](#2-decisión-arquitectónica)
3. [Stack Tecnológico](#3-stack-tecnológico)
4. [Estructura de Carpetas](#4-estructura-de-carpetas)
5. [Buenas Prácticas Obligatorias](#5-buenas-prácticas-obligatorias)
6. [Estrategia de Testing](#6-estrategia-de-testing)
7. [Observabilidad y Monitoreo](#7-observabilidad-y-monitoreo)
8. [Integración con LLMs](#8-integración-con-llms)
9. [Roadmap Técnico por Fases](#9-roadmap-técnico-por-fases)
10. [Estrategia DevOps](#10-estrategia-devops)
11. [Qué Evitar y Qué Priorizar](#11-qué-evitar-y-qué-priorizar)

---

## 1. Contexto y Alcance

### Descripción del Problema

Los pequeños negocios carecen de herramientas asequibles e inteligentes para gestionar sus finanzas. Las soluciones existentes son costosas, complejas o no integran capacidades de IA que simplifiquen la clasificación y el análisis de transacciones.

### Funcionalidades Requeridas

| Funcionalidad | Prioridad | Complejidad |
|---|---|---|
| Registro de ingresos y gastos | Alta | Baja |
| Autenticación de usuarios | Alta | Media |
| Clasificación automática via LLM | Alta | Alta |
| Dashboards y reportes | Alta | Media |
| Persistencia de datos | Alta | Baja |
| Generación de reportes exportables | Media | Media |
| Análisis predictivo | Baja | Alta |

### Restricciones

- **Equipo:** 1 desarrollador
- **Presupuesto:** Bajo / bajo costo operativo
- **Time-to-market:** Relevante (MVP rápido)
- **Mantenibilidad:** Crítica a largo plazo

---

## 2. Decisión Arquitectónica

### Opciones Evaluadas

#### Opción A: Clean Architecture (Hexagonal)
- **Pros:** Separación estricta, testeable, independiente de frameworks.
- **Contras:** Verbosa, mucho boilerplate, sobreingeniería para un solo desarrollador. Curva de aprendizaje alta. Velocidad de desarrollo baja en etapas tempranas.

#### Opción B: Vertical Slice Architecture (VSA)
- **Pros:** Organización por feature, bajo acoplamiento entre features, fácil de navegar, cada slice es independiente.
- **Contras:** Puede generar duplicación si no se gestiona bien la capa compartida (shared kernel).

#### Opción C: Modular Monolith
- **Pros:** Simple de desplegar, todo en un proceso, comunicación interna sin overhead de red. Módulos bien definidos permiten extraer microservicios después.
- **Contras:** Sin disciplina, puede degenerar en un monolito acoplado.

#### Opción D: Híbrido VSA + Modular Monolith (ELEGIDA)

### Decisión: Modular Monolith con Vertical Slices por Feature

**Justificación técnica:**

```
┌─────────────────────────────────────────────────────────┐
│                    API Layer (HTTP)                      │
├──────────┬──────────┬──────────┬──────────┬─────────────┤
│   Auth   │Transact. │ Reports  │Dashboard │  AI/LLM     │
│  Module  │  Module  │  Module  │  Module  │  Module     │
├──────────┴──────────┴──────────┴──────────┴─────────────┤
│                   Shared Kernel                          │
│  (domain types, utils, error handling, auth middleware)  │
├─────────────────────────────────────────────────────────┤
│               Infrastructure Layer                       │
│         (Database, LLM clients, email, storage)         │
└─────────────────────────────────────────────────────────┘
```

**Por qué esta arquitectura:**

1. **Un solo desarrollador:** VSA permite navegar el código por feature, no por capa. Cuando trabajas en "Transacciones", todo lo relacionado está junto: controller, service, repository, DTOs, tests.

2. **Velocidad + calidad:** Evita el boilerplate excesivo de Clean Architecture sin sacrificar separación de responsabilidades.

3. **Escalabilidad futura:** Los módulos bien delimitados pueden extraerse como microservicios independientes cuando el equipo y la carga crezcan.

4. **Testing natural:** Cada slice tiene su propio conjunto de tests. Las dependencias entre slices son mínimas.

5. **Integración con IA:** El módulo LLM es un slice independiente con su propio cliente, prompts, caché y fallback. El resto de módulos lo consumen como un servicio interno.

6. **Complejidad real del dominio:** El dominio financiero no es excesivamente complejo. No justifica DDD completo ni Event Sourcing. Entidades simples con lógica de negocio clara.

**Principio rector:** *"Make it work, make it right, make it fast"* — en ese orden.

---

## 3. Stack Tecnológico

### Evaluación Comparativa de Backend

| Criterio | Spring Boot (Java) | NestJS (TS) | FastAPI (Python) | Next.js API Routes |
|---|---|---|---|---|
| Productividad (1 dev) | Media | Alta | Alta | Media |
| Curva de aprendizaje | Alta | Media | Baja | Media |
| Integración LLMs | Buena | Buena | Excelente | Básica |
| Testing | Excelente | Buena | Buena | Básica |
| Observabilidad | Excelente | Buena | Buena | Limitada |
| Clean Code | Excelente | Muy Buena | Buena | Media |
| Ecosistema IA/ML | Pobre | Media | Excelente | Pobre |
| Costo operativo | Alto (JVM) | Bajo | Muy Bajo | Bajo |
| Mantenimiento LP | Muy Alto | Alto | Alto | Medio |

### Evaluación Comparativa de Frontend

| Criterio | React (SPA) | Next.js | Remix | Svelte |
|---|---|---|---|---|
| Productividad | Alta | Alta | Media | Alta |
| Ecosistema | Muy Amplio | Amplio | Medio | Medio |
| SSR/SSG | No nativo | Sí | Sí | Sí |
| Complejidad | Media | Media | Alta | Baja |
| Adopción industria | Muy Alta | Alta | Media | Media |

### Stack Recomendado

#### Backend: Python + FastAPI

```
Python 3.12+
FastAPI          — framework web moderno, async nativo, OpenAPI automático
SQLAlchemy 2.0   — ORM async con soporte completo para PostgreSQL
Alembic          — migraciones de base de datos
Pydantic v2      — validación, serialización y DTOs
python-jose      — JWT tokens
passlib + bcrypt — hashing de contraseñas
httpx            — cliente HTTP async (LLM calls)
tenacity         — reintentos con backoff exponencial
structlog        — logging estructurado
prometheus-client — métricas
pytest + pytest-asyncio — testing
```

**Por qué Python sobre Java:**
- Ecosistema IA/ML nativo: las librerías de LLM (LangChain, Anthropic SDK, OpenAI SDK) están en Python primero.
- FastAPI genera documentación OpenAPI automáticamente.
- Menor overhead operativo: pods más pequeños, arranque más rápido.
- Pydantic v2 es compilado en Rust — validación de alto rendimiento.
- Un solo desarrollador puede ser más productivo sin la verbosidad de Java.

**Por qué no NestJS:** TypeScript en backend agrega una capa de complejidad de tooling. Python es más directo para integración con IA.

**Por qué no Spring Boot:** Excelente para equipos grandes con expertise en Java. Para un solo desarrollador, el boilerplate y el overhead de la JVM no justifican los beneficios.

#### Frontend: React + Vite + TypeScript

```
React 19+
TypeScript 5+
Vite             — bundler moderno, HMR rápido
React Router v7  — routing
TanStack Query   — server state, caching, sincronización
TanStack Table   — tablas de datos financieros
Zustand          — client state (mínimo, solo UI state)
Recharts         — gráficos y dashboards
React Hook Form + Zod — formularios con validación
shadcn/ui        — componentes UI (sin vendor lock-in, copy-paste)
Tailwind CSS     — estilos utility-first
Axios / fetch    — HTTP client
Vitest           — unit testing
Playwright       — E2E testing
```

**Por qué React SPA sobre Next.js:**
- No necesitamos SSR para una aplicación financiera autenticada (todo detrás de login).
- Menor complejidad de despliegue: build estático servido desde CDN o Nginx.
- Separación clara frontend/backend facilita el desarrollo independiente.
- Next.js añade complejidad (server components, edge, etc.) innecesaria para este caso.

#### Base de Datos

```
PostgreSQL 16    — base de datos principal (ACID, JSONB, arrays, full-text search)
Redis 7          — caché de respuestas LLM, rate limiting, sesiones
```

**Por qué PostgreSQL:** JSONB permite almacenar metadata de transacciones sin esquema rígido. Soporte nativo para particionamiento cuando el volumen de datos crezca. Extensión `pg_trgm` para búsqueda de texto en descripciones.

#### Infraestructura

```
Docker + Docker Compose — desarrollo local y despliegue
Nginx                   — reverse proxy, servir frontend estático
GitHub Actions          — CI/CD
Railway / Render        — PaaS para despliegue inicial (bajo costo)
Cloudflare              — CDN para frontend, DDoS protection
```

---

## 4. Estructura de Carpetas

### Backend (Python/FastAPI)

```
financeai-backend/
├── src/
│   ├── main.py                         # Entry point FastAPI app
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py                 # Pydantic Settings (env vars)
│   │   └── database.py                 # SQLAlchemy engine + session factory
│   │
│   ├── shared/                         # Shared Kernel — sin dependencias a módulos
│   │   ├── __init__.py
│   │   ├── domain/
│   │   │   ├── base_entity.py          # BaseEntity con id, created_at, updated_at
│   │   │   └── value_objects.py        # Money, Currency, DateRange, etc.
│   │   ├── exceptions/
│   │   │   ├── base.py                 # AppException base
│   │   │   ├── not_found.py
│   │   │   ├── unauthorized.py
│   │   │   └── validation_error.py
│   │   ├── middleware/
│   │   │   ├── error_handler.py        # Global exception handler
│   │   │   ├── logging.py              # Request logging middleware
│   │   │   └── correlation_id.py       # X-Correlation-ID header
│   │   ├── schemas/
│   │   │   ├── response.py             # ApiResponse[T], PaginatedResponse[T]
│   │   │   └── pagination.py           # PaginationParams
│   │   └── utils/
│   │       ├── datetime_utils.py
│   │       └── pagination.py
│   │
│   ├── modules/
│   │   ├── auth/                       # Vertical Slice: Autenticación
│   │   │   ├── __init__.py
│   │   │   ├── router.py               # FastAPI router
│   │   │   ├── service.py              # Lógica de negocio
│   │   │   ├── repository.py           # Acceso a datos
│   │   │   ├── models.py               # SQLAlchemy models
│   │   │   ├── schemas.py              # Pydantic DTOs (Request/Response)
│   │   │   ├── dependencies.py         # FastAPI dependencies (get_current_user)
│   │   │   └── tests/
│   │   │       ├── test_router.py
│   │   │       ├── test_service.py
│   │   │       └── conftest.py
│   │   │
│   │   ├── transactions/               # Vertical Slice: Transacciones
│   │   │   ├── __init__.py
│   │   │   ├── router.py
│   │   │   ├── service.py
│   │   │   ├── repository.py
│   │   │   ├── models.py
│   │   │   ├── schemas.py
│   │   │   ├── categorizer.py          # Orquesta llamada al módulo LLM
│   │   │   ├── enums.py                # TransactionType, CategoryType
│   │   │   └── tests/
│   │   │       ├── test_router.py
│   │   │       ├── test_service.py
│   │   │       ├── test_categorizer.py
│   │   │       └── conftest.py
│   │   │
│   │   ├── reports/                    # Vertical Slice: Reportes
│   │   │   ├── __init__.py
│   │   │   ├── router.py
│   │   │   ├── service.py
│   │   │   ├── repository.py
│   │   │   ├── schemas.py
│   │   │   ├── exporters/
│   │   │   │   ├── pdf_exporter.py
│   │   │   │   └── csv_exporter.py
│   │   │   └── tests/
│   │   │
│   │   ├── dashboard/                  # Vertical Slice: Dashboard
│   │   │   ├── __init__.py
│   │   │   ├── router.py
│   │   │   ├── service.py              # Agrega datos de otros módulos
│   │   │   ├── schemas.py
│   │   │   └── tests/
│   │   │
│   │   └── ai/                         # Vertical Slice: Integración LLM
│   │       ├── __init__.py
│   │       ├── service.py              # AI service facade
│   │       ├── providers/
│   │       │   ├── base.py             # Protocol/ABC para providers
│   │       │   ├── anthropic.py        # Claude implementation
│   │       │   └── openai.py           # OpenAI fallback
│   │       ├── prompts/
│   │       │   ├── categorization_v1.py
│   │       │   └── categorization_v2.py
│   │       ├── cache.py                # Redis cache para respuestas LLM
│   │       ├── schemas.py
│   │       └── tests/
│   │           ├── test_service.py
│   │           └── test_providers.py
│   │
│   └── infrastructure/
│       ├── __init__.py
│       ├── database/
│       │   ├── migrations/             # Alembic migrations
│       │   └── seed.py                 # Datos de prueba
│       ├── cache/
│       │   └── redis_client.py
│       ├── observability/
│       │   ├── metrics.py              # Prometheus metrics
│       │   ├── tracing.py              # OpenTelemetry setup
│       │   └── health.py              # Health check endpoints
│       └── security/
│           ├── jwt.py
│           └── rate_limiter.py
│
├── tests/
│   ├── integration/                    # Tests de integración con DB real
│   │   ├── conftest.py                 # Setup DB de test
│   │   └── test_transaction_flow.py
│   └── e2e/                           # Tests E2E contra API levantada
│
├── scripts/
│   ├── seed_db.py
│   └── run_migrations.py
│
├── docker/
│   ├── Dockerfile
│   └── Dockerfile.dev
│
├── .env.example
├── .env.test
├── alembic.ini
├── pyproject.toml                      # Dependencias + configuración de tools
└── docker-compose.yml
```

### Frontend (React + Vite + TypeScript)

```
financeai-frontend/
├── public/
│   └── favicon.ico
│
├── src/
│   ├── main.tsx                        # Entry point
│   ├── App.tsx                         # Router setup
│   │
│   ├── features/                       # Organización por feature (espeja el backend)
│   │   ├── auth/
│   │   │   ├── components/
│   │   │   │   ├── LoginForm.tsx
│   │   │   │   └── RegisterForm.tsx
│   │   │   ├── hooks/
│   │   │   │   └── useAuth.ts
│   │   │   ├── api/
│   │   │   │   └── auth.api.ts         # Llamadas HTTP al backend
│   │   │   ├── schemas/
│   │   │   │   └── auth.schema.ts      # Zod schemas para validación
│   │   │   ├── store/
│   │   │   │   └── auth.store.ts       # Zustand store (solo estado de sesión)
│   │   │   └── types/
│   │   │       └── auth.types.ts
│   │   │
│   │   ├── transactions/
│   │   │   ├── components/
│   │   │   │   ├── TransactionList.tsx
│   │   │   │   ├── TransactionForm.tsx
│   │   │   │   ├── TransactionFilters.tsx
│   │   │   │   └── CategoryBadge.tsx
│   │   │   ├── hooks/
│   │   │   │   ├── useTransactions.ts  # TanStack Query hooks
│   │   │   │   └── useCreateTransaction.ts
│   │   │   ├── api/
│   │   │   │   └── transactions.api.ts
│   │   │   ├── schemas/
│   │   │   │   └── transaction.schema.ts
│   │   │   └── types/
│   │   │       └── transaction.types.ts
│   │   │
│   │   ├── dashboard/
│   │   │   ├── components/
│   │   │   │   ├── SummaryCards.tsx
│   │   │   │   ├── ExpenseChart.tsx
│   │   │   │   ├── IncomeChart.tsx
│   │   │   │   └── CategoryBreakdown.tsx
│   │   │   ├── hooks/
│   │   │   │   └── useDashboard.ts
│   │   │   └── api/
│   │   │       └── dashboard.api.ts
│   │   │
│   │   └── reports/
│   │       ├── components/
│   │       │   ├── ReportGenerator.tsx
│   │       │   └── ReportPreview.tsx
│   │       ├── hooks/
│   │       │   └── useReports.ts
│   │       └── api/
│   │           └── reports.api.ts
│   │
│   ├── shared/                         # Componentes y utilidades compartidas
│   │   ├── components/
│   │   │   ├── ui/                     # shadcn/ui components (re-exportados)
│   │   │   │   ├── Button.tsx
│   │   │   │   ├── Input.tsx
│   │   │   │   ├── Card.tsx
│   │   │   │   └── ...
│   │   │   ├── layout/
│   │   │   │   ├── AppLayout.tsx
│   │   │   │   ├── Sidebar.tsx
│   │   │   │   └── TopBar.tsx
│   │   │   ├── ErrorBoundary.tsx
│   │   │   ├── LoadingSpinner.tsx
│   │   │   └── ProtectedRoute.tsx
│   │   ├── hooks/
│   │   │   ├── useDebounce.ts
│   │   │   └── useLocalStorage.ts
│   │   ├── lib/
│   │   │   ├── api-client.ts           # Axios instance con interceptors
│   │   │   ├── query-client.ts         # TanStack Query config
│   │   │   └── utils.ts                # cn(), formatCurrency(), etc.
│   │   └── types/
│   │       ├── api.types.ts            # ApiResponse<T>, PaginatedResponse<T>
│   │       └── common.types.ts
│   │
│   ├── pages/                          # Páginas (thin, solo composición)
│   │   ├── LoginPage.tsx
│   │   ├── DashboardPage.tsx
│   │   ├── TransactionsPage.tsx
│   │   └── ReportsPage.tsx
│   │
│   └── router/
│       └── index.tsx                   # React Router config
│
├── tests/
│   ├── unit/
│   │   └── features/
│   └── e2e/
│       └── transactions.spec.ts        # Playwright
│
├── .env.example
├── .env.development
├── index.html
├── vite.config.ts
├── tsconfig.json
├── tailwind.config.ts
└── package.json
```

---

## 5. Buenas Prácticas Obligatorias

### 5.1 Clean Code y SOLID

**Reglas no negociables:**

```python
# BIEN: Una función, una responsabilidad
async def categorize_transaction(description: str, amount: Decimal) -> Category:
    prompt = build_categorization_prompt(description, amount)
    response = await llm_client.complete(prompt)
    return parse_category(response)

# MAL: Función que hace demasiado
async def process_and_save_transaction(data: dict):
    # valida, guarda, categoriza, notifica, loguea... NO
```

**Principios aplicados:**
- **S** — Cada módulo/clase tiene una sola razón para cambiar.
- **O** — Nuevos providers de LLM se agregan implementando el Protocol, sin modificar código existente.
- **L** — Cualquier provider LLM puede sustituir al base sin romper el sistema.
- **I** — Interfaces pequeñas y específicas (no un `AIService` que hace todo).
- **D** — Los módulos de negocio dependen de abstracciones (Protocol/ABC), no de implementaciones concretas de Anthropic u OpenAI.

### 5.2 DTOs y Validación

```python
# schemas.py — Pydantic v2
from pydantic import BaseModel, Field, field_validator
from decimal import Decimal
from datetime import date
from enum import Enum

class TransactionType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"

class CreateTransactionRequest(BaseModel):
    description: str = Field(min_length=1, max_length=500)
    amount: Decimal = Field(gt=0, decimal_places=2)
    transaction_type: TransactionType
    transaction_date: date
    notes: str | None = Field(default=None, max_length=1000)

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        if v > Decimal("999999999.99"):
            raise ValueError("Amount exceeds maximum allowed value")
        return v

class TransactionResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    description: str
    amount: Decimal
    transaction_type: TransactionType
    category: str | None
    ai_confidence: float | None
    transaction_date: date
    created_at: datetime
```

### 5.3 Manejo de Errores

```python
# shared/exceptions/base.py
class AppException(Exception):
    def __init__(self, message: str, code: str, status_code: int = 400):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)

class TransactionNotFoundException(AppException):
    def __init__(self, transaction_id: uuid.UUID):
        super().__init__(
            message=f"Transaction {transaction_id} not found",
            code="TRANSACTION_NOT_FOUND",
            status_code=404,
        )

# shared/middleware/error_handler.py
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {"code": exc.code, "message": exc.message},
            "correlation_id": request.state.correlation_id,
        },
    )
```

**Respuesta de error estandarizada:**
```json
{
  "error": {
    "code": "TRANSACTION_NOT_FOUND",
    "message": "Transaction abc-123 not found"
  },
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### 5.4 Logging Estructurado

```python
# config/logging.py
import structlog

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    logger_factory=structlog.PrintLoggerFactory(),
)

# Uso en servicios
logger = structlog.get_logger(__name__)

async def create_transaction(self, data: CreateTransactionRequest, user_id: UUID):
    logger.info(
        "creating_transaction",
        user_id=str(user_id),
        amount=str(data.amount),
        type=data.transaction_type,
    )
```

**Log output (JSON):**
```json
{
  "event": "creating_transaction",
  "user_id": "abc-123",
  "amount": "1500.00",
  "type": "expense",
  "correlation_id": "550e8400",
  "timestamp": "2026-05-22T10:30:00Z",
  "level": "info"
}
```

### 5.5 Configuración por Entornos

```python
# config/settings.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # App
    app_name: str = "FinanceAI"
    debug: bool = False
    secret_key: str
    cors_origins: list[str] = []

    # Database
    database_url: str
    database_pool_size: int = 10

    # Redis
    redis_url: str

    # LLM
    anthropic_api_key: str
    openai_api_key: str | None = None
    llm_provider: str = "anthropic"
    llm_cache_ttl_seconds: int = 3600

    # Security
    jwt_secret: str
    jwt_expire_minutes: int = 60
    bcrypt_rounds: int = 12

settings = Settings()
```

### 5.6 Seguridad Básica

- **JWT** con expiración corta (60 min) + refresh tokens.
- **bcrypt** para hashing de contraseñas (rounds >= 12).
- **Rate limiting** por IP y por usuario en endpoints de auth.
- **CORS** configurado explícitamente — nunca `*` en producción.
- **SQL injection**: imposible con SQLAlchemy ORM. Para queries raw, usar `text()` con bind parameters.
- **Secrets en variables de entorno** — nunca hardcodeados ni en logs.
- **HTTPS obligatorio** en producción via Nginx/Cloudflare.
- **Headers de seguridad**: `X-Content-Type-Options`, `X-Frame-Options`, `HSTS`.

### 5.7 Convenciones de Código

**Backend (Python):**
```toml
# pyproject.toml
[tool.ruff]
line-length = 88
select = ["E", "F", "I", "N", "UP", "ANN", "S", "B"]

[tool.mypy]
strict = true
python_version = "3.12"
```

**Frontend (TypeScript):**
```json
// .eslintrc
{
  "extends": ["@typescript-eslint/recommended-strict"],
  "rules": {
    "no-console": "error",
    "@typescript-eslint/no-explicit-any": "error"
  }
}
```

**Convenciones de nombres:**
- Backend: `snake_case` para funciones/variables, `PascalCase` para clases.
- Frontend: `camelCase` para funciones/variables, `PascalCase` para componentes.
- Commits: Conventional Commits (`feat:`, `fix:`, `chore:`, `docs:`, `test:`).
- Ramas: `feature/`, `fix/`, `chore/`.

---

## 6. Estrategia de Testing

### Pirámide de Testing

```
         /\
        /E2E\        — Playwright (5-10 flows críticos)
       /──────\
      /  Integ  \    — pytest + DB real (20-30% de tests)
     /────────────\
    /  Unit Tests   \ — pytest + mocks (60-70% de tests)
   /──────────────────\
```

### 6.1 Unit Tests

```python
# modules/transactions/tests/test_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from decimal import Decimal

class TestTransactionService:
    @pytest.fixture
    def mock_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_ai_service(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_repo, mock_ai_service):
        return TransactionService(repo=mock_repo, ai_service=mock_ai_service)

    @pytest.mark.asyncio
    async def test_create_transaction_calls_categorizer(self, service, mock_ai_service):
        mock_ai_service.categorize.return_value = CategoryResult(
            category="food", confidence=0.95
        )
        data = CreateTransactionRequest(
            description="Almuerzo restaurante",
            amount=Decimal("25.00"),
            transaction_type=TransactionType.EXPENSE,
            transaction_date=date.today(),
        )
        await service.create(data, user_id=uuid4())
        mock_ai_service.categorize.assert_called_once_with(
            description="Almuerzo restaurante", amount=Decimal("25.00")
        )

    @pytest.mark.parametrize("amount,expected_valid", [
        (Decimal("0.01"), True),
        (Decimal("0"), False),
        (Decimal("-1"), False),
        (Decimal("999999999.99"), True),
    ])
    def test_transaction_amount_validation(self, amount, expected_valid):
        if expected_valid:
            request = CreateTransactionRequest(
                description="Test", amount=amount,
                transaction_type=TransactionType.INCOME,
                transaction_date=date.today(),
            )
            assert request.amount == amount
        else:
            with pytest.raises(ValidationError):
                CreateTransactionRequest(
                    description="Test", amount=amount,
                    transaction_type=TransactionType.INCOME,
                    transaction_date=date.today(),
                )
```

### 6.2 Integration Tests

```python
# tests/integration/test_transaction_flow.py
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

@pytest.fixture(scope="session")
async def test_db():
    engine = create_async_engine("postgresql+asyncpg://test:test@localhost/financeai_test")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.mark.asyncio
async def test_create_and_retrieve_transaction(client: AsyncClient, auth_headers):
    # Create
    response = await client.post(
        "/api/v1/transactions",
        json={
            "description": "Pago proveedor",
            "amount": "500.00",
            "transaction_type": "expense",
            "transaction_date": "2026-05-22",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    transaction_id = response.json()["data"]["id"]

    # Retrieve
    response = await client.get(
        f"/api/v1/transactions/{transaction_id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["data"]["description"] == "Pago proveedor"
```

### 6.3 Contract Testing

Usar **Pact** (consumer-driven contracts) si el frontend y backend se desarrollan de forma independiente:

```typescript
// Frontend define el contrato esperado
const transaction = {
  id: like("550e8400-e29b-41d4-a716-446655440000"),
  description: like("Almuerzo"),
  amount: like("25.00"),
  category: like("food"),
};
```

### 6.4 E2E Tests con Playwright

```typescript
// tests/e2e/transactions.spec.ts
import { test, expect } from "@playwright/test";

test("usuario puede registrar un gasto y verlo en el dashboard", async ({ page }) => {
  await page.goto("/login");
  await page.fill('[name="email"]', "test@example.com");
  await page.fill('[name="password"]', "password123");
  await page.click('[type="submit"]');

  await expect(page).toHaveURL("/dashboard");

  await page.click('[data-testid="add-transaction"]');
  await page.fill('[name="description"]', "Compra materiales");
  await page.fill('[name="amount"]', "150.00");
  await page.selectOption('[name="type"]', "expense");
  await page.click('[type="submit"]');

  await expect(page.locator('[data-testid="transaction-list"]')).toContainText("Compra materiales");
});
```

### 6.5 Cobertura y Herramientas

| Layer | Herramienta | Cobertura mínima |
|---|---|---|
| Unit (Backend) | pytest-cov | 80% |
| Unit (Frontend) | Vitest + coverage-v8 | 70% |
| Integration | pytest | Flows críticos |
| E2E | Playwright | 10 flows clave |
| Contract | Pact | Endpoints públicos |

```toml
# pyproject.toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
addopts = "--cov=src --cov-report=html --cov-fail-under=80"
```

---

## 7. Observabilidad y Monitoreo

### Arquitectura de Observabilidad

```
App (FastAPI)
    │
    ├── structlog ────────────────────► Loki (logs estructurados JSON)
    │
    ├── prometheus-client ────────────► Prometheus ──► Grafana (dashboards)
    │
    └── opentelemetry ────────────────► Tempo (distributed tracing)

                    Alertmanager ◄──── Prometheus (alertas)
```

### 7.1 Métricas Clave

```python
# infrastructure/observability/metrics.py
from prometheus_client import Counter, Histogram, Gauge

# Business metrics
transactions_created = Counter(
    "transactions_created_total",
    "Total transactions created",
    ["type", "category"],
)

# LLM metrics
llm_request_duration = Histogram(
    "llm_request_duration_seconds",
    "LLM request duration",
    ["provider", "model", "prompt_version"],
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0],
)

llm_tokens_used = Counter(
    "llm_tokens_used_total",
    "Total LLM tokens consumed",
    ["provider", "model", "direction"],  # direction: input/output
)

llm_cost_usd = Counter(
    "llm_cost_usd_total",
    "Estimated LLM cost in USD",
    ["provider", "model"],
)

llm_cache_hits = Counter(
    "llm_cache_hits_total",
    "LLM cache hit/miss",
    ["result"],  # hit / miss
)

# API metrics
http_request_duration = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration",
    ["method", "endpoint", "status_code"],
)

active_users = Gauge(
    "active_users_current",
    "Currently active users (last 15 min)",
)
```

### 7.2 Health Checks

```python
# infrastructure/observability/health.py
@router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@router.get("/health/detailed")
async def detailed_health(db: AsyncSession = Depends(get_db)):
    checks = {}
    
    # Database
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = {"status": "healthy"}
    except Exception as e:
        checks["database"] = {"status": "unhealthy", "error": str(e)}
    
    # Redis
    try:
        await redis_client.ping()
        checks["redis"] = {"status": "healthy"}
    except Exception as e:
        checks["redis"] = {"status": "unhealthy", "error": str(e)}

    # LLM Provider
    checks["llm"] = await check_llm_connectivity()

    overall = "healthy" if all(
        c["status"] == "healthy" for c in checks.values()
    ) else "degraded"

    return {"status": overall, "checks": checks}
```

### 7.3 Dashboards Grafana (Panels clave)

- **API:** Request rate, error rate, P50/P95/P99 latency, por endpoint.
- **LLM:** Requests/min por modelo, tokens/request, costo/hora, cache hit ratio, tasa de errores.
- **Business:** Transacciones creadas/hora, usuarios activos, distribución por categoría.
- **Infrastructure:** CPU, memoria, conexiones DB activas, tamaño de pool.

### 7.4 Alertas Recomendadas

| Alerta | Condición | Severidad |
|---|---|---|
| API Error Rate | > 5% en 5 min | Critical |
| LLM Cost | > $5/hora | Warning |
| LLM Latency | P95 > 10s | Warning |
| DB Connections | > 80% del pool | Warning |
| Health Check Fails | 3 fallos consecutivos | Critical |

---

## 8. Integración con LLMs

### 8.1 Arquitectura de Desacoplamiento

```python
# modules/ai/providers/base.py
from typing import Protocol

class LLMProvider(Protocol):
    async def complete(
        self,
        prompt: str,
        max_tokens: int = 256,
        temperature: float = 0.0,
    ) -> LLMResponse:
        ...

# modules/ai/providers/anthropic.py
class AnthropicProvider:
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-6"):
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.model = model

    async def complete(self, prompt: str, max_tokens: int = 256, temperature: float = 0.0) -> LLMResponse:
        with llm_request_duration.labels(provider="anthropic", model=self.model, prompt_version="v1").time():
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}],
            )
        
        tokens_in = response.usage.input_tokens
        tokens_out = response.usage.output_tokens
        llm_tokens_used.labels(provider="anthropic", model=self.model, direction="input").inc(tokens_in)
        llm_tokens_used.labels(provider="anthropic", model=self.model, direction="output").inc(tokens_out)
        
        return LLMResponse(
            content=response.content[0].text,
            tokens_input=tokens_in,
            tokens_output=tokens_out,
        )
```

### 8.2 Facade con Fallback y Caché

```python
# modules/ai/service.py
class AIService:
    def __init__(
        self,
        primary: LLMProvider,
        fallback: LLMProvider | None,
        cache: LLMCache,
    ):
        self.primary = primary
        self.fallback = fallback
        self.cache = cache

    async def categorize_transaction(
        self,
        description: str,
        amount: Decimal,
        prompt_version: str = "v2",
    ) -> CategoryResult:
        # 1. Check cache
        cache_key = self._build_cache_key(description, amount)
        cached = await self.cache.get(cache_key)
        if cached:
            llm_cache_hits.labels(result="hit").inc()
            return cached
        llm_cache_hits.labels(result="miss").inc()

        # 2. Build prompt
        prompt = self._build_prompt(description, amount, version=prompt_version)

        # 3. Call primary with fallback
        try:
            response = await self.primary.complete(prompt, max_tokens=128, temperature=0.0)
        except LLMProviderError as e:
            logger.warning("primary_llm_failed", error=str(e), provider="anthropic")
            if self.fallback:
                response = await self.fallback.complete(prompt, max_tokens=128, temperature=0.0)
            else:
                return CategoryResult(category="uncategorized", confidence=0.0, fallback=True)

        # 4. Parse response
        result = self._parse_category(response.content)

        # 5. Cache result
        await self.cache.set(cache_key, result, ttl=3600)

        return result
```

### 8.3 Versionamiento de Prompts

```python
# modules/ai/prompts/categorization_v2.py
SYSTEM_PROMPT = """Eres un asistente especializado en contabilidad para pequeños negocios.
Tu única tarea es clasificar transacciones financieras en una de estas categorías:
food, transport, utilities, supplies, marketing, payroll, rent, equipment, other.

Responde ÚNICAMENTE con un JSON válido con este formato exacto:
{"category": "<categoria>", "confidence": <0.0-1.0>}

No incluyas explicaciones ni texto adicional."""

def build_prompt_v2(description: str, amount: Decimal) -> str:
    return f"""Clasifica esta transacción:
Descripción: {description}
Monto: ${amount}

Responde solo con el JSON."""

PROMPT_VERSION = "v2.1.0"
PROMPT_METADATA = {
    "version": PROMPT_VERSION,
    "created": "2026-05-22",
    "model_tested": "claude-sonnet-4-6",
    "accuracy_eval": 0.94,  # resultado de evaluación offline
}
```

### 8.4 Control de Costos

```python
# Estimación de costos por request (Claude claude-sonnet-4-6)
COST_PER_INPUT_TOKEN = 0.000003   # $3/M tokens
COST_PER_OUTPUT_TOKEN = 0.000015  # $15/M tokens

def estimate_cost(tokens_input: int, tokens_output: int) -> float:
    return (tokens_input * COST_PER_INPUT_TOKEN) + (tokens_output * COST_PER_OUTPUT_TOKEN)
```

**Estrategias de reducción de costo:**
1. **Caché agresivo:** Misma descripción = misma respuesta (Redis, TTL 1h).
2. **Normalización previa:** lowercase, strip, remover caracteres especiales antes de cachear.
3. **Batch processing opcional:** Si el volumen crece, agrupar categorizaciones.
4. **Modelo correcto por tarea:** Claude Haiku para categorización simple, Sonnet para análisis complejos.
5. **Rate limiting por usuario:** Evitar abuso que dispare costos.

### 8.5 Evaluación de Precisión

Mantener un dataset curado de ~200 transacciones reales con categorías correctas. Ejecutar evaluación offline al cambiar prompts:

```python
# scripts/evaluate_prompts.py
async def evaluate_prompt_accuracy(test_dataset: list[EvalCase]) -> EvalResult:
    correct = 0
    for case in test_dataset:
        result = await ai_service.categorize_transaction(case.description, case.amount)
        if result.category == case.expected_category:
            correct += 1
    
    accuracy = correct / len(test_dataset)
    logger.info("prompt_evaluation", accuracy=accuracy, version=PROMPT_VERSION)
    return EvalResult(accuracy=accuracy, total=len(test_dataset), correct=correct)
```

---

## 9. Roadmap Técnico por Fases

### Fase 1: MVP (Semanas 1-6)

**Objetivo:** Producto funcional básico, validable con usuarios reales.

| Tarea | Semana |
|---|---|
| Setup proyecto: repos, Docker, CI básico | 1 |
| Auth: registro, login, JWT, protección de rutas | 1-2 |
| Módulo transacciones: CRUD completo | 2-3 |
| Integración LLM: categorización automática | 3-4 |
| Dashboard básico: totales, gráficos simples | 4-5 |
| Despliegue en Railway/Render | 5-6 |
| Testing: unit + integration básicos | Continuo |

**Criterios de éxito del MVP:**
- Un usuario puede registrarse, crear transacciones y ver un dashboard.
- La categorización automática funciona en < 3 segundos.
- El sistema está desplegado y accesible en producción.

### Fase 2: Versión Intermedia (Semanas 7-14)

| Tarea | Semana |
|---|---|
| Reportes: PDF/CSV con filtros por período | 7-8 |
| Búsqueda y filtros avanzados en transacciones | 8-9 |
| Importación de transacciones (CSV bancario) | 9-10 |
| Categorías personalizadas por usuario | 10-11 |
| Observabilidad: Prometheus + Grafana + alertas | 11-12 |
| Mejora de prompts con feedback de usuarios | 12-13 |
| E2E tests con Playwright | 13-14 |

### Fase 3: Versión Escalable (Semanas 15-24)

| Tarea | Semana |
|---|---|
| Multi-tenant con aislamiento por negocio | 15-16 |
| Análisis de tendencias y predicciones | 17-18 |
| Notificaciones (email, alertas de presupuesto) | 18-19 |
| API pública con rate limiting y API keys | 19-20 |
| Cache de segundo nivel para reportes costosos | 20-21 |
| Optimización de queries con índices y particiones | 21-22 |
| Documentación de API publicada | 22-24 |

### Fase 4: Mejoras Futuras

- **Mobile app** (React Native o PWA).
- **Integración bancaria** (Open Banking APIs).
- **Análisis predictivo** con ML propio (si los datos lo justifican).
- **Asistente conversacional** (chat financiero).
- **Módulo de facturación** electrónica.
- Migración selectiva a **microservicios** si el equipo crece.

---

## 10. Estrategia DevOps

### 10.1 Entornos

| Entorno | Uso | Infraestructura |
|---|---|---|
| `local` | Desarrollo | Docker Compose |
| `staging` | Testing pre-producción | Railway (plan free/hobby) |
| `production` | Usuarios reales | Railway + Cloudflare |

### 10.2 Docker

```dockerfile
# docker/Dockerfile (multi-stage)
FROM python:3.12-slim AS builder
WORKDIR /app
RUN pip install uv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

FROM python:3.12-slim AS runner
WORKDIR /app
RUN adduser --disabled-password --gecos "" appuser
COPY --from=builder /app/.venv /app/.venv
COPY src/ ./src/
USER appuser
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s CMD curl -f http://localhost:8000/health || exit 1
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml (desarrollo local)
services:
  backend:
    build:
      context: ./financeai-backend
      dockerfile: docker/Dockerfile.dev
    volumes:
      - ./financeai-backend/src:/app/src  # hot reload
    env_file: .env
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy

  frontend:
    build: ./financeai-frontend
    volumes:
      - ./financeai-frontend/src:/app/src
    ports:
      - "5173:5173"
    environment:
      - VITE_API_URL=http://localhost:8000

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: financeai
      POSTGRES_USER: financeai
      POSTGRES_PASSWORD: local_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U financeai"]
      interval: 5s
      timeout: 5s
      retries: 5
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

### 10.3 CI/CD con GitHub Actions

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_DB: financeai_test
          POSTGRES_USER: financeai
          POSTGRES_PASSWORD: test_password
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
      redis:
        image: redis:7-alpine
        options: --health-cmd "redis-cli ping"

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install uv
        run: pip install uv
      - name: Install dependencies
        run: uv sync --frozen
        working-directory: financeai-backend
      - name: Lint (ruff)
        run: uv run ruff check src/
        working-directory: financeai-backend
      - name: Type check (mypy)
        run: uv run mypy src/
        working-directory: financeai-backend
      - name: Tests
        run: uv run pytest
        working-directory: financeai-backend
        env:
          DATABASE_URL: postgresql+asyncpg://financeai:test_password@localhost/financeai_test
          REDIS_URL: redis://localhost:6379

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "22"
          cache: "npm"
          cache-dependency-path: financeai-frontend/package-lock.json
      - run: npm ci
        working-directory: financeai-frontend
      - run: npm run lint
        working-directory: financeai-frontend
      - run: npm run type-check
        working-directory: financeai-frontend
      - run: npm run test:coverage
        working-directory: financeai-frontend
      - run: npm run build
        working-directory: financeai-frontend

  deploy:
    needs: [backend-tests, frontend-tests]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to Railway
        run: railway up --service backend
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
```

### 10.4 Despliegue Inicial Recomendado

**Opción A (Recomendada para MVP): Railway**
- Backend FastAPI: Railway service.
- PostgreSQL: Railway managed DB.
- Redis: Railway managed Redis.
- Frontend: Vercel (CDN global gratuito para React SPA).
- **Costo estimado:** ~$10-20/mes.

**Opción B (Más control): VPS**
- DigitalOcean Droplet $12/mes (2GB RAM).
- Nginx como reverse proxy.
- Docker Compose para orquestación.
- Let's Encrypt para HTTPS.
- **Costo estimado:** ~$12-15/mes.

---

## 11. Qué Evitar y Qué Priorizar

### 11.1 Qué Evitar (Sobreingeniería)

| Tecnología / Patrón | Por qué evitarlo |
|---|---|
| **Microservicios desde el inicio** | Overhead operativo enorme para 1 dev. Extraer cuando el dolor sea real. |
| **Event Sourcing / CQRS** | El dominio financiero no justifica esta complejidad en el MVP. |
| **Kubernetes** | Overkill para un solo servicio. Railway/Render manejan orquestación. |
| **GraphQL** | REST es suficiente. GraphQL agrega complejidad de schema y tooling. |
| **Message queues (Kafka/RabbitMQ)** | Un task runner simple (Celery o ARQ) es suficiente. |
| **Multiple databases** | PostgreSQL maneja todo: relacional, JSON, full-text. |
| **DDD completo (Aggregates, Domain Events)** | Demasiado ceremonioso para este dominio. |
| **12-Factor extremo desde día 1** | Adoptar gradualmente según necesidad real. |

### 11.2 Qué Mantener Simple

- **Auth:** JWT + bcrypt. No implementar OAuth propio. Usar Supabase Auth o Auth0 si se complica.
- **Emails:** Un servicio simple como Resend o SendGrid. No servidor de email propio.
- **File storage:** Cloudflare R2 o S3 para PDFs exportados. No implementar almacenamiento propio.
- **Caché:** Redis para LLM y sessions. No implementar caché en memoria complejo.
- **Migrations:** Alembic. Scripts manuales simples al principio, automatizar en CI después.

### 11.3 Decisiones Tempranas Anti-Deuda Técnica

| Decisión | Por qué desde el inicio |
|---|---|
| **Pydantic para todos los DTOs** | Evita inconsistencias de tipos entre capas. Muy difícil de agregar después. |
| **Logging estructurado (JSON) desde el día 1** | Los logs en texto plano no escalan. Imposible agregar retroactivamente. |
| **Conventional Commits** | Permite generar changelogs automáticos y facilita git bisect. |
| **UUID como PK, no integer** | Evita enumeration attacks. Facilita futura distribución. |
| **Correlation IDs en todas las requests** | Esencial para debugging. Trivial de agregar desde el inicio, costoso después. |
| **Versionamiento de API desde v1** | `/api/v1/` evita breaking changes cuando la API evoluciona. |
| **Variables de entorno para todo** | Nunca hardcodear URLs, keys, ni configuraciones. |
| **Tests desde el primer endpoint** | La deuda de tests es la más cara de pagar. |

### 11.4 Balance Arquitectura Limpia vs Velocidad

```
Semana 1-4:  Velocidad > Pureza
             → Escribe código funcional, refactoriza después.
             → Tests para lógica crítica (auth, dinero), no todo.
             → No optimices hasta tener usuarios reales.

Semana 5-12: Equilibrio
             → Aplica principios SOLID cuando hagas cambios.
             → Agrega tests cuando encuentres bugs.
             → Refactoriza cuando el código duele.

Semana 13+:  Calidad > Velocidad
             → Cobertura de tests > 80%.
             → Observabilidad completa.
             → Documentación actualizada.
             → Code review de tus propios PRs (descansa 24h antes de mergear).
```

**Regla de oro:** Si el código hace lo que debe hacer, es correcto. Si es difícil de cambiar, es un problema. Si es difícil de entender, es una deuda. Prioriza en ese orden.

---

## Apéndices

### A. Variables de Entorno Requeridas

```bash
# .env.example
# App
APP_NAME=FinanceAI
DEBUG=false
SECRET_KEY=change-me-in-production
CORS_ORIGINS=["https://app.financeai.com"]

# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/financeai
DATABASE_POOL_SIZE=10

# Redis
REDIS_URL=redis://localhost:6379

# LLM
ANTHROPIC_API_KEY=sk-ant-...
LLM_PROVIDER=anthropic
LLM_CACHE_TTL_SECONDS=3600

# Auth
JWT_SECRET=change-me-in-production
JWT_EXPIRE_MINUTES=60

# Observability
PROMETHEUS_ENABLED=true
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
```

### B. Estimación de Costos Operativos Mensuales

| Servicio | Plan | Costo/mes |
|---|---|---|
| Railway (Backend + DB + Redis) | Hobby | $5-20 |
| Vercel (Frontend CDN) | Free/Pro | $0-20 |
| Anthropic API | Pay-per-use | $5-30* |
| Cloudflare (DNS + CDN) | Free | $0 |
| GitHub (CI/CD) | Free | $0 |
| **Total estimado MVP** | | **$10-70/mes** |

*Estimado para 1,000-10,000 categorizaciones/mes con caché activo.

### C. Decisiones Pendientes (ADRs por tomar)

- [ ] **ADR-001:** ¿Supabase Auth vs JWT propio?
- [ ] **ADR-002:** ¿Celery vs ARQ vs FastAPI BackgroundTasks para tareas asíncronas?
- [ ] **ADR-003:** ¿Almacenamiento de PDFs en DB vs object storage?
- [ ] **ADR-004:** ¿Multi-tenant con row-level security en PostgreSQL vs schemas separados?

---

*Este documento es un artefacto vivo. Actualizar con cada decisión arquitectónica relevante.*
