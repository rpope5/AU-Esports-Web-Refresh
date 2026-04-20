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
- Azure Static Web Apps deployment workflow lives at:
  - `.github/workflows/deploy-web-azure-swa.yml`
- Full deployment guide:
  - `../../DEPLOY_AZURE.md`
