## Quickstart (Windows)

### 1) Requirements
- Node.js 20+
- Python 3.11+

### 2) Clone and set env files
```bash
git clone <REPO_URL>
cd au-esports-platform

---

### 3) Optional but recommended: `CONTRIBUTING.md`
Create `CONTRIBUTING.md` at repo root:

```md
# Contributing Guide

## Workflow
1. Pull latest `dev`
2. Create a feature branch: `feat/<area>-<desc>`
3. Commit small, clear changes
4. Open a PR to `dev`
5. Get 1 approval + pass CI

## Commit style
Use simple prefixes:
- `feat:` new feature
- `fix:` bug fix
- `chore:` tooling/config
- `docs:` documentation

## Local testing
- API health: http://localhost:8000/health
- API docs: http://localhost:8000/docs
- Web: http://localhost:3000

---

Create .env files as files, not folders:

Root: .env (copy from .env.example)

Web: apps/web/.env.local

Example root .env:

CORS_ORIGINS=http://localhost:3000
DATABASE_URL=sqlite:///./dev.db
NEXT_PUBLIC_API_URL=http://localhost:8000


Example apps/web/.env.local:

NEXT_PUBLIC_API_URL=http://localhost:8000

3) Install + run API

From repo root:

npm run install:api
npm run dev:api


API should be running at:

Health: http://localhost:8000/health

Docs: http://localhost:8000/docs

4) Install + run Web

Open a second terminal at repo root:

npm run install:web
npm run dev:web


Web should be running at:

http://localhost:3000

Common Commands

From repo root:

Run web dev server: npm run dev:web

Run API dev server: npm run dev:api

Install web deps: npm run install:web

Install API deps: npm run install:api

Lint web: npm run lint:web

Build web: npm run build:web

Branching / PR Rules

main: stable + deployable only

dev: active integration branch

feature branches: feat/<area>-<desc> (ex: feat/recruiting-form)

Open a PR into dev

Require at least 1 approval + CI pass

Environment Notes

We use SQLite locally so anyone can run the project without Docker.

When we deploy later, we will switch:

DATABASE_URL → Postgres connection string

run Alembic migrations against Postgres