from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List
import hashlib

SIGMA_PATTERNS = {
    "reconnaissance": {
        "description": "Port scan or network enumeration detected",
        "threshold": 8,
        "window_seconds": 120,
        "severity": "MEDIUM",
        "mitre": "T1595",
    },
    "brute_force": {
        "description": "Multiple failed logins from same source",
        "threshold": 5,
        "window_seconds": 60,
        "severity": "HIGH",
        "mitre": "T1110",
    },
    "credential_stuffing": {
        "description": "Credential stuffing pattern detected across multiple users",
        "threshold": 6,
        "window_seconds": 120,
        "severity": "HIGH",
        "mitre": "T1110",
    },
    "lateral_movement": {
        "description": "Sequential logins across multiple hosts",
        "threshold": 3,
        "window_seconds": 300,
        "severity": "CRITICAL",
        "mitre": "T1021",
    },
    "data_exfiltration": {
        "description": "Large outbound data transfer detected",
        "threshold": 100_000_000,
        "severity": "CRITICAL",
        "mitre": "T1041",
    },
    "privilege_escalation": {
        "description": "Sudo, admin, or privilege change spike detected",
        "threshold": 3,
        "window_seconds": 120,
        "severity": "HIGH",
        "mitre": "T1068",
    },
    "malware_indicator": {
        "description": "Known indicator of compromise detected",
        "threshold": 1,
        "window_seconds": 600,
        "severity": "CRITICAL",
        "mitre": "T1204",
    },
}

IOC_KEYWORDS = {"mimikatz", "cobaltstrike", "ransomware", "meterpreter", "powershell-encoded"}


class ThreatCorrelationEngine:
    def __init__(self):
        self.event_buffer: Dict[str, List] = defaultdict(list)

    def ingest_log(self, log_entry: dict) -> List[dict]:
        alerts = []
        src_ip = log_entry.get("src_ip", "unknown")
        event_type = log_entry.get("event_type", "")
        timestamp = log_entry.get("timestamp") or datetime.utcnow().isoformat()

        key = f"{src_ip}:{event_type}"
        self.event_buffer[key].append({"timestamp": timestamp, "data": log_entry})
        self._clean_old_events(key, 900)

        if event_type in {"port_scan", "network_enum"}:
            alerts.extend(self._threshold_alert("reconnaissance", key, src_ip))

        if event_type == "auth_failure":
            alerts.extend(self._threshold_alert("brute_force", key, src_ip))
            alerts.extend(self._credential_stuffing_alert(src_ip))

        if event_type == "auth_success":
            hosts = {
                e["data"].get("dst_host")
                for e in self.event_buffer.get(key, [])
                if e["data"].get("dst_host")
            }
            if len(hosts) >= SIGMA_PATTERNS["lateral_movement"]["threshold"]:
                alerts.append(self._build_alert("lateral_movement", src_ip, list(self.event_buffer[key])))

        if event_type in {"privilege_escalation", "admin_created", "permission_change"}:
            alerts.extend(self._threshold_alert("privilege_escalation", key, src_ip))

        if event_type in {"data_transfer", "exfiltration"}:
            bytes_transferred = int(log_entry.get("bytes_transferred") or 0)
            if bytes_transferred >= SIGMA_PATTERNS["data_exfiltration"]["threshold"]:
                alerts.append(self._build_alert("data_exfiltration", src_ip, [self.event_buffer[key][-1]]))

        if self._contains_ioc(log_entry):
            alerts.append(self._build_alert("malware_indicator", src_ip, [self.event_buffer[key][-1]]))

        return alerts

    def _threshold_alert(self, pattern_name: str, key: str, src_ip: str) -> list[dict]:
        pattern = SIGMA_PATTERNS[pattern_name]
        recent = self._events_in_window(key, pattern["window_seconds"])
        if len(recent) >= pattern["threshold"]:
            return [self._build_alert(pattern_name, src_ip, recent)]
        return []

    def _credential_stuffing_alert(self, src_ip: str) -> list[dict]:
        pattern = SIGMA_PATTERNS["credential_stuffing"]
        users = set()
        events = []
        for key, values in self.event_buffer.items():
            if not key.startswith(f"{src_ip}:auth_failure"):
                continue
            for event in values:
                users.add(event["data"].get("user"))
                events.append(event)
        recent = [
            event for event in events
            if datetime.fromisoformat(event["timestamp"]) > datetime.utcnow() - timedelta(seconds=pattern["window_seconds"])
        ]
        if len(users) >= 3 and len(recent) >= pattern["threshold"]:
            return [self._build_alert("credential_stuffing", src_ip, recent)]
        return []

    def _contains_ioc(self, log_entry: dict) -> bool:
        haystack = " ".join(str(value).lower() for value in log_entry.values())
        return any(keyword in haystack for keyword in IOC_KEYWORDS)

    def _build_alert(self, pattern_name: str, src_ip: str, events: list) -> dict:
        pattern = SIGMA_PATTERNS[pattern_name]
        return {
            "id": hashlib.md5(f"{pattern_name}{src_ip}{events[0]['timestamp']}".encode()).hexdigest()[:12],
            "type": pattern_name,
            "description": pattern["description"],
            "severity": pattern["severity"],
            "mitre_technique": pattern["mitre"],
            "source_ip": src_ip,
            "target": events[-1]["data"].get("dst_host") or events[-1]["data"].get("dst_ip"),
            "event_count": len(events),
            "timestamp": datetime.utcnow().isoformat(),
            "status": "NEW",
            "risk_score": self._calculate_risk_score(pattern["severity"], len(events)),
            "explanation": self._explain(pattern_name, events),
        }

    def _explain(self, pattern_name: str, events: list) -> str:
        return (
            f"Rule {pattern_name} matched {len(events)} event(s) inside the configured time window. "
            f"The alert maps to {SIGMA_PATTERNS[pattern_name]['mitre']}."
        )

    def _calculate_risk_score(self, severity: str, event_count: int) -> int:
        base = {"CRITICAL": 80, "HIGH": 60, "MEDIUM": 40, "LOW": 20}.get(severity, 20)
        return min(100, base + min(event_count * 2, 20))

    def _events_in_window(self, key: str, seconds: int) -> list:
        cutoff = datetime.utcnow() - timedelta(seconds=seconds)
        return [e for e in self.event_buffer[key] if datetime.fromisoformat(e["timestamp"]) > cutoff]

    def _clean_old_events(self, key: str, max_age_seconds: int):
        cutoff = datetime.utcnow() - timedelta(seconds=max_age_seconds)
        self.event_buffer[key] = [
            e for e in self.event_buffer[key]
            if datetime.fromisoformat(e["timestamp"]) > cutoff
        ]
