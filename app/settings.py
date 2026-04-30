from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass(frozen=True)
class AISettings:
    """Runtime AI backend configuration (server-side only)."""

    provider: str  # "openai" | "anthropic" | "deepseek"
    api_key: str
    base_url: str
    model: str
    timeout_sec: float
    batch_size: int
    max_comment_len: int
    max_rationale_len: int
    max_request_bytes: int
    max_concurrent_batches: int
    anthropic_version: str


def _normalize_provider(raw: str) -> str:
    r = (raw or "").strip().lower()
    if r in ("claude", "anthropic"):
        return "anthropic"
    if r in ("deepseek",):
        return "deepseek"
    if r in ("openai", "openai_compatible", "compatible"):
        return "openai"
    return r


def _infer_provider_from_base_url(base_url: str) -> str:
    host = (urlparse(base_url).netloc or base_url).lower()
    if "anthropic.com" in host:
        return "anthropic"
    if "deepseek.com" in host:
        return "deepseek"
    return "openai"


def _resolve_provider(explicit: str, base_url: str) -> str:
    exp = _normalize_provider(explicit)
    if exp == "auto" or not exp:
        return _infer_provider_from_base_url(base_url)
    return exp


def _default_base_url(provider: str) -> str:
    if provider == "anthropic":
        return "https://api.anthropic.com/v1"
    if provider == "deepseek":
        return "https://api.deepseek.com/v1"
    return "https://api.openai.com/v1"


def _default_model(provider: str) -> str:
    if provider == "anthropic":
        return "claude-3-5-sonnet-20241022"
    if provider == "deepseek":
        return "deepseek-chat"
    return "gpt-4o-mini"


def get_ai_settings() -> AISettings:
    key = (os.environ.get("DATA_CLASSIFIER_AI_API_KEY") or "").strip()
    explicit_provider = os.environ.get("DATA_CLASSIFIER_AI_PROVIDER") or "auto"
    base_env = (os.environ.get("DATA_CLASSIFIER_AI_BASE_URL") or "").strip()
    model_env = (os.environ.get("DATA_CLASSIFIER_AI_MODEL") or "").strip()
    anthropic_version = (
        os.environ.get("DATA_CLASSIFIER_AI_ANTHROPIC_VERSION") or "2023-06-01"
    ).strip()

    if base_env:
        base = base_env.rstrip("/")
        provider = _resolve_provider(explicit_provider, base)
    else:
        prov_guess = _normalize_provider(explicit_provider)
        if prov_guess in ("auto", ""):
            provider = "openai"
        else:
            provider = prov_guess
        base = _default_base_url(provider)

    model = model_env if model_env else _default_model(provider)

    timeout_sec = float(os.environ.get("DATA_CLASSIFIER_AI_TIMEOUT_SEC") or "120")
    # Smaller default batches avoid huge JSON bodies (proxy / API limits, "network error").
    batch_size = max(1, min(80, int(os.environ.get("DATA_CLASSIFIER_AI_BATCH_SIZE") or "15")))
    max_comment_len = max(
        100, min(2000, int(os.environ.get("DATA_CLASSIFIER_AI_MAX_COMMENT_LEN") or "400"))
    )
    max_rationale_len = max(
        80, min(1200, int(os.environ.get("DATA_CLASSIFIER_AI_MAX_RATIONALE_LEN") or "380"))
    )
    # Cap serialized user message size (UTF-8); split batches when exceeded.
    max_request_bytes = max(
        16_384,
        min(2_000_000, int(os.environ.get("DATA_CLASSIFIER_AI_MAX_REQUEST_BYTES") or "98304")),
    )
    max_concurrent_batches = max(
        1,
        min(16, int(os.environ.get("DATA_CLASSIFIER_AI_MAX_CONCURRENCY") or "3")),
    )

    return AISettings(
        provider=provider,
        api_key=key,
        base_url=base,
        model=model,
        timeout_sec=timeout_sec,
        batch_size=batch_size,
        max_comment_len=max_comment_len,
        max_rationale_len=max_rationale_len,
        max_request_bytes=max_request_bytes,
        max_concurrent_batches=max_concurrent_batches,
        anthropic_version=anthropic_version,
    )


def ai_enhancement_configured() -> bool:
    return bool(get_ai_settings().api_key)


def public_ai_status() -> dict:
    s = get_ai_settings()
    return {
        "available": bool(s.api_key),
        "provider": s.provider if s.api_key else None,
        "model": s.model if s.api_key else None,
        "base_url_host": _safe_host(s.base_url) if s.api_key else None,
    }


def _safe_host(base_url: str) -> str:
    try:
        u = urlparse(base_url)
        return u.netloc or base_url[:48]
    except Exception:
        return ""
