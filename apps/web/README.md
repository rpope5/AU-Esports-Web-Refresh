# Web App (Next.js)

## Local development

Package manager: `npm` (this repo does not use npm/pnpm/yarn workspaces for `apps/web` dependencies).

1. Install dependencies:
   - from `apps/web`: `npm ci`
   - or from repo root: `npm run install:web`
2. Configure environment:
   - copy `.env.example` to `.env.local`
   - set `NEXT_PUBLIC_API_URL` (local default is `http://localhost:8000`)
3. Run:
   - from `apps/web`: `npm run dev`
   - or from repo root: `npm run dev:web`

## Production notes

- Frontend expects API base URL from `NEXT_PUBLIC_API_URL`
- Frontend deploy target is **Vercel** using this directory (`apps/web`) as the project Root Directory
- Keep frontend production dependencies self-contained within `apps/web`
- Required Vercel env var:
  - `NEXT_PUBLIC_API_URL=https://<your-api-app>.azurewebsites.net`
- Optional Vercel env vars for server-side route handlers:
  - `INSTAGRAM_ACCESS_TOKEN`
  - `INSTAGRAM_USER_ID`
- Deployment docs:
  - `../../docs/DEPLOY_VERCEL.md` (frontend)
  - `../../docs/DEPLOY_AZURE.md` (backend/data services)
