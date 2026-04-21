# Azure Deployment Guide (Backend + Data Services)

This guide covers the Azure-hosted parts of the platform.

## Target architecture

- Frontend: Vercel (`apps/web`)
- Backend: Azure App Service for Linux (`apps/api`)
- Database: Azure Database for PostgreSQL Flexible Server
- Media: Azure Blob Storage
- Source control/CI: GitHub

If you need frontend deploy steps, use `docs/DEPLOY_VERCEL.md`.

## Scope in Azure

Azure currently hosts:
- FastAPI backend (`apps/api`)
- PostgreSQL database
- Blob storage for uploaded media

Azure no longer hosts the frontend deployment target.

## Required Azure resources

1. Resource Group
2. App Service Plan (Linux)
3. Web App (Linux, Python 3.11)
4. Azure Database for PostgreSQL Flexible Server + database
5. Storage Account + Blob Container (recommended for durable media)

## Backend environment variables (`apps/api`)

Use `apps/api/.env.example` as baseline.

Required in production:
- `APP_ENV=production`
- `DATABASE_URL=postgresql://<user>:<pass>@<host>:5432/<db>?sslmode=require`
- `CORS_ORIGINS=https://<your-vercel-domain>,https://<your-custom-frontend-domain-if-any>`
- `JWT_SECRET=<long random secret>`

Recommended:
- `AUTO_CREATE_TABLES=false`
- `RUN_DB_MIGRATIONS_ON_STARTUP=false` (run migrations in controlled release steps)
- `ENABLE_DEBUG_ROUTES=false`

Media options:
- Local disk (not durable): `MEDIA_BACKEND=local`
- Durable blob storage: `MEDIA_BACKEND=azure_blob` plus:
  - `MEDIA_AZURE_BLOB_CONNECTION_STRING=...`
  - `MEDIA_AZURE_BLOB_CONTAINER=au-esports-media`

Graph integration (only if used):
- `AZURE_TENANT_ID`
- `AZURE_CLIENT_ID`
- `AZURE_CLIENT_SECRET`
- `AZURE_GROUP_ID`
- `REDIRECT_URI`

## Migration process

From `apps/api` with production `DATABASE_URL` set:

- `alembic upgrade head`

Recommended release sequencing:
1. Deploy backend code
2. Run migrations
3. Verify `GET /healthz`
4. Deploy/validate frontend in Vercel

## GitHub Actions (backend)

Workflow file:
- `.github/workflows/deploy-api-azure.yml`

Behavior:
- Triggers on `main` changes to `apps/api/**` and backend deploy docs
- Uses Azure OIDC login (`azure/login@v2`)
- Zip-deploys `apps/api` to App Service
- Sets startup command to `bash startup.sh`

Required GitHub secrets:
- `AZURE_CLIENT_ID`
- `AZURE_TENANT_ID`
- `AZURE_SUBSCRIPTION_ID`
- `AZURE_API_RESOURCE_GROUP`
- `AZURE_API_APP_NAME`

## Frontend alignment requirements

To work with a Vercel-hosted frontend:
- Add the deployed Vercel domain(s) to `CORS_ORIGINS`
- Keep `NEXT_PUBLIC_API_URL` in Vercel set to the Azure API HTTPS URL
- If Graph auth flow is used, ensure Entra redirect URIs match deployed callback URL(s)

## Post-deploy smoke test checklist

1. `GET https://<api>/healthz` returns `{ "status": "ok" }`
2. Frontend loads from Vercel and reads from Azure API
3. Recruit form submission succeeds
4. Admin login/whoami succeeds
5. Announcements CRUD works
6. Roster CRUD works
7. Schedule workflows work
8. Uploaded media renders (news + roster)
9. No browser CORS errors for frontend/API calls

## Common failure points

- `CORS_ORIGINS` missing Vercel production domain
- `NEXT_PUBLIC_API_URL` not set to Azure API HTTPS URL
- `DATABASE_URL` not set to PostgreSQL in production
- Blob settings missing while `MEDIA_BACKEND=azure_blob`
- Graph redirect URI mismatch with `REDIRECT_URI`
