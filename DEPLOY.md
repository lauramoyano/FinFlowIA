# Despliegue

Frontend en Vercel; backend (Docker) en Render o Railway; Postgres en Neon; Redis en Upstash.
Los secretos se pegan solo en los paneles de cada servicio, nunca en el repositorio.

## 1. Base de datos y Redis
- **Neon**: crear proyecto y copiar la connection string (`postgresql://...`). Se convierte sola a asyncpg.
- **Upstash**: crear base Redis y copiar la URL `rediss://...`.

## 2. Backend (Render, Web Service con Docker)
- Root directory: `FinFlowIA-Backend`
- Dockerfile path: `docker/Dockerfile`
- Health check path: `/health`
- Variables de entorno:
  - `DATABASE_URL`, `REDIS_URL`
  - `OPENAI_API_KEY`, `LLM_PROVIDER=openai`
  - `JWT_SECRET`, `SECRET_KEY` (cadenas largas aleatorias; `openssl rand -hex 32`)
  - `CORS_ORIGINS` = URL de Vercel, separada por comas si hay varias
- Las migraciones (`alembic upgrade head`) corren solas en cada arranque.

## 3. Frontend (Vercel)
- Root directory: `FinFlowIA-Frontend`, framework Vite.
- Variable: `VITE_API_URL` = URL pública del backend (sin `/` final).
- `vercel.json` ya redirige las rutas de React Router a `index.html`.

## 4. Usuario demo (opcional)
Registrarse desde la app, o ejecutar `python -m src.infrastructure.database.seed`
con `DATABASE_URL` apuntando a producción.
