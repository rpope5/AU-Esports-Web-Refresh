# Web App (Next.js)

## Local development

1. Install dependencies:
   - `npm ci`
2. Configure environment:
   - copy `.env.example` to `.env.local`
   - set `NEXT_PUBLIC_API_URL` (local default is `http://localhost:8000`)
3. Run:
   - `npm run dev`

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
