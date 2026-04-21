# API (FastAPI)

## Local development

1. Create/install dependencies:
   - `python -m venv .venv`
   - `.venv\Scripts\pip install -r requirements.txt` (Windows)
2. Start API:
   - `.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000`
3. Local defaults:
   - `DATABASE_URL=sqlite:///./dev.db`
   - `MEDIA_BACKEND=local`

## Production startup (Azure App Service Linux)

- Startup command:
  - `bash startup.sh`
- App server:
  - `gunicorn -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:$PORT`

## Database migrations

- Production migration command:
  - `alembic upgrade head`
- Optional startup migration gate:
  - `RUN_DB_MIGRATIONS_ON_STARTUP=true`

## Key environment variables

- `APP_ENV` (`development` or `production`)
- `DATABASE_URL` (PostgreSQL in production, SQLite for local)
- `CORS_ORIGINS` (comma-separated frontend origins, including your Vercel domain in production)
- `JWT_SECRET`
- `MEDIA_BACKEND` (`local` or `azure_blob`)
- `MEDIA_AZURE_BLOB_CONNECTION_STRING` (required when `MEDIA_BACKEND=azure_blob`)
- `MEDIA_AZURE_BLOB_CONTAINER`

## Deployment model

- Frontend is deployed on Vercel from `apps/web`
- Backend remains on Azure App Service from `apps/api`
- See `../../docs/DEPLOY_AZURE.md` for backend/data deployment
- See `../../docs/DEPLOY_VERCEL.md` for frontend deployment and API wiring
