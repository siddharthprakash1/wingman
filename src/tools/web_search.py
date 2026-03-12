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
    
    print(f"   🔍 Web search: '{query}' (max {max_results} results)")
    
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
                # Use news search for news-related queries, otherwise text search
                with DDGS() as ddgs:
                    # Check if this is a news query
                    news_keywords = ['news', 'latest', 'today', 'breaking', 'recent', 'announcement', 'update']
                    is_news_query = any(kw in query.lower() for kw in news_keywords)
                    
                    if is_news_query:
                        print(f"   📰 Using NEWS search...")
                        search_results = ddgs.news(
                            query, 
                            max_results=max_results + 3,  # Get a few extra to filter
                            safesearch='moderate',
                        )
                    else:
                        print(f"   🌐 Using TEXT search...")
                        search_results = ddgs.text(
                            query, 
                            max_results=max_results + 3,
                            safesearch='moderate',
                            region='wt-wt',
                        )
                    
                    for r in search_results:
                        title = r.get("title", "")
                        # News results have 'body', text results have 'body' or 'snippet'
                        body = r.get("body", r.get("snippet", ""))
                        href = r.get("url", r.get("href", r.get("link", "")))
                        date = r.get("date", "")
                        source = r.get("source", "")
                        
                        # Skip generic/irrelevant results
                        skip_phrases = [
                            "Air New Zealand", "About Us", "Contact Us", 
                            "Privacy Policy", "Terms of Service"
                        ]
                        if any(phrase in title for phrase in skip_phrases):
                            continue
                        
                        result_entry = {
                            "title": title,
                            "url": href,
                            "snippet": body[:400] if body else "",
                        }
                        if date:
                            result_entry["date"] = date
                        if source:
                            result_entry["source"] = source
                            
                        results.append(result_entry)
                        
                        if len(results) >= max_results:
                            break
                            
                break  # Success, exit retry loop
            except Exception as e:
                last_error = e
                print(f"   ⚠️ Search attempt {attempt+1} failed: {e}")
                if attempt < 2:
                    await asyncio.sleep(2 ** attempt)
                continue

        if not results and last_error:
            return f"❌ Search failed after 3 attempts: {last_error}"

        if not results:
            return f"No results found for: {query}"

        print(f"   ✅ Found {len(results)} results")
        
        output = f"🔍 Search results for: {query}\n{'─' * 50}\n\n"
        for i, r in enumerate(results, 1):
            output += f"**{i}. {r['title']}**\n"
            if r.get('source'):
                output += f"   Source: {r['source']}"
            if r.get('date'):
                output += f" | Date: {r['date']}"
            if r.get('source') or r.get('date'):
                output += "\n"
            output += f"   URL: {r['url']}\n"
            output += f"   {r['snippet']}\n\n"

        return output

    except ImportError:
        return (
            "❌ duckduckgo-search not installed. "
            "Run: pip install duckduckgo-search"
        )
    except Exception as e:
        print(f"   ❌ Search error: {e}")
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
        import httpx
    except ImportError:
        return "❌ httpx not installed. Run: pip install httpx"
    
    try:
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
