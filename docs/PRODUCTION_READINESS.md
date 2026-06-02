# SentinelX Production Readiness Checklist

Last reviewed: June 1, 2026

## Current Verdict

SentinelX is now structured as a deployable SOC platform prototype with production-oriented foundations. It is not yet a complete enterprise SOC replacement until the remaining items below are completed against real infrastructure, real log sources, and a real operating environment.

## Completed Foundations

- Dockerized frontend and backend services.
- Postgres-ready persistence for logs, alerts, and incidents.
- SQLite fallback for local development.
- Log ingestion, bulk ingestion, stream, and search endpoints.
- Detection coverage for reconnaissance, brute force, credential stuffing, lateral movement, privilege escalation, malware indicators, and data exfiltration.
- Alert de-duplication by fingerprint.
- Incident creation with timeline and graph reconstruction.
- Text and simple PDF incident report endpoints.
- API-key protection for ingestion, simulation, and admin reset routes when `SENTINELX_API_KEY` is configured.
- Analyst login, bearer-token sessions, bootstrap admin, and role-checked protected routes.
- Optional self-registration controlled by `SENTINELX_ALLOW_REGISTRATION`.
- Environment-based demo mode, so mock seed alerts can be disabled in production.
- Configurable CORS origins.
- Health and readiness endpoints.
- Docker Compose volumes for Postgres and Elasticsearch data.
- Optional Elasticsearch indexing/search with SQL fallback.
- Normalized collector endpoints for Windows, Linux, network, and application events.
- Incident lifecycle update and comments endpoints.
- Backup and healthcheck scripts in `ops/`.
- TOTP MFA setup/enable/disable endpoints.
- OIDC/SSO configuration endpoint for enterprise identity provider wiring.
- SLA targets, SLA breach metrics, and incident escalation endpoint.
- External alert webhook integration for alerts and escalations.
- Kubernetes manifests for namespace, frontend, backend, ingress, secrets, and monitoring.
- Collector agent scripts for Windows event logs, Linux auth logs, and network JSON feeds.

## Required Before Public Production

- Rotate all API keys that were ever stored in local `.env` files.
- Set `SENTINELX_ENV=production`.
- Set `SENTINELX_DEMO_MODE=false`.
- Set a long random `SENTINELX_API_KEY`.
- Restrict `SENTINELX_CORS_ORIGINS` to the deployed frontend origin.
- Put the backend behind HTTPS.
- Put the frontend behind HTTPS.
- Use a managed Postgres database or backed-up Postgres volume.
- Add regular Postgres backups and restore testing.
- Add centralized logs for backend and frontend containers.
- Add uptime monitoring against `/health` and `/ready`.
- Add rate limiting at the reverse proxy or API gateway.
- Configure enterprise SSO/OIDC with the production identity provider.
- Enforce MFA for all analyst/admin accounts.
- Connect real collectors/agents to the normalized collector endpoints.
- Configure external alert receiver for Slack, Teams, PagerDuty, Opsgenie, or SIEM.
- Add retention policy for logs, alerts, incidents, and reports.
- Add migration tooling before schema changes become frequent.

## Enterprise SOC Gaps

- OIDC configuration and TOTP MFA foundations exist; production identity provider details must be configured.
- Case assignment, comments, and status updates exist at API level; richer escalation and SLA workflows are still needed.
- Elasticsearch indexing/search exists with SQL fallback; production mappings and retention policies still need tuning.
- Rule configuration is code-based, not UI/API managed.
- Incident lifecycle state changes are minimal.
- AI assistant still needs live incident evidence injection from the backend.
- The PDF report generator is basic and should be replaced with a proper report renderer.
- No SIEM integrations, EDR integrations, webhook outputs, Slack/Teams notification flows, or ticketing integrations yet.
- Kubernetes manifests exist; Terraform/cloud-specific provisioning is still environment-specific.

## Production Definition

Treat SentinelX as production-ready only when this flow works with real infrastructure:

1. Real endpoint logs are collected continuously.
2. Logs persist to a backed-up production database/search layer.
3. Alerts and incidents survive backend restarts.
4. Analysts authenticate and can only access permitted data.
5. Detection rules are documented, explainable, and tested.
6. Incidents have lifecycle management from new to closed.
7. Reports are generated from real incident evidence.
8. Monitoring alerts the owner when ingestion, detection, database, or frontend availability fails.
9. Backups are tested.
10. Secrets are managed outside source control.
