# Vercel Deployment Guide (Frontend)

This guide covers deploying the Next.js frontend from `apps/web` to Vercel while the backend stays on Azure.

## Target architecture

- Frontend: Vercel (`apps/web`)
- Backend API: Azure App Service (`apps/api`)
- Database: Azure PostgreSQL
- Media: Azure Blob Storage

## Prerequisites

- Azure API is healthy (`/healthz`)
- Azure PostgreSQL migrations are applied (`alembic upgrade head`)
- You know the Azure API HTTPS URL, for example:
  - `https://<your-api-app>.azurewebsites.net`

## Vercel project setup (monorepo)

1. Import the GitHub repository into Vercel.
2. Set the Vercel project **Root Directory** to `apps/web`.
3. Keep framework preset as Next.js.
4. Keep install/build defaults for Next.js in that root.

Notes:
- `apps/web` is configured to install independently (no local `file:../..` dependency).
- You should not need to enable "include files outside root directory" for this frontend deploy.

## Required Vercel environment variables

Set in Vercel for Production (and Preview as needed):

- `NEXT_PUBLIC_API_URL=https://<your-api-app>.azurewebsites.net`

Optional (only if using server-side social route handlers):
- `INSTAGRAM_ACCESS_TOKEN=<token>`
- `INSTAGRAM_USER_ID=<id>`

## Backend CORS alignment

Ensure Azure API includes deployed Vercel domain(s) in `CORS_ORIGINS`, for example:

- `https://<project>.vercel.app`
- `https://<your-custom-frontend-domain>`

Keep localhost origins for local development if needed.

## Deployment flow

1. Push frontend changes to GitHub.
2. Vercel builds/deploys from `apps/web` via Git integration.
3. Validate site behavior against Azure API.

No GitHub Actions workflow is required for frontend deploy when Vercel Git integration is used.

## Smoke test checklist

1. Frontend loads from Vercel URL
2. Public pages render (`/`, `/news`, `/roster`, `/schedule`, `/recruit`)
3. Admin login works
4. Admin announcement/roster/schedule/recruit tooling reaches Azure API
5. No CORS errors in browser console
6. No API calls point at `localhost` in deployed site
