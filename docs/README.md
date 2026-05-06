# AU Esports Platform (Capstone)

A full-stack platform for Ashland University Esports:
- Hype/news page + media
- Team rosters and player profiles
- Staff & leadership directory with coach profile pages (`/staff`, `/staff/[slug]`)
- Schedules and results
- Recruiting form + coach/admin dashboard
- Future: AI-assisted recruiting + recap generation

## Tech Stack
- **Frontend:** Next.js (TypeScript, Tailwind) on Vercel
- **Backend:** FastAPI (Python) on Azure App Service (Linux)
- **Database (local dev):** SQLite
- **Database (production):** Azure Database for PostgreSQL Flexible Server
- **Media (production):** Azure Blob Storage

## Repo Structure
- `apps/web` - Next.js frontend
- `apps/api` - FastAPI backend
- `docs` - deployment and project documentation

## Staff Directory APIs
- `GET /api/v1/staff` (public active profiles, optional `category` and `game` filters)
- `GET /api/v1/staff/{slug}` (public active profile detail)
- `GET /api/v1/admin/staff` (admin/staff-authenticated full list)
- `POST /api/v1/admin/staff` (admin create)
- `PATCH /api/v1/admin/staff/{staff_id}` (admin update)
- `DELETE /api/v1/admin/staff/{staff_id}` (admin deactivate)

## Local Tooling
- Package manager: `npm`
- Root `package.json` provides orchestration scripts; frontend dependencies are installed in `apps/web` (not hoisted at repo root)
- Typical frontend commands from repo root:
  - `npm run install:web`
  - `npm run dev:web`
  - `npm run build:web`

## Deployment Docs

- [Frontend Deployment (Vercel)](./DEPLOY_VERCEL.md)
- [Backend/Data Deployment (Azure)](./DEPLOY_AZURE.md)

## Recruiting Docs

- [Recruit Scoring System (Capstone)](./recruit-scoring-system.md)
- [Recruit Triage Playbook (Phase 1)](./recruit-triage-playbook.md)
