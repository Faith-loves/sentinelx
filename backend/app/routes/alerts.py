from fastapi import APIRouter
from app.config import settings
from app.store import store

router = APIRouter()

SEED_ALERTS = [
    {
        "id": "a1b2c3",
        "type": "brute_force",
        "severity": "HIGH",
        "risk_score": 78,
        "source_ip": "10.0.0.45",
        "status": "NEW",
        "mitre_technique": "T1110",
        "description": "Multiple failed logins from same source",
        "timestamp": "2024-01-15T09:23:11Z",
        "event_count": 23,
        "explanation": "Threshold rule matched repeated authentication failures.",
    },
    {
        "id": "d4e5f6",
        "type": "lateral_movement",
        "severity": "CRITICAL",
        "risk_score": 94,
        "source_ip": "10.0.0.45",
        "status": "INVESTIGATING",
        "mitre_technique": "T1021",
        "description": "Sequential logins across multiple hosts",
        "timestamp": "2024-01-15T09:31:44Z",
        "event_count": 8,
        "explanation": "Same account accessed multiple hosts in a short window.",
    },
]


@router.get("/")
async def get_alerts(
    severity: str = None,
    status: str = None,
    sort_by: str = "risk_score",
    order: str = "desc",
):
    live_alerts = store.list_alerts(severity=severity, status=status, sort_by=sort_by, order=order)
    alerts = live_alerts or (SEED_ALERTS if settings.demo_mode else [])
    if severity and not live_alerts and settings.demo_mode:
        alerts = [alert for alert in alerts if alert["severity"] == severity]
    if status and not live_alerts and settings.demo_mode:
        alerts = [alert for alert in alerts if alert["status"] == status]
    return {"alerts": alerts, "total": len(alerts)}


@router.get("/stats")
async def get_stats():
    alerts = store.list_alerts() or (SEED_ALERTS if settings.demo_mode else [])
    return {
        "total_alerts": len(alerts),
        "critical": len([a for a in alerts if a["severity"] == "CRITICAL"]),
        "high": len([a for a in alerts if a["severity"] == "HIGH"]),
        "medium": len([a for a in alerts if a["severity"] == "MEDIUM"]),
        "low": len([a for a in alerts if a["severity"] == "LOW"]),
        "new": len([a for a in alerts if a["status"] == "NEW"]),
        "investigating": len([a for a in alerts if a["status"] == "INVESTIGATING"]),
        "resolved": len([a for a in alerts if a["status"] == "RESOLVED"]),
        "avg_risk_score": round(sum(a["risk_score"] for a in alerts) / len(alerts)) if alerts else 0,
        "top_attackers": _top_attackers(alerts),
    }


@router.get("/{alert_id}")
async def get_alert(alert_id: str):
    seed_alerts = SEED_ALERTS if settings.demo_mode else []
    for alert in store.list_alerts() + seed_alerts:
        if alert["id"] == alert_id:
            return alert
    return {"error": "Alert not found"}


def _top_attackers(alerts: list[dict]):
    counts = {}
    for alert in alerts:
        source = alert.get("source_ip", "unknown")
        counts.setdefault(source, {"ip": source, "alerts": 0, "risk": 0})
        counts[source]["alerts"] += 1
        counts[source]["risk"] = max(counts[source]["risk"], alert.get("risk_score", 0))
    return sorted(counts.values(), key=lambda item: item["risk"], reverse=True)[:5]
