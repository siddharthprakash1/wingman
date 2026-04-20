"""
HTTP client tool — structured REST/GraphQL calls.

Unlike the basic web_fetch (GET + text), this lets the agent issue arbitrary
HTTP methods with headers/params/body. Uses the shared httpx AsyncClient.
"""

from __future__ import annotations

import json as _json
import logging
from typing import Any

from src.providers._http import get_shared_client
from src.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)

_ALLOWED_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}


async def http_request(
    method: str,
    url: str,
    headers: dict[str, str] | None = None,
    params: dict[str, Any] | None = None,
    json: dict[str, Any] | list[Any] | None = None,
    body: str | None = None,
    timeout: int = 30,
) -> str:
    """
    Issue an HTTP request.

    Args:
        method: HTTP method (GET/POST/PUT/PATCH/DELETE/HEAD/OPTIONS).
        url: Absolute URL.
        headers: Optional request headers.
        params: Optional URL query params.
        json: Optional JSON body (sets Content-Type).
        body: Optional raw text body (ignored if json given).
        timeout: Request timeout in seconds.

    Returns:
        Formatted string with status, headers, and body.
    """
    method_u = method.upper()
    if method_u not in _ALLOWED_METHODS:
        return f"Unsupported method: {method}. Use one of {sorted(_ALLOWED_METHODS)}"

    if not url.startswith(("http://", "https://")):
        return f"URL must start with http:// or https:// (got: {url[:60]})"

    client = get_shared_client()
    try:
        kwargs: dict[str, Any] = {
            "headers": headers or {},
            "params": params,
            "timeout": timeout,
        }
        if json is not None:
            kwargs["json"] = json
        elif body is not None:
            kwargs["content"] = body

        resp = await client.request(method_u, url, **kwargs)
    except Exception as e:
        return f"Request failed: {type(e).__name__}: {e}"

    # Try to parse JSON for prettier output
    content_type = resp.headers.get("content-type", "")
    body_out: str
    if "application/json" in content_type:
        try:
            body_out = _json.dumps(resp.json(), indent=2, ensure_ascii=False)
        except Exception:
            body_out = resp.text
    else:
        body_out = resp.text

    # Truncate very long bodies
    if len(body_out) > 20_000:
        body_out = body_out[:20_000] + f"\n... (truncated, {len(body_out)} total chars)"

    header_lines = "\n".join(f"{k}: {v}" for k, v in resp.headers.items())
    return (
        f"HTTP {resp.status_code} {resp.reason_phrase}\n"
        f"{header_lines}\n"
        f"\n{body_out}"
    )


def register_http_client_tools(registry: ToolRegistry) -> None:
    registry.register(
        name="http_request",
        description=(
            "Issue an HTTP request (GET/POST/PUT/PATCH/DELETE/HEAD/OPTIONS). "
            "Supports headers, query params, JSON body, and raw body. Returns "
            "status, headers, and response body (JSON pretty-printed if applicable)."
        ),
        parameters={
            "type": "object",
            "properties": {
                "method": {"type": "string", "description": "HTTP method"},
                "url": {"type": "string", "description": "Absolute URL"},
                "headers": {
                    "type": "object",
                    "description": "Request headers",
                    "additionalProperties": {"type": "string"},
                },
                "params": {
                    "type": "object",
                    "description": "URL query parameters",
                },
                "json": {
                    "description": "JSON body (object or array)",
                },
                "body": {
                    "type": "string",
                    "description": "Raw body text (ignored if json given)",
                },
                "timeout": {
                    "type": "integer",
                    "description": "Timeout seconds",
                    "default": 30,
                },
            },
            "required": ["method", "url"],
        },
        func=http_request,
    )
