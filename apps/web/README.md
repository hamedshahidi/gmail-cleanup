# apps/web

Next.js App Router frontend for Gmail account connection and listing.

## Local Run

1. Start the FastAPI backend on port `8000`.
2. In `apps/web`, create `.env.local` from `.env.example`.
3. In `apps/web`, install dependencies:
   ```bash
   npm install
   ```
4. Start Next.js:
   ```bash
   npm run dev
   ```
5. Open `http://localhost:3000/accounts`.

## Environment

- `FASTAPI_BASE_URL` defaults to `http://127.0.0.1:8000` when not set.
- Commit only `.env.example`. Do not commit `.env` or `.env.local`.

## Notes

- Browser requests go to Next.js `/api/*` routes, which proxy to FastAPI.
- OAuth redirect and cookies are preserved through the proxy.
