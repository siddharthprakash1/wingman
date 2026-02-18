"""
Multi-Agent System - Specialized agents for different tasks.

OpenClaw-style agent architecture with:
- BaseAgent: Common interface for all agents
- Router: Routes tasks to appropriate agents
- Specialized Agents:
  - PlannerAgent: Breaks down complex tasks
  - CoderAgent: Writes and modifies code
  - ReviewerAgent: Reviews code quality
  - ResearchAgent: Web research and information gathering
  - BrowserAgent: Web automation and scraping
  - WriterAgent: Content creation and editing
  - DataAgent: Data analysis and visualization
  - SystemAgent: System administration tasks
"""

from src.agents.base import BaseAgent, AgentCapability, AgentContext
from src.agents.router import AgentRouter

__all__ = [
    "BaseAgent",
    "AgentCapability",
    "AgentContext",
    "AgentRouter",
]
