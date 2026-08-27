"""
WEALTH HTTP Retry Utility — Phase 1c resilience hardening.

Provides retry with exponential backoff for transient failures
(ConnectTimeout, ReadTimeout, ConnectionError, OSError).

DO NOT change business logic or output formats.
This is resilience hardening only.

DITEMPA BUKAN DIBERI — Forged, not given.
"""
from __future__ import annotations

import asyncio
import logging
import sys
import time
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")

# Default retry policy
DEFAULT_MAX_RETRIES = 3
DEFAULT_TIMEOUT = 10.0  # seconds
DEFAULT_BACKOFF_BASE = 1.0  # seconds


def _log_retry(attempt: int, max_retries: int, url: str, error: Exception) -> None:
    """Log retry to stderr for observability."""
    msg = (
        f"[HTTP_RETRY] attempt {attempt}/{max_retries} for {url}: "
        f"{type(error).__name__}: {error}"
    )
    print(msg, file=sys.stderr, flush=True)


def _log_final_failure(url: str, error: Exception) -> None:
    """Log final failure to stderr."""
    msg = (
        f"[HTTP_RETRY] FINAL_FAILURE for {url}: "
        f"{type(error).__name__}: {error}"
    )
    print(msg, file=sys.stderr, flush=True)


def _is_transient(exc: Exception) -> bool:
    """Check if exception is transient (retryable)."""
    # httpx transient errors
    try:
        import httpx
        if isinstance(exc, (httpx.ConnectTimeout, httpx.ReadTimeout,
                            httpx.ConnectError, httpx.RemoteProtocolError)):
            return True
    except ImportError:
        pass
    # urllib transient errors
    import urllib.error
    if isinstance(exc, (urllib.error.URLError, TimeoutError, OSError)):
        return True
    if isinstance(exc, ConnectionError):
        return True
    return False


def _make_error_response(
    provider: str,
    error_code: str,
    message: str,
    url: str = "",
) -> dict:
    """Return structured error dict on failure."""
    return {
        "status": "ERROR",
        "error_code": error_code,
        "message": message,
        "provider": provider,
        "source_uri": url,
    }


async def async_fetch_with_retry(
    url: str,
    *,
    max_retries: int = DEFAULT_MAX_RETRIES,
    timeout: float = DEFAULT_TIMEOUT,
    backoff_base: float = DEFAULT_BACKOFF_BASE,
    provider: str = "unknown",
    **kwargs: Any,
) -> dict:
    """Async HTTP GET with retry + timeout via httpx.

    Returns parsed JSON dict on success.
    Returns structured error dict on failure.
    """
    import httpx

    last_exc: Exception | None = None

    for attempt in range(1, max_retries + 1):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.get(url, **kwargs)
                resp.raise_for_status()
                return resp.json()
        except Exception as e:
            last_exc = e
            if attempt < max_retries and _is_transient(e):
                _log_retry(attempt, max_retries, url, e)
                await asyncio.sleep(backoff_base * (2 ** (attempt - 1)))
            else:
                break

    _log_final_failure(url, last_exc or Exception("unknown"))
    error_code = "API_TIMEOUT" if isinstance(last_exc, TimeoutError) else "API_UNAVAILABLE"
    return _make_error_response(
        provider=provider,
        error_code=error_code,
        message=f"{type(last_exc).__name__}: {last_exc}",
        url=url,
    )


def sync_fetch_with_retry(
    url: str,
    *,
    max_retries: int = DEFAULT_MAX_RETRIES,
    timeout: float = DEFAULT_TIMEOUT,
    backoff_base: float = DEFAULT_BACKOFF_BASE,
    provider: str = "unknown",
    **kwargs: Any,
) -> dict:
    """Sync HTTP GET with retry + timeout via httpx.

    Returns parsed JSON dict on success.
    Returns structured error dict on failure.
    """
    import httpx

    last_exc: Exception | None = None

    for attempt in range(1, max_retries + 1):
        try:
            with httpx.Client(timeout=timeout) as client:
                resp = client.get(url, **kwargs)
                resp.raise_for_status()
                return resp.json()
        except Exception as e:
            last_exc = e
            if attempt < max_retries and _is_transient(e):
                _log_retry(attempt, max_retries, url, e)
                time.sleep(backoff_base * (2 ** (attempt - 1)))
            else:
                break

    _log_final_failure(url, last_exc or Exception("unknown"))
    error_code = "API_TIMEOUT" if isinstance(last_exc, TimeoutError) else "API_UNAVAILABLE"
    return _make_error_response(
        provider=provider,
        error_code=error_code,
        message=f"{type(last_exc).__name__}: {last_exc}",
        url=url,
    )


async def async_fetch_raw_with_retry(
    url: str,
    *,
    max_retries: int = DEFAULT_MAX_RETRIES,
    timeout: float = DEFAULT_TIMEOUT,
    backoff_base: float = DEFAULT_BACKOFF_BASE,
    provider: str = "unknown",
    **kwargs: Any,
) -> tuple[str, int]:
    """Async HTTP GET with retry — returns (body_text, status_code).

    For callers that need the raw response (e.g., crypto adapters
    that compute response_hash from raw bytes).

    Returns ("", -1) + error dict on final failure.
    """
    import httpx

    last_exc: Exception | None = None

    for attempt in range(1, max_retries + 1):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.get(url, **kwargs)
                if resp.status_code == 429:
                    # Rate limit — caller should handle, don't retry here
                    return "", 429
                resp.raise_for_status()
                return resp.text, resp.status_code
        except Exception as e:
            last_exc = e
            if attempt < max_retries and _is_transient(e):
                _log_retry(attempt, max_retries, url, e)
                await asyncio.sleep(backoff_base * (2 ** (attempt - 1)))
            else:
                break

    _log_final_failure(url, last_exc or Exception("unknown"))
    return "", -1


def sync_fetch_raw_with_retry(
    url: str,
    *,
    max_retries: int = DEFAULT_MAX_RETRIES,
    timeout: float = DEFAULT_TIMEOUT,
    backoff_base: float = DEFAULT_BACKOFF_BASE,
    provider: str = "unknown",
    headers: dict[str, str] | None = None,
) -> tuple[str, int]:
    """Sync HTTP GET with retry — returns (body_text, status_code).

    For callers that need the raw response (e.g., crypto adapters
    that compute response_hash from raw bytes).

    Returns ("", -1) on final failure.
    """
    import httpx

    last_exc: Exception | None = None

    for attempt in range(1, max_retries + 1):
        try:
            with httpx.Client(timeout=timeout) as client:
                resp = client.get(url, headers=headers or {})
                if resp.status_code == 429:
                    return "", 429
                resp.raise_for_status()
                return resp.text, resp.status_code
        except Exception as e:
            last_exc = e
            if attempt < max_retries and _is_transient(e):
                _log_retry(attempt, max_retries, url, e)
                time.sleep(backoff_base * (2 ** (attempt - 1)))
            else:
                break

    _log_final_failure(url, last_exc or Exception("unknown"))
    return "", -1
