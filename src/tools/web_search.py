"""
Web search tool — search the web using DuckDuckGo (free, no API key).
"""

from __future__ import annotations

import logging
from typing import Any

from src.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


async def web_search(query: str, max_results: int = 5) -> str:
    """
    Search the web using DuckDuckGo.

    Args:
        query: The search query.
        max_results: Maximum number of results to return (default: 5).

    Returns:
        Formatted search results.
    """
    import asyncio
    
    try:
        try:
            from ddgs import DDGS
        except ImportError:
            from duckduckgo_search import DDGS

        results = []
        last_error = None
        
        # Retry up to 3 times with exponential backoff
        for attempt in range(3):
            try:
                with DDGS() as ddgs:
                    for r in ddgs.text(query, max_results=max_results):
                        results.append({
                            "title": r.get("title", ""),
                            "url": r.get("href", r.get("link", "")),
                            "snippet": r.get("body", r.get("snippet", "")),
                        })
                break  # Success, exit retry loop
            except Exception as e:
                last_error = e
                if attempt < 2:  # Don't sleep on last attempt
                    await asyncio.sleep(2 ** attempt)  # 1s, 2s backoff
                continue

        if not results and last_error:
            return f"❌ Search failed after 3 attempts: {last_error}"

        if not results:
            return f"No results found for: {query}"

        output = f"🔍 Search results for: {query}\n{'─' * 50}\n\n"
        for i, r in enumerate(results, 1):
            output += f"**{i}. {r['title']}**\n"
            output += f"   {r['url']}\n"
            output += f"   {r['snippet']}\n\n"

        return output

    except ImportError:
        return (
            "❌ duckduckgo-search not installed. "
            "Run: pip install duckduckgo-search"
        )
    except Exception as e:
        return f"❌ Search failed: {e}"


async def web_fetch(url: str) -> str:
    """
    Fetch the text content of a web page.

    Args:
        url: The URL to fetch.

    Returns:
        The page content as plain text.
    """
    try:
        try:
            import httpx
        except ImportError:
            return "❌ httpx not installed. Run: pip install httpx"

        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=30.0,
            headers={"User-Agent": "OpenClaw-Mine/0.1.0"},
        ) as client:
            response = await client.get(url)
            response.raise_for_status()

            content_type = response.headers.get("content-type", "")
            if "text/html" in content_type:
                # Try to extract text from HTML
                try:
                    from html.parser import HTMLParser
                    from io import StringIO

                    class TextExtractor(HTMLParser):
                        def __init__(self):
                            super().__init__()
                            self.result = StringIO()
                            self._skip = False

                        def handle_starttag(self, tag, attrs):
                            if tag in ("script", "style", "head"):
                                self._skip = True

                        def handle_endtag(self, tag):
                            if tag in ("script", "style", "head"):
                                self._skip = False
                            if tag in ("p", "br", "div", "h1", "h2", "h3", "h4", "li"):
                                self.result.write("\n")

                        def handle_data(self, data):
                            if not self._skip:
                                self.result.write(data.strip() + " ")

                    extractor = TextExtractor()
                    extractor.feed(response.text)
                    text = extractor.result.getvalue()
                    # Clean up whitespace
                    lines = [line.strip() for line in text.split("\n") if line.strip()]
                    return "\n".join(lines[:500])  # Limit to 500 lines
                except Exception:
                    return response.text[:10000]
            else:
                return response.text[:10000]

    except Exception as e:
        return f"❌ Failed to fetch {url}: {e}"


def register_web_search_tools(registry: ToolRegistry) -> None:
    """Register web search tools with the registry."""
    registry.register(
        name="web_search",
        description="Search the web using DuckDuckGo. Returns titles, URLs, and snippets.",
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results (default: 5)",
                    "default": 5,
                },
            },
            "required": ["query"],
        },
        func=web_search,
    )

    registry.register(
        name="web_fetch",
        description="Fetch and extract text content from a web page URL.",
        parameters={
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The URL to fetch",
                },
            },
            "required": ["url"],
        },
        func=web_fetch,
    )
