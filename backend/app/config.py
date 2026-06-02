from __future__ import annotations

import os
from dataclasses import dataclass


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    environment: str = os.getenv("SENTINELX_ENV", "development")
    api_key: str | None = os.getenv("SENTINELX_API_KEY")
    admin_email: str = os.getenv("SENTINELX_ADMIN_EMAIL", "admin@sentinelx.local")
    admin_password: str = os.getenv("SENTINELX_ADMIN_PASSWORD", "ChangeMe-Admin-Password")
    allow_registration: bool = _bool_env("SENTINELX_ALLOW_REGISTRATION", False)
    elasticsearch_url: str | None = os.getenv("ELASTICSEARCH_URL")
    elasticsearch_index: str = os.getenv("SENTINELX_ELASTICSEARCH_INDEX", "sentinelx-logs")
    alert_webhook_url: str | None = os.getenv("SENTINELX_ALERT_WEBHOOK_URL")
    oidc_enabled: bool = _bool_env("SENTINELX_OIDC_ENABLED", False)
    oidc_issuer: str | None = os.getenv("SENTINELX_OIDC_ISSUER")
    oidc_client_id: str | None = os.getenv("SENTINELX_OIDC_CLIENT_ID")
    oidc_authorization_url: str | None = os.getenv("SENTINELX_OIDC_AUTHORIZATION_URL")
    oidc_token_url: str | None = os.getenv("SENTINELX_OIDC_TOKEN_URL")
    sla_critical_minutes: int = int(os.getenv("SENTINELX_SLA_CRITICAL_MINUTES", "15"))
    sla_high_minutes: int = int(os.getenv("SENTINELX_SLA_HIGH_MINUTES", "60"))
    sla_medium_minutes: int = int(os.getenv("SENTINELX_SLA_MEDIUM_MINUTES", "240"))
    sla_low_minutes: int = int(os.getenv("SENTINELX_SLA_LOW_MINUTES", "1440"))
    cors_origins: tuple[str, ...] = tuple(
        origin.strip()
        for origin in os.getenv("SENTINELX_CORS_ORIGINS", "http://localhost:3000").split(",")
        if origin.strip()
    )
    demo_mode: bool = _bool_env("SENTINELX_DEMO_MODE", True)
    elasticsearch_enabled: bool = _bool_env("SENTINELX_ELASTICSEARCH_ENABLED", True)

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


settings = Settings()
