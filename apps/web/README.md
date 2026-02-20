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
- Proxy routes also forward upstream status/body and `Set-Cookie` headers.

## Testing

Use build as a quick verification step:
```bash
npm run build
```

## Production behavior notes

- Keep browser traffic to Next.js routes only (`/api/*`).
- Set `FASTAPI_BASE_URL` to your deployed FastAPI origin.
- FastAPI session hardening is environment-driven (`APP_ENV`, `APP_SESSION_SECRET`).
