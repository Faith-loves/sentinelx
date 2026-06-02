from __future__ import annotations

from typing import Any

from app.config import settings

try:
    from elasticsearch import Elasticsearch
except Exception:  # pragma: no cover - optional runtime dependency
    Elasticsearch = None  # type: ignore[assignment]


class LogSearch:
    def __init__(self) -> None:
        self.client = None
        if settings.elasticsearch_enabled and settings.elasticsearch_url and Elasticsearch:
            self.client = Elasticsearch(settings.elasticsearch_url)

    @property
    def available(self) -> bool:
        if not self.client:
            return False
        try:
            return bool(self.client.ping())
        except Exception:
            return False

    def index_log(self, log: dict[str, Any]) -> None:
        if not self.available:
            return
        self.client.index(index=settings.elasticsearch_index, id=log["id"], document=log)

    def search_logs(
        self,
        query: str | None = None,
        event_type: str | None = None,
        src_ip: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]] | None:
        if not self.available:
            return None

        filters: list[dict[str, Any]] = []
        if event_type:
            filters.append({"term": {"event_type.keyword": event_type}})
        if src_ip:
            filters.append({"term": {"src_ip.keyword": src_ip}})

        body: dict[str, Any] = {
            "size": limit,
            "sort": [{"timestamp": {"order": "desc"}}],
            "query": {"bool": {"filter": filters}},
        }
        if query:
            body["query"]["bool"]["must"] = [{
                "simple_query_string": {
                    "query": query,
                    "fields": ["event_type^2", "src_ip", "dst_ip", "dst_host", "user", "process", "command"],
                    "default_operator": "and",
                }
            }]

        response = self.client.search(index=settings.elasticsearch_index, **body)
        return [hit["_source"] for hit in response.get("hits", {}).get("hits", [])]


log_search = LogSearch()
