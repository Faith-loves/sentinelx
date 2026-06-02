# SentinelX Deployment Guide

## Local Production-Like Deployment

1. Create an environment file:

```bash
copy .env.example .env
```

2. Edit `.env` and set:

```text
GROQ_API_KEY=your-groq-key
SENTINELX_API_KEY=a-long-random-secret
SENTINELX_ENV=production
SENTINELX_DEMO_MODE=false
SENTINELX_CORS_ORIGINS=http://localhost:3000
```

3. Start the stack:

```bash
docker compose up --build
```

4. Open the app:

- Frontend: http://localhost:3000
- Backend health: http://localhost:8000/health
- Backend readiness: http://localhost:8000/ready
- API docs: http://localhost:8000/docs

5. Ingest logs with the API key:

```bash
curl -X POST http://localhost:8000/api/logs/ingest ^
  -H "Content-Type: application/json" ^
  -H "X-API-Key: your-api-key" ^
  -d "{\"src_ip\":\"10.0.0.5\",\"dst_host\":\"auth-01\",\"event_type\":\"auth_failure\",\"user\":\"admin\"}"
```

Or sign in as the bootstrap admin and use the bearer token:

```bash
curl -X POST http://localhost:8000/api/auth/login ^
  -H "Content-Type: application/json" ^
  -d "{\"email\":\"admin@sentinelx.local\",\"password\":\"your-admin-password\"}"
```

Then send protected requests with:

```text
Authorization: Bearer <token>
```

6. Run the demo simulation only in a controlled environment:

```bash
curl http://localhost:8000/api/logs/simulate -H "X-API-Key: your-api-key"
```

## Public Deployment Notes

- Put the frontend and backend behind HTTPS.
- Do not expose Postgres or Elasticsearch directly to the public internet.
- Use a managed database where possible.
- Store secrets in the host, cloud secret manager, or deployment platform secret settings.
- Set `SENTINELX_CORS_ORIGINS` to the real frontend URL.
- Set `NEXT_PUBLIC_API_URL` to the real backend URL before building the frontend image.
- Add a reverse proxy or API gateway for TLS, rate limiting, request logs, and IP allowlists.
- Add monitoring for `/ready`, container restarts, disk usage, database health, and ingestion volume.

## Minimum Environment Variables

```text
SENTINELX_ENV=production
SENTINELX_DEMO_MODE=false
SENTINELX_API_KEY=long-random-secret
SENTINELX_CORS_ORIGINS=https://your-frontend-domain
POSTGRES_URL=postgresql://user:password@host:5432/sentinelx
GROQ_API_KEY=your-groq-key
NEXT_PUBLIC_API_URL=https://your-backend-domain
```

## Protected API Areas

- `POST /api/auth/login`: analyst login.
- `POST /api/auth/register`: optional analyst self-registration when `SENTINELX_ALLOW_REGISTRATION=true`.
- `GET /api/auth/me`: current analyst profile.
- `POST /api/auth/users`: create analyst/admin users, admin only.
- `POST /api/incidents`: create a real analyst-submitted incident from evidence.
- `POST /api/logs/ingest`: protected log ingestion.
- `POST /api/logs/ingest/bulk`: protected bulk ingestion.
- `POST /api/logs/collectors/{source}`: protected normalized collector ingestion.
- `PATCH /api/incidents/{id}`: analyst/admin incident lifecycle update.
- `POST /api/incidents/{id}/comments`: analyst comment workflow.
- `POST /api/admin/reset`: admin only.

## New User Access

Recommended production flow:

1. Admin logs in.
2. Admin creates analyst users through `POST /api/auth/users`.
3. New analyst signs in at `/login`.

Optional portfolio/demo flow:

1. Set `SENTINELX_ALLOW_REGISTRATION=true`.
2. New users can create analyst accounts at `/signup`.
3. Set it back to `false` before using the system as a private SOC workspace.

## Real Incident Intake

Use the frontend:

```text
/intake
```

Sign in first, then submit the incident title, severity, source IP, summary, recommendations, and evidence JSON.

Use the API:

```bash
curl -X POST http://localhost:8000/api/incidents ^
  -H "Content-Type: application/json" ^
  -H "Authorization: Bearer <token>" ^
  -d "{\"title\":\"Suspicious privileged login\",\"severity\":\"HIGH\",\"source_ip\":\"10.0.0.45\",\"summary\":\"Analyst observed suspicious admin access on finance host.\",\"evidence\":[{\"event_type\":\"auth_success\",\"src_ip\":\"10.0.0.45\",\"dst_host\":\"finance-server-01\",\"user\":\"admin\",\"description\":\"Unexpected admin login outside approved change window.\"}],\"recommendations\":[\"Validate admin session owner\",\"Preserve auth logs\",\"Review lateral movement from finance-server-01\"]}"
```

After creating it, review:

```text
/investigate
/reports
```
