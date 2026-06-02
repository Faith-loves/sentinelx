from fastapi import Depends, FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from app.routes import alerts, auth, incidents, logs
from app.config import settings
from app.search import log_search
from app.security import require_roles
from app.store import store

app = FastAPI(
    title="SentinelX API",
    description="Autonomous Threat Hunting Platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_methods=["*"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["Alerts"])
app.include_router(logs.router, prefix="/api/logs", tags=["Logs"])
app.include_router(incidents.router, prefix="/api/incidents", tags=["Incidents"])

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "SentinelX",
        "version": "1.0.0",
        "environment": settings.environment,
        "demo_mode": settings.demo_mode,
        "database": str(store.db_path),
        "logs": len(store.logs),
        "alerts": len(store.alerts),
        "incidents": len(store.incidents),
    }

@app.get("/ready")
async def ready():
    database = store.health_check()
    return {
        "status": "ready",
        "service": "SentinelX",
        "database": database,
        "search": {
            "engine": "elasticsearch" if log_search.available else "sql-fallback",
            "index": settings.elasticsearch_index,
        },
    }

@app.get("/metrics")
async def metrics():
    alerts = store.alerts
    incidents = list(store.incidents.values())
    lines = [
        "# HELP sentinelx_logs_total Total logs retained in SentinelX.",
        "# TYPE sentinelx_logs_total gauge",
        f"sentinelx_logs_total {len(store.logs)}",
        "# HELP sentinelx_alerts_total Total alerts retained in SentinelX.",
        "# TYPE sentinelx_alerts_total gauge",
        f"sentinelx_alerts_total {len(alerts)}",
        "# HELP sentinelx_incidents_total Total incidents retained in SentinelX.",
        "# TYPE sentinelx_incidents_total gauge",
        f"sentinelx_incidents_total {len(incidents)}",
        "# HELP sentinelx_sla_breaches_total Open incidents past SLA.",
        "# TYPE sentinelx_sla_breaches_total gauge",
        f"sentinelx_sla_breaches_total {len(store.list_sla_breaches())}",
    ]
    return Response("\n".join(lines) + "\n", media_type="text/plain")

@app.on_event("startup")
async def bootstrap_admin():
    store.ensure_admin_user(settings.admin_email, settings.admin_password)

@app.post("/api/admin/reset")
async def reset_data(actor: dict = Depends(require_roles("ADMIN"))):
    store.reset()
    return {"reset": True, "actor": actor["email"]}

@app.get("/")
async def root():
    return {"message": "Welcome to SentinelX API"}
