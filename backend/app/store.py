from __future__ import annotations

import json
import os
import hashlib
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import uuid4

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from app.config import settings
from app.mfa import generate_totp_secret, provisioning_uri, verify_totp


class SentinelStore:
    """Database store for logs, alerts, and incidents.

    Production:
        Set SENTINELX_DATABASE_URL or DATABASE_URL to a managed Postgres URL.

    Development fallback:
        Uses backend/data/sentinelx.db with SQLite.
    """

    def __init__(self, database_url: str | None = None):
        self.database_url = self._resolve_database_url(database_url)
        self.engine = create_engine(self.database_url, pool_pre_ping=True, future=True)
        self._init_db()

    @property
    def db_path(self) -> str:
        return self.database_url

    def _resolve_database_url(self, database_url: str | None) -> str:
        url = (
            database_url
            or os.getenv("SENTINELX_DATABASE_URL")
            or os.getenv("DATABASE_URL")
            or os.getenv("POSTGRES_URL")
        )
        if url:
            if url.startswith("postgres://"):
                return url.replace("postgres://", "postgresql+psycopg://", 1)
            if url.startswith("postgresql://"):
                return url.replace("postgresql://", "postgresql+psycopg://", 1)
            return url

        default_path = Path(__file__).resolve().parents[1] / "data" / "sentinelx.db"
        default_path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{default_path.as_posix()}"

    def _json_type(self) -> str:
        return "JSONB" if self.engine.dialect.name == "postgresql" else "TEXT"

    def _init_db(self) -> None:
        raw_json_type = self._json_type()
        statements = [
            f"""
            CREATE TABLE IF NOT EXISTS logs (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                src_ip TEXT NOT NULL,
                dst_ip TEXT,
                dst_host TEXT,
                event_type TEXT NOT NULL,
                username TEXT,
                process TEXT,
                command TEXT,
                bytes_transferred BIGINT,
                raw_json {raw_json_type} NOT NULL
            )
            """,
            f"""
            CREATE TABLE IF NOT EXISTS alerts (
                id TEXT PRIMARY KEY,
                fingerprint TEXT UNIQUE NOT NULL,
                type TEXT NOT NULL,
                description TEXT NOT NULL,
                severity TEXT NOT NULL,
                mitre_technique TEXT,
                source_ip TEXT NOT NULL,
                target TEXT,
                event_count INTEGER NOT NULL,
                timestamp TEXT NOT NULL,
                updated_at TEXT,
                status TEXT NOT NULL,
                risk_score INTEGER NOT NULL,
                explanation TEXT,
                raw_json {raw_json_type} NOT NULL
            )
            """,
            f"""
            CREATE TABLE IF NOT EXISTS incidents (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                status TEXT NOT NULL,
                severity TEXT NOT NULL,
                risk_score INTEGER NOT NULL,
                source_ip TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                summary TEXT NOT NULL,
                raw_json {raw_json_type} NOT NULL
            )
            """,
            f"""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                role TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL,
                last_login_at TEXT,
                active INTEGER NOT NULL,
                raw_json {raw_json_type} NOT NULL
            )
            """,
            f"""
            CREATE TABLE IF NOT EXISTS sessions (
                token_hash TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                raw_json {raw_json_type} NOT NULL
            )
            """,
            "CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_logs_src_ip ON logs(src_ip)",
            "CREATE INDEX IF NOT EXISTS idx_logs_event_type ON logs(event_type)",
            "CREATE INDEX IF NOT EXISTS idx_alerts_risk ON alerts(risk_score)",
            "CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id)",
        ]
        with self.engine.begin() as conn:
            for statement in statements:
                conn.execute(text(statement))

    def health_check(self) -> dict[str, Any]:
        with self.engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {
            "status": "ok",
            "dialect": self.engine.dialect.name,
            "database": self.engine.url.render_as_string(hide_password=True),
        }

    def _dump(self, value: dict[str, Any]) -> str:
        return json.dumps(value)

    def _load(self, value: Any) -> dict[str, Any]:
        if isinstance(value, dict):
            return value
        return json.loads(value)

    def add_log(self, log: dict[str, Any]) -> dict[str, Any]:
        entry = {
            **log,
            "id": log.get("id") or str(uuid4()),
            "timestamp": log.get("timestamp") or datetime.utcnow().isoformat(),
        }
        with self.engine.begin() as conn:
            conn.execute(
                text(
                    """
                    INSERT INTO logs (
                        id, timestamp, src_ip, dst_ip, dst_host, event_type,
                        username, process, command, bytes_transferred, raw_json
                    ) VALUES (
                        :id, :timestamp, :src_ip, :dst_ip, :dst_host, :event_type,
                        :username, :process, :command, :bytes_transferred, :raw_json
                    )
                    """
                ),
                {
                    "id": entry["id"],
                    "timestamp": entry["timestamp"],
                    "src_ip": entry.get("src_ip", "unknown"),
                    "dst_ip": entry.get("dst_ip"),
                    "dst_host": entry.get("dst_host"),
                    "event_type": entry.get("event_type", "unknown"),
                    "username": entry.get("user"),
                    "process": entry.get("process"),
                    "command": entry.get("command"),
                    "bytes_transferred": entry.get("bytes_transferred"),
                    "raw_json": self._dump(entry),
                },
            )
        return entry

    def search_logs(
        self,
        query: str | None = None,
        event_type: str | None = None,
        src_ip: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        sql = "SELECT raw_json FROM logs WHERE 1=1"
        params: dict[str, Any] = {"limit": limit}
        if event_type:
            sql += " AND event_type = :event_type"
            params["event_type"] = event_type
        if src_ip:
            sql += " AND src_ip = :src_ip"
            params["src_ip"] = src_ip
        if query:
            sql += " AND CAST(raw_json AS TEXT) LIKE :query"
            params["query"] = f"%{query}%"
        sql += " ORDER BY timestamp DESC LIMIT :limit"
        with self.engine.connect() as conn:
            rows = conn.execute(text(sql), params).fetchall()
        return [self._load(row.raw_json) for row in rows]

    def ensure_admin_user(self, email: str, password: str) -> dict[str, Any]:
        existing = self.get_user_by_email(email)
        if existing:
            return existing
        return self.create_user(email=email, name="SentinelX Admin", role="ADMIN", password=password)

    def create_user(self, email: str, name: str, role: str, password: str) -> dict[str, Any]:
        now = datetime.utcnow().isoformat()
        user = {
            "id": str(uuid4()),
            "email": email.lower().strip(),
            "name": name.strip() or email,
            "role": role.upper(),
            "created_at": now,
            "last_login_at": None,
            "active": True,
            "mfa_enabled": False,
            "mfa_secret": None,
        }
        password_hash = self._hash_password(password)
        with self.engine.begin() as conn:
            conn.execute(
                text(
                    """
                    INSERT INTO users (
                        id, email, name, role, password_hash, created_at,
                        last_login_at, active, raw_json
                    ) VALUES (
                        :id, :email, :name, :role, :password_hash, :created_at,
                        :last_login_at, :active, :raw_json
                    )
                    """
                ),
                {
                    **user,
                    "active": 1,
                    "password_hash": password_hash,
                    "raw_json": self._dump(user),
                },
            )
        return user

    def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        with self.engine.connect() as conn:
            row = conn.execute(
                text("SELECT raw_json FROM users WHERE email = :email"),
                {"email": email.lower().strip()},
            ).fetchone()
        return self._load(row.raw_json) if row else None

    def get_user_by_id(self, user_id: str) -> dict[str, Any] | None:
        with self.engine.connect() as conn:
            row = conn.execute(
                text("SELECT raw_json FROM users WHERE id = :id"),
                {"id": user_id},
            ).fetchone()
        return self._load(row.raw_json) if row else None

    def authenticate_user(self, email: str, password: str, mfa_code: str | None = None) -> dict[str, Any] | None:
        with self.engine.begin() as conn:
            row = conn.execute(
                text("SELECT id, password_hash, raw_json FROM users WHERE email = :email AND active = 1"),
                {"email": email.lower().strip()},
            ).fetchone()
            if not row or not self._verify_password(password, row.password_hash):
                return None
            user = self._load(row.raw_json)
            if user.get("mfa_enabled"):
                secret = user.get("mfa_secret")
                if not secret or not mfa_code or not verify_totp(secret, mfa_code):
                    return None
            user["last_login_at"] = datetime.utcnow().isoformat()
            conn.execute(
                text("UPDATE users SET last_login_at = :last_login_at, raw_json = :raw_json WHERE id = :id"),
                {"id": row.id, "last_login_at": user["last_login_at"], "raw_json": self._dump(user)},
            )
        return user

    def prepare_mfa(self, user_id: str) -> dict[str, Any] | None:
        user = self.get_user_by_id(user_id)
        if not user:
            return None
        secret = user.get("mfa_secret") or generate_totp_secret()
        user["mfa_secret"] = secret
        self._replace_user(user)
        return {
            "secret": secret,
            "provisioning_uri": provisioning_uri(user["email"], secret),
        }

    def enable_mfa(self, user_id: str, code: str) -> bool:
        user = self.get_user_by_id(user_id)
        if not user or not user.get("mfa_secret") or not verify_totp(user["mfa_secret"], code):
            return False
        user["mfa_enabled"] = True
        self._replace_user(user)
        return True

    def disable_mfa(self, user_id: str) -> bool:
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        user["mfa_enabled"] = False
        user["mfa_secret"] = None
        self._replace_user(user)
        return True

    def _replace_user(self, user: dict[str, Any]) -> None:
        with self.engine.begin() as conn:
            conn.execute(
                text("UPDATE users SET raw_json = :raw_json WHERE id = :id"),
                {"id": user["id"], "raw_json": self._dump(user)},
            )

    def create_session(self, user: dict[str, Any], hours: int = 12) -> dict[str, Any]:
        token = secrets.token_urlsafe(36)
        now = datetime.utcnow()
        session = {
            "token": token,
            "user": user,
            "created_at": now.isoformat(),
            "expires_at": (now + timedelta(hours=hours)).isoformat(),
        }
        with self.engine.begin() as conn:
            conn.execute(
                text(
                    """
                    INSERT INTO sessions (token_hash, user_id, created_at, expires_at, raw_json)
                    VALUES (:token_hash, :user_id, :created_at, :expires_at, :raw_json)
                    """
                ),
                {
                    "token_hash": self._hash_token(token),
                    "user_id": user["id"],
                    "created_at": session["created_at"],
                    "expires_at": session["expires_at"],
                    "raw_json": self._dump({k: v for k, v in session.items() if k != "token"}),
                },
            )
        return session

    def get_user_for_token(self, token: str) -> dict[str, Any] | None:
        with self.engine.connect() as conn:
            row = conn.execute(
                text("SELECT user_id, expires_at FROM sessions WHERE token_hash = :token_hash"),
                {"token_hash": self._hash_token(token)},
            ).fetchone()
        if not row or row.expires_at < datetime.utcnow().isoformat():
            return None
        return self.get_user_by_id(row.user_id)

    def add_alert(self, alert: dict[str, Any]) -> dict[str, Any] | None:
        fingerprint = f"{alert.get('type')}:{alert.get('source_ip')}:{alert.get('mitre_technique')}"
        now = datetime.utcnow().isoformat()
        with self.engine.begin() as conn:
            existing = conn.execute(
                text("SELECT raw_json FROM alerts WHERE fingerprint = :fingerprint"),
                {"fingerprint": fingerprint},
            ).fetchone()
            if existing:
                current = self._load(existing.raw_json)
                current["event_count"] = max(current.get("event_count", 0), alert.get("event_count", 0))
                current["risk_score"] = max(current.get("risk_score", 0), alert.get("risk_score", 0))
                current["updated_at"] = now
                conn.execute(
                    text(
                        """
                        UPDATE alerts
                        SET event_count = :event_count,
                            risk_score = :risk_score,
                            updated_at = :updated_at,
                            raw_json = :raw_json
                        WHERE fingerprint = :fingerprint
                        """
                    ),
                    {
                        "event_count": current["event_count"],
                        "risk_score": current["risk_score"],
                        "updated_at": current["updated_at"],
                        "raw_json": self._dump(current),
                        "fingerprint": fingerprint,
                    },
                )
                return current

            stored = {**alert, "updated_at": alert.get("updated_at") or now}
            conn.execute(
                text(
                    """
                    INSERT INTO alerts (
                        id, fingerprint, type, description, severity, mitre_technique,
                        source_ip, target, event_count, timestamp, updated_at, status,
                        risk_score, explanation, raw_json
                    ) VALUES (
                        :id, :fingerprint, :type, :description, :severity, :mitre_technique,
                        :source_ip, :target, :event_count, :timestamp, :updated_at, :status,
                        :risk_score, :explanation, :raw_json
                    )
                    """
                ),
                {
                    "id": stored["id"],
                    "fingerprint": fingerprint,
                    "type": stored.get("type"),
                    "description": stored.get("description"),
                    "severity": stored.get("severity"),
                    "mitre_technique": stored.get("mitre_technique"),
                    "source_ip": stored.get("source_ip", "unknown"),
                    "target": stored.get("target"),
                    "event_count": stored.get("event_count", 0),
                    "timestamp": stored.get("timestamp") or now,
                    "updated_at": stored.get("updated_at"),
                    "status": stored.get("status", "NEW"),
                    "risk_score": stored.get("risk_score", 0),
                    "explanation": stored.get("explanation"),
                    "raw_json": self._dump(stored),
                },
            )
            return stored

    def list_alerts(
        self,
        severity: str | None = None,
        status: str | None = None,
        sort_by: str = "risk_score",
        order: str = "desc",
    ) -> list[dict[str, Any]]:
        allowed_sort = {
            "risk_score": "risk_score",
            "timestamp": "timestamp",
            "severity": "severity",
            "event_count": "event_count",
            "type": "type",
        }
        sql = "SELECT raw_json FROM alerts WHERE 1=1"
        params: dict[str, Any] = {}
        if severity:
            sql += " AND severity = :severity"
            params["severity"] = severity
        if status:
            sql += " AND status = :status"
            params["status"] = status
        direction = "ASC" if order.lower() == "asc" else "DESC"
        sql += f" ORDER BY {allowed_sort.get(sort_by, 'risk_score')} {direction}"
        with self.engine.connect() as conn:
            rows = conn.execute(text(sql), params).fetchall()
        return [self._load(row.raw_json) for row in rows]

    def upsert_incident_from_alerts(self, alerts: list[dict[str, Any]], logs: list[dict[str, Any]]) -> dict[str, Any]:
        if not alerts:
            raise ValueError("Cannot create incident without alerts")
        source_ip = alerts[0].get("source_ip", "unknown")
        incident_id = f"INC-{datetime.utcnow().strftime('%Y%m%d')}-{abs(hash(source_ip)) % 10000:04d}"
        existing = self.get_incident(incident_id)
        created_at = existing["created_at"] if existing else datetime.utcnow().isoformat()
        timeline = self._build_timeline(logs, alerts)
        graph = self._build_graph(logs, alerts)
        risk_score = max(alert.get("risk_score", 0) for alert in alerts)
        incident = {
            "id": incident_id,
            "title": "Autonomous attack investigation",
            "status": "INVESTIGATING",
            "risk_score": risk_score,
            "severity": self._severity_from_risk(risk_score),
            "source_ip": source_ip,
            "created_at": created_at,
            "updated_at": datetime.utcnow().isoformat(),
            "alert_ids": sorted({alert["id"] for alert in alerts}),
            "timeline": timeline,
            "graph": graph,
            "summary": self._build_summary(alerts, timeline),
            "recommendations": [
                "Isolate affected hosts from the network.",
                "Reset impacted credentials and revoke active sessions.",
                "Block malicious source and destination IP addresses.",
                "Preserve logs and capture forensic images for compromised hosts.",
                "Add detection rules for observed MITRE ATT&CK techniques.",
            ],
            "assignee": existing.get("assignee") if existing else None,
            "comments": existing.get("comments", []) if existing else [],
            "sla": existing.get("sla") if existing else self._build_sla(risk_score),
            "escalated_at": existing.get("escalated_at") if existing else None,
            "escalation_level": existing.get("escalation_level", 0) if existing else 0,
        }
        with self.engine.begin() as conn:
            conn.execute(
                text(
                    """
                    DELETE FROM incidents WHERE id = :id
                    """
                ),
                {"id": incident["id"]},
            )
            conn.execute(
                text(
                    """
                    INSERT INTO incidents (
                        id, title, status, severity, risk_score, source_ip,
                        created_at, updated_at, summary, raw_json
                    ) VALUES (
                        :id, :title, :status, :severity, :risk_score, :source_ip,
                        :created_at, :updated_at, :summary, :raw_json
                    )
                    """
                ),
                {
                    "id": incident["id"],
                    "title": incident["title"],
                    "status": incident["status"],
                    "severity": incident["severity"],
                    "risk_score": incident["risk_score"],
                    "source_ip": incident["source_ip"],
                    "created_at": incident["created_at"],
                    "updated_at": incident["updated_at"],
                    "summary": incident["summary"],
                    "raw_json": self._dump(incident),
                },
            )
        return incident

    def create_manual_incident(
        self,
        title: str,
        severity: str,
        source_ip: str,
        summary: str,
        evidence: list[dict[str, Any]],
        recommendations: list[str],
        actor: dict[str, Any],
    ) -> dict[str, Any]:
        now = datetime.utcnow().isoformat()
        risk_score = self._risk_from_severity(severity)
        incident_id = f"INC-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid4())[:8].upper()}"
        normalized_evidence = [
            {
                "id": item.get("id") or str(uuid4()),
                "timestamp": item.get("timestamp") or now,
                "event_type": item.get("event_type") or "analyst_evidence",
                "src_ip": item.get("src_ip") or item.get("source") or source_ip,
                "dst_ip": item.get("dst_ip"),
                "dst_host": item.get("dst_host") or item.get("target"),
                "user": item.get("user"),
                "process": item.get("process"),
                "command": item.get("command") or item.get("description"),
                "description": item.get("description") or "Analyst-submitted evidence",
            }
            for item in evidence
        ]
        incident = {
            "id": incident_id,
            "title": title,
            "status": "NEW",
            "severity": severity.upper(),
            "risk_score": risk_score,
            "source_ip": source_ip,
            "created_at": now,
            "updated_at": now,
            "alert_ids": [],
            "timeline": self._build_timeline(normalized_evidence, []),
            "graph": self._build_graph(normalized_evidence, []),
            "summary": summary,
            "recommendations": recommendations or [
                "Validate submitted evidence and scope affected systems.",
                "Preserve logs and isolate impacted assets if compromise is confirmed.",
                "Assign an analyst owner and update incident status after triage.",
            ],
            "assignee": actor.get("email"),
            "comments": [
                {
                    "id": str(uuid4()),
                    "body": "Incident opened from analyst-submitted evidence.",
                    "author": actor.get("email", "system"),
                    "role": actor.get("role", "ANALYST"),
                    "created_at": now,
                }
            ],
            "sla": self._build_sla(risk_score),
            "escalated_at": None,
            "escalation_level": 0,
            "source": "manual_intake",
            "audit_log": [
                {
                    "timestamp": now,
                    "actor": actor.get("email", "system"),
                    "action": "incident_created",
                    "source": "manual_intake",
                }
            ],
        }
        self._replace_incident(incident)
        return incident

    def list_sla_breaches(self) -> list[dict[str, Any]]:
        now = datetime.utcnow().isoformat()
        open_statuses = {"NEW", "INVESTIGATING", "TRIAGED", "CONTAINING"}
        return [
            incident for incident in self.list_incidents()
            if incident.get("status") in open_statuses
            and incident.get("sla", {}).get("due_at")
            and incident["sla"]["due_at"] < now
        ]

    def escalate_incident(self, incident_id: str, actor: dict[str, Any], reason: str) -> dict[str, Any] | None:
        incident = self.get_incident(incident_id)
        if not incident:
            return None
        now = datetime.utcnow().isoformat()
        incident["status"] = "ESCALATED"
        incident["escalated_at"] = now
        incident["escalation_level"] = int(incident.get("escalation_level") or 0) + 1
        incident["updated_at"] = now
        incident.setdefault("audit_log", []).append({
            "timestamp": now,
            "actor": actor.get("email", "system"),
            "action": "incident_escalated",
            "reason": reason,
        })
        self._replace_incident(incident)
        return incident

    def update_incident(self, incident_id: str, updates: dict[str, Any], actor: dict[str, Any]) -> dict[str, Any] | None:
        incident = self.get_incident(incident_id)
        if not incident:
            return None
        allowed = {"status", "severity", "assignee", "summary", "recommendations"}
        for key, value in updates.items():
            if key in allowed:
                incident[key] = value
        incident["updated_at"] = datetime.utcnow().isoformat()
        incident.setdefault("audit_log", []).append({
            "timestamp": incident["updated_at"],
            "actor": actor.get("email", "system"),
            "action": "incident_updated",
            "changes": {key: value for key, value in updates.items() if key in allowed},
        })
        self._replace_incident(incident)
        return incident

    def add_incident_comment(self, incident_id: str, body: str, actor: dict[str, Any]) -> dict[str, Any] | None:
        incident = self.get_incident(incident_id)
        if not incident:
            return None
        comment = {
            "id": str(uuid4()),
            "body": body,
            "author": actor.get("email", "system"),
            "role": actor.get("role", "ANALYST"),
            "created_at": datetime.utcnow().isoformat(),
        }
        incident.setdefault("comments", []).append(comment)
        incident["updated_at"] = comment["created_at"]
        self._replace_incident(incident)
        return comment

    def _replace_incident(self, incident: dict[str, Any]) -> None:
        with self.engine.begin() as conn:
            conn.execute(text("DELETE FROM incidents WHERE id = :id"), {"id": incident["id"]})
            conn.execute(
                text(
                    """
                    INSERT INTO incidents (
                        id, title, status, severity, risk_score, source_ip,
                        created_at, updated_at, summary, raw_json
                    ) VALUES (
                        :id, :title, :status, :severity, :risk_score, :source_ip,
                        :created_at, :updated_at, :summary, :raw_json
                    )
                    """
                ),
                {
                    "id": incident["id"],
                    "title": incident["title"],
                    "status": incident["status"],
                    "severity": incident["severity"],
                    "risk_score": incident["risk_score"],
                    "source_ip": incident["source_ip"],
                    "created_at": incident["created_at"],
                    "updated_at": incident["updated_at"],
                    "summary": incident["summary"],
                    "raw_json": self._dump(incident),
                },
            )

    def get_incident(self, incident_id: str) -> dict[str, Any] | None:
        with self.engine.connect() as conn:
            row = conn.execute(
                text("SELECT raw_json FROM incidents WHERE id = :id"),
                {"id": incident_id},
            ).fetchone()
        return self._load(row.raw_json) if row else None

    def list_incidents(self) -> list[dict[str, Any]]:
        with self.engine.connect() as conn:
            rows = conn.execute(text("SELECT raw_json FROM incidents ORDER BY updated_at DESC")).fetchall()
        return [self._load(row.raw_json) for row in rows]

    def reset(self) -> None:
        with self.engine.begin() as conn:
            conn.execute(text("DELETE FROM incidents"))
            conn.execute(text("DELETE FROM alerts"))
            conn.execute(text("DELETE FROM logs"))

    @property
    def logs(self) -> list[dict[str, Any]]:
        return self.search_logs(limit=10000)

    @property
    def alerts(self) -> list[dict[str, Any]]:
        return self.list_alerts()

    @property
    def incidents(self) -> dict[str, dict[str, Any]]:
        return {incident["id"]: incident for incident in self.list_incidents()}

    def _build_timeline(self, logs: list[dict[str, Any]], alerts: list[dict[str, Any]]) -> list[dict[str, Any]]:
        events = []
        for log in logs:
            events.append({
                "id": log.get("id"),
                "timestamp": log.get("timestamp"),
                "event_type": log.get("event_type"),
                "source": log.get("src_ip"),
                "target": log.get("dst_host") or log.get("dst_ip"),
                "description": self._describe_log(log),
            })
        for alert in alerts:
            events.append({
                "id": alert.get("id"),
                "timestamp": alert.get("timestamp"),
                "event_type": "alert",
                "source": alert.get("source_ip"),
                "target": alert.get("target"),
                "description": alert.get("description"),
                "severity": alert.get("severity"),
                "mitre_technique": alert.get("mitre_technique"),
            })
        return sorted(events, key=lambda item: item.get("timestamp", ""))

    def _build_graph(self, logs: list[dict[str, Any]], alerts: list[dict[str, Any]]) -> dict[str, Any]:
        nodes: dict[str, dict[str, Any]] = {}
        edges: list[dict[str, Any]] = []
        for log in logs:
            src = log.get("src_ip")
            target = log.get("dst_host") or log.get("dst_ip")
            if src:
                nodes[src] = {"id": src, "label": src, "type": "source", "risk": 70}
            if target:
                nodes[target] = {"id": target, "label": target, "type": "target", "risk": 55}
                edges.append({
                    "from": src,
                    "to": target,
                    "label": log.get("event_type", "event"),
                    "timestamp": log.get("timestamp"),
                })
        for alert in alerts:
            src = alert.get("source_ip")
            alert_node = alert.get("type")
            nodes[alert_node] = {
                "id": alert_node,
                "label": str(alert_node).replace("_", " ").title(),
                "type": "alert",
                "risk": alert.get("risk_score"),
            }
            if src:
                edges.append({
                    "from": src,
                    "to": alert_node,
                    "label": alert.get("mitre_technique"),
                    "timestamp": alert.get("timestamp"),
                })
        return {"nodes": list(nodes.values()), "edges": edges}

    def _build_summary(self, alerts: list[dict[str, Any]], timeline: list[dict[str, Any]]) -> str:
        techniques = sorted({alert.get("mitre_technique") for alert in alerts if alert.get("mitre_technique")})
        return (
            f"SentinelX correlated {len(alerts)} alert(s) across {len(timeline)} timeline events. "
            f"Observed techniques: {', '.join(techniques) or 'none mapped'}."
        )

    def _describe_log(self, log: dict[str, Any]) -> str:
        event = str(log.get("event_type", "event")).replace("_", " ")
        src = log.get("src_ip", "unknown source")
        target = log.get("dst_host") or log.get("dst_ip") or "unknown target"
        return f"{event.title()} from {src} to {target}"

    def _severity_from_risk(self, risk_score: int) -> str:
        if risk_score >= 80:
            return "CRITICAL"
        if risk_score >= 60:
            return "HIGH"
        if risk_score >= 40:
            return "MEDIUM"
        return "LOW"

    def _risk_from_severity(self, severity: str) -> int:
        return {
            "CRITICAL": 92,
            "HIGH": 76,
            "MEDIUM": 52,
            "LOW": 28,
        }.get(severity.upper(), 52)

    def _build_sla(self, risk_score: int) -> dict[str, Any]:
        severity = self._severity_from_risk(risk_score)
        minutes = {
            "CRITICAL": settings.sla_critical_minutes,
            "HIGH": settings.sla_high_minutes,
            "MEDIUM": settings.sla_medium_minutes,
            "LOW": settings.sla_low_minutes,
        }[severity]
        return {
            "severity": severity,
            "target_minutes": minutes,
            "due_at": (datetime.utcnow() + timedelta(minutes=minutes)).isoformat(),
        }

    def _hash_password(self, password: str) -> str:
        salt = secrets.token_hex(16)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120_000).hex()
        return f"pbkdf2_sha256${salt}${digest}"

    def _verify_password(self, password: str, password_hash: str) -> bool:
        try:
            algorithm, salt, expected = password_hash.split("$", 2)
        except ValueError:
            return False
        if algorithm != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120_000).hex()
        return secrets.compare_digest(digest, expected)

    def _hash_token(self, token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()


store = SentinelStore()
