"""
Browser Agent - Web automation and interaction.

Capabilities:
- Navigate websites
- Fill forms
- Extract data from web pages
- Take screenshots
- Interact with web applications
"""

from __future__ import annotations

from src.agents.base import BaseAgent, AgentCapability, AgentContext


class BrowserAgent(BaseAgent):
    """Agent specialized in web browser automation."""

    @property
    def name(self) -> str:
        return "browser"

    @property
    def description(self) -> str:
        return "Automates web browser interactions, form filling, and data extraction."

    @property
    def capabilities(self) -> list[AgentCapability]:
        return [AgentCapability.BROWSER]

    def get_allowed_tools(self) -> list[str]:
        return [
            "web_fetch", "web_search", "bash",
            "read_file", "write_file",
        ]

    def get_system_prompt(self, context: AgentContext) -> str:
        return f"""You are a Browser Agent - an expert at web automation and interaction.

## Your Role
You automate web browser tasks including:
- Navigating websites
- Extracting information from web pages
- Filling out forms
- Interacting with web applications
- Scraping data

## Guidelines
1. **Respect robots.txt**: Don't scrape sites that prohibit it.
2. **Rate Limiting**: Add delays between requests to avoid overloading servers.
3. **Error Handling**: Handle network errors gracefully.
4. **Data Extraction**: Use appropriate parsing for HTML content.
5. **Privacy**: Don't store sensitive user data unnecessarily.

## Available Tools
- `web_fetch`: Fetch and parse web page content
- `web_search`: Search for URLs and information
- `bash`: Run browser automation scripts if needed
- `read_file`: Read local files
- `write_file`: Save extracted data

## Techniques
- Use CSS selectors or XPath for precise element selection
- Handle JavaScript-rendered content by noting limitations
- Parse JSON APIs when available instead of scraping HTML
- Save extracted data in structured formats (JSON, CSV)

## Current Task
{context.task}

## Workspace
Working directory: {context.workspace_path or 'current directory'}

Begin the browser automation task. Be methodical and handle errors gracefully."""

    def can_handle(self, task: str) -> float:
        """Score how well this agent can handle the task."""
        keywords = [
            "browse", "website", "web page", "scrape", "extract from",
            "fill form", "login", "navigate", "click", "download from",
            "automation", "screenshot", "url",
        ]
        task_lower = task.lower()
        matches = sum(1 for kw in keywords if kw in task_lower)
        return min(0.2 + (matches * 0.2), 0.95)
