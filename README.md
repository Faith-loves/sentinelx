# SentinelX

SentinelX is an autonomous threat hunting platform with a SOC dashboard, attack graph investigation view, AI investigation assistant, and incident reporting workflow.

It now includes a working local backend pipeline:

- SQLite persistence for logs, alerts, and incidents.
- Log ingestion, bulk ingestion, streaming, and search.
- Detection for recon, brute force, credential stuffing, lateral movement, privilege escalation, malware indicators, and data exfiltration.
- Automatic incident creation with timeline and graph reconstruction.
- Text and PDF incident report generation.

## Portfolio Readiness

The current readiness audit is tracked in [docs/PORTFOLIO_READINESS.md](docs/PORTFOLIO_READINESS.md).
Production readiness is tracked in [docs/PRODUCTION_READINESS.md](docs/PRODUCTION_READINESS.md), and deployment steps are in [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).
Operational monitoring and backup guidance is in [docs/OPERATIONS.md](docs/OPERATIONS.md).

Current project status:

- Deployable SOC platform prototype with production-oriented foundations.
- Frontend portfolio UI is polished and responsive.
- Backend has ingestion, persistence, correlation, incident, timeline, graph, and report foundations.
- Enterprise production gaps remain around authentication, real collectors, monitoring, backups, and operational integrations.

## Local Development

Create a local environment file first:

```bash
cp .env.example .env
```

Then set `GROQ_API_KEY` in `.env` if you want the AI assistant to respond.
Set `SENTINELX_API_KEY` if you want ingestion and admin endpoints protected locally.

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Backend:

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Run the end-to-end attack simulation:

```bash
curl http://localhost:8000/api/logs/simulate
```

Useful backend endpoints:

```text
GET  /health
POST /api/admin/reset
POST /api/incidents
POST /api/logs/ingest
POST /api/logs/ingest/bulk
GET  /api/logs/search
GET  /api/logs/stream
GET  /api/logs/simulate
GET  /api/alerts
GET  /api/incidents
GET  /api/incidents/{id}/timeline
GET  /api/incidents/{id}/graph
GET  /api/incidents/{id}/report
GET  /api/incidents/{id}/report.pdf
```

For real analyst-submitted cases, sign in and use `/intake` in the frontend.

Docker Compose is available at the repo root for the backend, frontend, Elasticsearch, and Postgres services.
See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for production-like deployment details.

## Docker Deployment

From the repository root:

```bash
docker compose up --build
```

Then open:

- Frontend: http://localhost:3000
- Backend health check: http://localhost:8000/health
- Backend API docs: http://localhost:8000/docs

Run the demo pipeline after the services are up:

```bash
curl http://localhost:8000/api/logs/simulate
```

Before deploying publicly, rotate any keys that were stored in local `.env` files and keep real secrets out of Git.
