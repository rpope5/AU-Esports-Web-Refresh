# AU Esports Platform (Capstone)

A full-stack platform for Ashland University Esports:
- Hype/news page + media
- Team rosters and player profiles
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
