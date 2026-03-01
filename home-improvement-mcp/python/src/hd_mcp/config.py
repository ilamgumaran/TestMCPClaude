"""Environment-based configuration with cached singleton."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

_config: Config | None = None


@dataclass(frozen=True)
class Config:
    hd_api_key: str
    hd_api_base_url: str
    hd_default_store_id: str | None
    anthropic_api_key: str | None
    claude_model: str
    hd_request_timeout: float


def get_config() -> Config:
    global _config
    if _config is None:
        hd_api_key = os.environ.get("HD_API_KEY", "").strip()
        if not hd_api_key:
            raise RuntimeError(
                "HD_API_KEY environment variable is required but not set."
            )
        _config = Config(
            hd_api_key=hd_api_key,
            hd_api_base_url=os.environ.get(
                "HD_API_BASE_URL", "https://productapi.homedepot.com"
            ).rstrip("/"),
            hd_default_store_id=os.environ.get("HD_DEFAULT_STORE_ID") or None,
            anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY") or None,
            claude_model=os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-6"),
            hd_request_timeout=float(os.environ.get("HD_REQUEST_TIMEOUT", "30")),
        )
    return _config


def reset_config() -> None:
    """Clear cached config — for test isolation only."""
    global _config
    _config = None
