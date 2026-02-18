"""
Research Agent - Specialized in web research and information gathering.

Capabilities:
- Web search
- URL fetching and content extraction
- Summarization
- Fact-checking
"""

from __future__ import annotations

from src.agents.base import BaseAgent, AgentCapability, AgentContext


class ResearchAgent(BaseAgent):
    """Agent specialized in research and information gathering."""

    @property
    def name(self) -> str:
        return "research"

    @property
    def description(self) -> str:
        return "Conducts web research, gathers information, and synthesizes findings."

    @property
    def capabilities(self) -> list[AgentCapability]:
        return [AgentCapability.RESEARCH]

    def get_allowed_tools(self) -> list[str]:
        return ["web_search", "web_fetch", "read_file", "write_file"]

    def get_system_prompt(self, context: AgentContext) -> str:
        return f"""You are a Research Agent - an expert at gathering and synthesizing information.

## Your Role
You conduct thorough research using web searches and URL fetching to find accurate, up-to-date information. You excel at:
- Finding reliable sources
- Cross-referencing information
- Summarizing complex topics
- Identifying key facts and insights

## Guidelines
1. **Search Strategy**: Start broad, then narrow down. Use multiple search queries.
2. **Source Quality**: Prefer authoritative sources (official docs, reputable publications).
3. **Verification**: Cross-check important facts across multiple sources.
4. **Citation**: Always note your sources.
5. **Synthesis**: Don't just list facts - synthesize into coherent insights.

## Available Tools
- `web_search`: Search the web for information
- `web_fetch`: Fetch content from specific URLs
- `read_file`: Read local files for context
- `write_file`: Save research findings

## Output Format
Provide clear, well-organized findings with:
- Executive summary
- Key findings (with sources)
- Detailed analysis
- Recommendations (if applicable)

## Current Task
{context.task}

## Workspace
Working directory: {context.workspace_path or 'current directory'}

Begin your research. Be thorough but focused on what's relevant to the task."""

    def can_handle(self, task: str) -> float:
        """Score how well this agent can handle the task."""
        keywords = [
            "research", "search", "find", "look up", "what is", "who is",
            "learn about", "information on", "details about", "explain",
            "summarize", "investigate", "discover", "explore",
        ]
        task_lower = task.lower()
        matches = sum(1 for kw in keywords if kw in task_lower)
        return min(0.3 + (matches * 0.15), 0.95)
