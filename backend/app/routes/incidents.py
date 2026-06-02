from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel
from app.notifier import send_alert
from app.security import require_actor, require_roles
from app.store import store

router = APIRouter()


class IncidentUpdate(BaseModel):
    status: str | None = None
    severity: str | None = None
    assignee: str | None = None
    summary: str | None = None
    recommendations: list[str] | None = None


class IncidentComment(BaseModel):
    body: str


class IncidentEscalation(BaseModel):
    reason: str = "SLA breach or analyst escalation"


class IncidentEvidence(BaseModel):
    timestamp: str | None = None
    event_type: str = "analyst_evidence"
    src_ip: str | None = None
    dst_ip: str | None = None
    dst_host: str | None = None
    user: str | None = None
    process: str | None = None
    command: str | None = None
    description: str


class IncidentCreate(BaseModel):
    title: str
    severity: str = "MEDIUM"
    source_ip: str = "unknown"
    summary: str
    evidence: list[IncidentEvidence] = []
    recommendations: list[str] = []


@router.get("/")
async def list_incidents():
    incidents = store.list_incidents()
    return {"incidents": incidents, "total": len(incidents)}


@router.post("/")
async def create_incident(payload: IncidentCreate, actor: dict = Depends(require_roles("ADMIN", "ANALYST"))):
    incident = store.create_manual_incident(
        title=payload.title,
        severity=payload.severity,
        source_ip=payload.source_ip,
        summary=payload.summary,
        evidence=[item.model_dump() for item in payload.evidence],
        recommendations=payload.recommendations,
        actor=actor,
    )
    await send_alert("incident_created", {"incident": incident, "actor": actor["email"], "source": "manual_intake"})
    return incident


@router.get("/sla/breaches")
async def list_sla_breaches(actor: dict = Depends(require_roles("ADMIN", "ANALYST"))):
    incidents = store.list_sla_breaches()
    return {"incidents": incidents, "total": len(incidents)}


@router.get("/{incident_id}")
async def get_incident(incident_id: str):
    incident = store.get_incident(incident_id)
    if not incident:
        return {"error": "Incident not found"}
    return incident


@router.patch("/{incident_id}")
async def update_incident(
    incident_id: str,
    payload: IncidentUpdate,
    actor: dict = Depends(require_roles("ADMIN", "ANALYST")),
):
    updates = payload.model_dump(exclude_none=True)
    incident = store.update_incident(incident_id, updates, actor)
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    return incident


@router.post("/{incident_id}/escalate")
async def escalate_incident(
    incident_id: str,
    payload: IncidentEscalation,
    actor: dict = Depends(require_roles("ADMIN", "ANALYST")),
):
    incident = store.escalate_incident(incident_id, actor, payload.reason)
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    await send_alert("incident_escalated", {"incident": incident, "reason": payload.reason, "actor": actor["email"]})
    return incident


@router.post("/{incident_id}/comments")
async def add_comment(
    incident_id: str,
    payload: IncidentComment,
    actor: dict = Depends(require_actor),
):
    comment = store.add_incident_comment(incident_id, payload.body, actor)
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    return {"comment": comment}


@router.get("/{incident_id}/timeline")
async def get_incident_timeline(incident_id: str):
    incident = store.get_incident(incident_id)
    if not incident:
        return {"error": "Incident not found"}
    return {"incident_id": incident_id, "timeline": incident["timeline"]}


@router.get("/{incident_id}/graph")
async def get_incident_graph(incident_id: str):
    incident = store.get_incident(incident_id)
    if not incident:
        return {"error": "Incident not found"}
    return {"incident_id": incident_id, "graph": incident["graph"]}


@router.get("/{incident_id}/report")
async def get_incident_report(incident_id: str):
    incident = store.get_incident(incident_id)
    if not incident:
        return {"error": "Incident not found"}
    return {"incident_id": incident_id, "report": _build_report(incident)}


@router.get("/{incident_id}/report.pdf")
async def get_incident_report_pdf(incident_id: str):
    incident = store.get_incident(incident_id)
    if not incident:
        return {"error": "Incident not found"}
    report = _build_report(incident)
    pdf = _simple_pdf(report)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={incident_id}-SentinelX-report.pdf"},
    )


def _build_report(incident: dict) -> str:
    timeline = "\n".join(
        f"- {event.get('timestamp')} | {event.get('description')}"
        for event in incident.get("timeline", [])
    )
    recommendations = "\n".join(f"- {item}" for item in incident.get("recommendations", []))
    return f"""SENTINELX INCIDENT REPORT

Incident: {incident['id']}
Status: {incident['status']}
Severity: {incident['severity']}
Risk Score: {incident['risk_score']}
Source IP: {incident['source_ip']}

EXECUTIVE SUMMARY
{incident['summary']}

TECHNICAL TIMELINE
{timeline}

RECOMMENDATIONS
{recommendations}
"""


def _simple_pdf(text: str) -> bytes:
    safe = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    lines = safe.splitlines()[:42]
    content_lines = ["BT", "/F1 10 Tf", "50 780 Td"]
    for line in lines:
        content_lines.append(f"({line[:95]}) Tj")
        content_lines.append("0 -15 Td")
    content_lines.append("ET")
    stream = "\n".join(content_lines)
    objects = [
        "1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj",
        "2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj",
        "3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj",
        "4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Courier >> endobj",
        f"5 0 obj << /Length {len(stream.encode())} >> stream\n{stream}\nendstream endobj",
    ]
    pdf = "%PDF-1.4\n"
    offsets = [0]
    for obj in objects:
        offsets.append(len(pdf.encode()))
        pdf += obj + "\n"
    xref = len(pdf.encode())
    pdf += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n"
    for offset in offsets[1:]:
        pdf += f"{offset:010d} 00000 n \n"
    pdf += f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF"
    return pdf.encode()
