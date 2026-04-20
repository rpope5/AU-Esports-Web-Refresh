# Azure Deployment Guide (AU Esports Monorepo)

## Target architecture

- Frontend: Azure Static Web Apps (`apps/web`)
- Backend: Azure App Service for Linux (`apps/api`, FastAPI + Gunicorn)
- Database: Azure Database for PostgreSQL Flexible Server
- Optional media persistence: Azure Blob Storage (for announcement images + roster headshots)

This deployment path covers all currently implemented modules:
- public pages
- recruit apply + recruit admin flows
- announcements/news module
- roster module
- schedule module
- admin auth, role permissions, and protected routes

## Recommended Azure sizing (starting point)

- App Service Plan: Basic B1 (upgrade to B2/B3 if API traffic grows)
- App Service runtime: Python 3.11 (Linux)
- PostgreSQL Flexible Server: Burstable B1ms for dev/staging, General Purpose for production traffic
- Static Web Apps: Standard tier if you need custom auth roles/features beyond free-tier limits

## What changed for Azure readiness

- API runtime is env-driven (`apps/api/app/core/config.py`)
- Production Postgres URL normalization is built in (`postgres://` and `postgresql://` -> psycopg driver)
- Alembic now supports production DB URL from environment and no longer forces SQLite batch mode on Postgres
- Full schema bootstrap migration added so `alembic upgrade head` builds the active module set
- API startup script added (`apps/api/startup.sh`) for App Service Linux
- Optional startup migration gate: `RUN_DB_MIGRATIONS_ON_STARTUP=true`
- Debug routes are disabled by default (`ENABLE_DEBUG_ROUTES=false`)
- Upload/media backend supports:
  - local filesystem (dev/default)
  - Azure Blob (`MEDIA_BACKEND=azure_blob`)
- Upload static mount path now aligns with write path (`apps/api/uploads`)

## Required Azure resources

1. Resource Group
2. App Service Plan (Linux)
3. Web App (Linux, Python 3.11)
4. Azure Database for PostgreSQL Flexible Server + database
5. Azure Static Web App
6. Optional but recommended for persistent media:
   - Storage Account
   - Blob Container (for `MEDIA_AZURE_BLOB_CONTAINER`)

## Environment variables

### Backend (`apps/api`)

Use `apps/api/.env.example` as source of truth.

Required in production:
- `APP_ENV=production`
- `DATABASE_URL=postgresql://<user>:<pass>@<host>:5432/<db>?sslmode=require`
- `CORS_ORIGINS=https://<your-swa-domain>,https://<your-custom-domain>`
- `JWT_SECRET=<long random secret>`

Recommended:
- `AUTO_CREATE_TABLES=false`
- `RUN_DB_MIGRATIONS_ON_STARTUP=false` (run migrations in a controlled release step)
- `ENABLE_DEBUG_ROUTES=false`

Media options:
- Local (not persistent across scale/redeploy): `MEDIA_BACKEND=local`
- Persistent (recommended): `MEDIA_BACKEND=azure_blob` plus:
  - `MEDIA_AZURE_BLOB_CONNECTION_STRING=...`
  - `MEDIA_AZURE_BLOB_CONTAINER=au-esports-media`

Graph integration (only if used):
- `AZURE_TENANT_ID`
- `AZURE_CLIENT_ID`
- `AZURE_CLIENT_SECRET`
- `AZURE_GROUP_ID`
- `REDIRECT_URI`

### Frontend (`apps/web`)

Use `apps/web/.env.example`.

Required:
- `NEXT_PUBLIC_API_URL=https://<your-api-app>.azurewebsites.net`

Optional server-route vars:
- `INSTAGRAM_ACCESS_TOKEN`
- `INSTAGRAM_USER_ID`

## Database migration process

Primary production migration path:
1. Set `DATABASE_URL` to Azure PostgreSQL
2. From `apps/api`: `alembic upgrade head`

Recommended release sequencing:
1. Deploy backend code
2. Run migrations
3. Verify `/healthz`
4. Deploy frontend

If you opt in to startup migrations:
- set `RUN_DB_MIGRATIONS_ON_STARTUP=true`
- startup script will run `alembic upgrade head` before Gunicorn starts

## GitHub Actions workflows

### Backend workflow
- File: `.github/workflows/deploy-api-azure.yml`
- Trigger: `main` branch changes under `apps/api/**` (or manual dispatch)
- Uses Azure OIDC login (`azure/login@v2`)
- Zip deploys `apps/api` to App Service
- Sets startup command to `bash startup.sh`

Required GitHub secrets:
- `AZURE_CLIENT_ID`
- `AZURE_TENANT_ID`
- `AZURE_SUBSCRIPTION_ID`
- `AZURE_API_RESOURCE_GROUP`
- `AZURE_API_APP_NAME`

### Frontend workflow
- File: `.github/workflows/deploy-web-azure-swa.yml`
- Trigger: `main` branch changes under `apps/web/**` (or manual dispatch)
- Uses `Azure/static-web-apps-deploy@v1`

Required GitHub secret:
- `AZURE_STATIC_WEB_APPS_API_TOKEN`

## Azure auth setup notes

Backend deploy uses OIDC:
1. Create an Entra ID app registration for GitHub Actions
2. Add federated credentials for your repo/branch
3. Grant deployment permissions (Contributor or scoped role) to the Resource Group or Web App

Frontend SWA deploy currently uses deployment token secret (action requirement).

## OAuth / callback alignment

If using Graph consent flow endpoints:
- `REDIRECT_URI` must match your deployed API callback URL
- Update allowed redirect URIs in Entra app registration

For admin/frontend auth behavior:
- ensure frontend domain is included in API `CORS_ORIGINS`
- keep JWT secret strong and private per environment

## Startup command

App Service startup command:
- `bash startup.sh`

Script location:
- `apps/api/startup.sh`

## Domain and HTTPS notes

- Prefer custom domain on Static Web Apps for public frontend
- Use HTTPS-only mode on App Service
- Keep `NEXT_PUBLIC_API_URL` on HTTPS endpoint
- Keep CORS origins HTTPS-only in production

## Uploads, images, and placeholders

- Bundled placeholders/static assets in `apps/web/public` are safe on SWA
- Admin-uploaded announcement images and roster headshots are user-managed media
- Local disk (`MEDIA_BACKEND=local`) is acceptable for dev, but not durable for scaled production
- For durable production media, use `MEDIA_BACKEND=azure_blob`

## Post-deploy smoke test checklist

1. `GET https://<api>/healthz` returns `{"status":"ok"}`
2. Frontend loads and reads from deployed API URL
3. Recruit form submission succeeds
4. Admin login succeeds
5. Admin whoami returns expected role/permission payload
6. Announcements list/create/edit/delete works
7. Roster list/create/edit/delete works
8. Schedule list/create/workflow actions/delete works
9. Uploaded images render correctly (news + roster)
10. CORS errors are absent in browser console for frontend/API calls

## Common failure points

- `DATABASE_URL` not set to Postgres in production
- CORS origin missing deployed SWA/custom domain
- `JWT_SECRET` left unset/weak
- Blob vars missing while `MEDIA_BACKEND=azure_blob`
- Graph redirect URI mismatch with `REDIRECT_URI`
- Running deploy before DB migration

## Rollback guidance

1. Roll back code by redeploying prior known-good commit
2. If migration introduced an issue, restore from DB backup and redeploy matching app version
3. Keep media container intact; do not delete blob data during code rollback
4. Validate `/healthz`, admin login, and recruit submission after rollback
