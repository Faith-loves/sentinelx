from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from typing import List, Optional
from typing import Any
from app.collectors import normalize_event
from app.correlate.engine import ThreatCorrelationEngine
from app.notifier import send_alert
from app.search import log_search
from app.security import require_actor
from app.store import store
import datetime

router = APIRouter()
engine = ThreatCorrelationEngine()


class LogEntry(BaseModel):
    src_ip: str
    dst_ip: Optional[str] = None
    dst_host: Optional[str] = None
    event_type: str
    user: Optional[str] = None
    process: Optional[str] = None
    command: Optional[str] = None
    bytes_transferred: Optional[int] = None
    timestamp: Optional[str] = None


class CollectorEvent(BaseModel):
    event: dict[str, Any]


def process_log(log: LogEntry):
    saved_log = store.add_log(log.model_dump())
    log_search.index_log(saved_log)
    generated_alerts = engine.ingest_log(saved_log)
    stored_alerts = []
    for alert in generated_alerts:
        stored = store.add_alert(alert)
        if stored:
            stored_alerts.append(stored)
    if stored_alerts:
        store.upsert_incident_from_alerts(stored_alerts, store.search_logs(src_ip=saved_log["src_ip"], limit=500))
    return saved_log, stored_alerts


@router.post("/ingest")
async def ingest_log(log: LogEntry, actor: dict = Depends(require_actor)):
    saved_log, alerts = process_log(log)
    if alerts:
        await send_alert("alerts_triggered", {"alerts": alerts, "log": saved_log})
    return {
        "received": True,
        "log": saved_log,
        "alerts_triggered": len(alerts),
        "alerts": alerts,
    }


@router.post("/ingest/bulk")
async def ingest_bulk(logs: List[LogEntry], actor: dict = Depends(require_actor)):
    all_logs = []
    all_alerts = []
    for log in logs:
        saved_log, alerts = process_log(log)
        all_logs.append(saved_log)
        all_alerts.extend(alerts)
    if all_alerts:
        await send_alert("alerts_triggered", {"alerts": all_alerts, "processed": len(all_logs)})
    return {
        "processed": len(all_logs),
        "alerts_triggered": len(all_alerts),
        "alerts": all_alerts,
        "incidents": store.list_incidents(),
    }


@router.post("/collectors/{source}")
async def ingest_collector_event(source: str, payload: CollectorEvent, actor: dict = Depends(require_actor)):
    normalized = LogEntry(**normalize_event(source, payload.event))
    saved_log, alerts = process_log(normalized)
    if alerts:
        await send_alert("collector_alerts_triggered", {"source": source, "alerts": alerts})
    return {
        "source": source,
        "received": True,
        "normalized_log": saved_log,
        "alerts_triggered": len(alerts),
        "alerts": alerts,
    }


@router.post("/collectors/{source}/bulk")
async def ingest_collector_bulk(source: str, payload: list[dict[str, Any]], actor: dict = Depends(require_actor)):
    all_logs = []
    all_alerts = []
    for event in payload:
        normalized = LogEntry(**normalize_event(source, event))
        saved_log, alerts = process_log(normalized)
        all_logs.append(saved_log)
        all_alerts.extend(alerts)
    if all_alerts:
        await send_alert("collector_alerts_triggered", {"source": source, "alerts": all_alerts})
    return {
        "source": source,
        "processed": len(all_logs),
        "alerts_triggered": len(all_alerts),
        "alerts": all_alerts,
    }


@router.get("/search")
async def search_logs(
    query: Optional[str] = None,
    event_type: Optional[str] = None,
    src_ip: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=500),
):
    search_results = log_search.search_logs(query=query, event_type=event_type, src_ip=src_ip, limit=limit)
    source = "elasticsearch" if search_results is not None else "sql"
    results = search_results if search_results is not None else store.search_logs(query=query, event_type=event_type, src_ip=src_ip, limit=limit)
    return {"logs": results, "total": len(results), "source": source}


@router.get("/stream")
async def stream_logs(limit: int = Query(default=25, ge=1, le=100)):
    return {"logs": store.search_logs(limit=limit), "total": len(store.logs)}


@router.get("/simulate")
async def simulate_attack(actor: dict = Depends(require_actor)):
    now = datetime.datetime.utcnow()
    attacker = "185.220.101.8"
    events = []

    for port in range(8):
        events.append(LogEntry(
            src_ip=attacker,
            dst_host="perimeter-fw-01",
            event_type="port_scan",
            command=f"scan-port-{20 + port}",
            timestamp=(now + datetime.timedelta(seconds=port)).isoformat(),
        ))

    for i in range(6):
        events.append(LogEntry(
            src_ip=attacker,
            event_type="auth_failure",
            user="admin",
            dst_host="auth-server-01",
            timestamp=(now + datetime.timedelta(seconds=20 + i)).isoformat(),
        ))

    for host in ["auth-server-01", "web-server-02", "file-server-03"]:
        events.append(LogEntry(
            src_ip="10.0.0.45",
            event_type="auth_success",
            user="admin",
            dst_host=host,
            timestamp=(now + datetime.timedelta(seconds=40 + len(events))).isoformat(),
        ))

    events.extend([
        LogEntry(
            src_ip="10.0.0.45",
            dst_host="file-server-03",
            event_type="privilege_escalation",
            user="admin",
            command="sudo usermod -aG admin svc-backup",
            timestamp=(now + datetime.timedelta(seconds=80)).isoformat(),
        ),
        LogEntry(
            src_ip="10.0.0.67",
            dst_host="file-server-03",
            event_type="process_start",
            process="mimikatz",
            timestamp=(now + datetime.timedelta(seconds=90)).isoformat(),
        ),
        LogEntry(
            src_ip="10.0.0.67",
            dst_ip="45.33.32.156",
            event_type="data_transfer",
            bytes_transferred=2_400_000_000,
            timestamp=(now + datetime.timedelta(seconds=110)).isoformat(),
        ),
    ])

    all_logs = []
    all_alerts = []
    for event in events:
        saved_log, alerts = process_log(event)
        all_logs.append(saved_log)
        all_alerts.extend(alerts)

    incident = None
    if all_alerts:
        incident = store.upsert_incident_from_alerts(all_alerts, all_logs)
        await send_alert("incident_created", {"incident": incident, "alerts": all_alerts})

    return {
        "simulated_events": len(all_logs),
        "attacker_ip": attacker,
        "alerts": all_alerts,
        "incident": incident,
    }
