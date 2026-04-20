"""
Shared httpx AsyncClient pool for provider HTTP calls.

One process-wide client with a tuned connection pool. Avoids the previous
per-provider `httpx.AsyncClient` instantiation that created N idle pools.

Usage:
    from src.providers._http import get_shared_client

    client = get_shared_client()
    resp = await client.post("https://api.openai.com/v1/chat/completions", ...)

At shutdown (gateway lifespan / CLI atexit), call `aclose_shared_client()`.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

_client: Optional[httpx.AsyncClient] = None
_lock = asyncio.Lock()

_DEFAULT_TIMEOUT = httpx.Timeout(120.0, connect=10.0)
_DEFAULT_LIMITS = httpx.Limits(max_connections=50, max_keepalive_connections=20)


def get_shared_client() -> httpx.AsyncClient:
    """Return the process-wide httpx AsyncClient, creating it on first use."""
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            timeout=_DEFAULT_TIMEOUT,
            limits=_DEFAULT_LIMITS,
        )
        logger.debug("Created shared httpx AsyncClient")
    return _client


async def aclose_shared_client() -> None:
    """Close the shared client. Idempotent."""
    global _client
    if _client is not None and not _client.is_closed:
        await _client.aclose()
        logger.debug("Closed shared httpx AsyncClient")
    _client = None
