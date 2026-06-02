from __future__ import annotations

from datetime import datetime
from typing import Any


def normalize_event(source: str, event: dict[str, Any]) -> dict[str, Any]:
    source = source.lower()
    if source == "windows":
        return _windows_event(event)
    if source == "linux":
        return _linux_event(event)
    if source == "network":
        return _network_event(event)
    if source == "application":
        return _application_event(event)
    return _generic_event(event)


def _base(event: dict[str, Any]) -> dict[str, Any]:
    return {
        "src_ip": event.get("src_ip") or event.get("source_ip") or event.get("host_ip") or "unknown",
        "dst_ip": event.get("dst_ip") or event.get("destination_ip"),
        "dst_host": event.get("dst_host") or event.get("host") or event.get("computer") or event.get("hostname"),
        "user": event.get("user") or event.get("username") or event.get("account"),
        "timestamp": event.get("timestamp") or event.get("@timestamp") or datetime.utcnow().isoformat(),
        "process": event.get("process") or event.get("process_name"),
        "command": event.get("command") or event.get("cmdline") or event.get("message"),
        "bytes_transferred": event.get("bytes_transferred") or event.get("bytes") or event.get("sent_bytes"),
        "raw_source": event,
    }


def _windows_event(event: dict[str, Any]) -> dict[str, Any]:
    normalized = _base(event)
    event_id = str(event.get("event_id") or event.get("EventID") or "")
    if event_id in {"4625"}:
        normalized["event_type"] = "auth_failure"
    elif event_id in {"4624"}:
        normalized["event_type"] = "auth_success"
    elif event_id in {"4670", "4720", "4732"}:
        normalized["event_type"] = "privilege_escalation"
    elif _contains(event, {"mimikatz", "cobaltstrike", "meterpreter", "ransomware"}):
        normalized["event_type"] = "process_start"
    else:
        normalized["event_type"] = event.get("event_type") or "windows_event"
    return normalized


def _linux_event(event: dict[str, Any]) -> dict[str, Any]:
    normalized = _base(event)
    message = str(event.get("message") or "").lower()
    if "failed password" in message or "authentication failure" in message:
        normalized["event_type"] = "auth_failure"
    elif "accepted password" in message or "session opened" in message:
        normalized["event_type"] = "auth_success"
    elif "sudo" in message or "usermod" in message or "chmod" in message:
        normalized["event_type"] = "privilege_escalation"
    else:
        normalized["event_type"] = event.get("event_type") or "linux_event"
    return normalized


def _network_event(event: dict[str, Any]) -> dict[str, Any]:
    normalized = _base(event)
    action = str(event.get("action") or event.get("event_type") or "").lower()
    if "scan" in action:
        normalized["event_type"] = "port_scan"
    elif int(event.get("bytes") or event.get("sent_bytes") or 0) >= 100_000_000:
        normalized["event_type"] = "data_transfer"
    else:
        normalized["event_type"] = event.get("event_type") or "network_event"
    return normalized


def _application_event(event: dict[str, Any]) -> dict[str, Any]:
    normalized = _base(event)
    outcome = str(event.get("outcome") or event.get("status") or "").lower()
    if outcome in {"failure", "failed", "denied"}:
        normalized["event_type"] = "auth_failure"
    elif outcome in {"success", "ok", "allowed"}:
        normalized["event_type"] = "auth_success"
    else:
        normalized["event_type"] = event.get("event_type") or "application_event"
    return normalized


def _generic_event(event: dict[str, Any]) -> dict[str, Any]:
    normalized = _base(event)
    normalized["event_type"] = event.get("event_type") or "generic_event"
    return normalized


def _contains(event: dict[str, Any], keywords: set[str]) -> bool:
    haystack = " ".join(str(value).lower() for value in event.values())
    return any(keyword in haystack for keyword in keywords)
