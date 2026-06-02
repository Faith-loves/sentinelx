# SentinelX Operations Runbook

## Health Monitoring

Monitor both endpoints:

- `GET /health`: application health and object counts.
- `GET /ready`: database and search readiness.
- `GET /metrics`: Prometheus-style metrics.

Use `ops/healthcheck.ps1` locally:

```powershell
.\ops\healthcheck.ps1 -BackendUrl http://localhost:8000
```

Alert when:

- `/ready` fails.
- Search falls back from `elasticsearch` to `sql-fallback` unexpectedly.
- Log ingestion volume drops to zero during expected collection windows.
- Postgres disk usage exceeds 80%.
- Any container restarts repeatedly.
- `sentinelx_sla_breaches_total` is greater than zero.

## External Alerting

Set `SENTINELX_ALERT_WEBHOOK_URL` to a webhook receiver. SentinelX sends JSON events for:

- `alerts_triggered`
- `collector_alerts_triggered`
- `incident_created`
- `incident_escalated`

This can point to a small webhook bridge for Slack, Teams, PagerDuty, Opsgenie, or a SIEM intake.

## Backups

Use managed database backups in cloud production. For Docker Compose deployments, run:

```powershell
.\ops\backup-postgres.ps1
```

Production backup expectations:

- Daily full database backup.
- Backup encryption at rest.
- Off-host backup storage.
- Monthly restore test.
- Documented retention window.

## Log Retention

Suggested defaults:

- Raw logs: 30-90 days depending on storage budget.
- Alerts: 180 days.
- Incidents and reports: 1-3 years.
- Authentication/session audit: 1 year.

## Collector Endpoints

Protected collector endpoints accept `Authorization: Bearer <token>` or `X-API-Key`.

- `POST /api/logs/collectors/windows`
- `POST /api/logs/collectors/linux`
- `POST /api/logs/collectors/network`
- `POST /api/logs/collectors/application`
- Bulk forms: add `/bulk`

Each endpoint normalizes source-specific fields into the SentinelX detection schema.

Collector scripts are available in `collectors/`:

- `windows-eventlog-agent.ps1`
- `linux-auth-agent.sh`
- `network-json-agent.ps1`

Run them from hosts that can reach the backend and provide either `SENTINELX_API_KEY` or a bearer token.

## Kubernetes

Manifests are available in `k8s/`:

- `namespace.yaml`
- `secret.example.yaml`
- `backend.yaml`
- `frontend.yaml`
- `ingress.example.yaml`
- `monitoring.yaml`

Replace placeholder domains, image names, and secrets before applying them to a real cluster.
