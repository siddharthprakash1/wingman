"""
Agent Router - Routes tasks to the most appropriate agent.

The router analyzes incoming tasks and delegates to specialized agents
based on capability matching and confidence scores.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from src.agents.base import BaseAgent, AgentCapability, AgentContext, AgentResult

logger = logging.getLogger(__name__)


@dataclass
class RouteDecision:
    """Decision about which agent should handle a task."""
    agent_name: str
    confidence: float
    reasoning: str


class AgentRouter:
    """
    Routes tasks to appropriate agents.
    
    The router maintains a registry of agents and their capabilities,
    and uses scoring to determine the best agent for each task.
    """

    def __init__(self):
        self._agents: dict[str, BaseAgent] = {}
        self._capability_map: dict[AgentCapability, list[str]] = {}

    def register(self, agent: BaseAgent) -> None:
        """Register an agent with the router."""
        self._agents[agent.name] = agent
        
        # Update capability map
        for cap in agent.capabilities:
            if cap not in self._capability_map:
                self._capability_map[cap] = []
            self._capability_map[cap].append(agent.name)
        
        logger.info(f"Registered agent: {agent.name} with capabilities: {agent.capabilities}")

    def unregister(self, agent_name: str) -> None:
        """Remove an agent from the router."""
        if agent_name in self._agents:
            agent = self._agents[agent_name]
            for cap in agent.capabilities:
                if cap in self._capability_map:
                    self._capability_map[cap].remove(agent_name)
            del self._agents[agent_name]

    def get_agent(self, name: str) -> BaseAgent | None:
        """Get an agent by name."""
        return self._agents.get(name)

    def list_agents(self) -> list[str]:
        """List all registered agent names."""
        return list(self._agents.keys())

    def get_agents_by_capability(self, capability: AgentCapability) -> list[BaseAgent]:
        """Get all agents with a specific capability."""
        agent_names = self._capability_map.get(capability, [])
        return [self._agents[name] for name in agent_names if name in self._agents]

    def route(self, task: str) -> RouteDecision:
        """
        Determine the best agent for a task.
        
        Uses confidence scoring from each agent to make the decision.
        """
        if not self._agents:
            return RouteDecision(
                agent_name="",
                confidence=0.0,
                reasoning="No agents registered",
            )
        
        # Get scores from all agents
        scores: list[tuple[str, float]] = []
        for name, agent in self._agents.items():
            try:
                score = agent.can_handle(task)
                scores.append((name, score))
            except Exception as e:
                logger.warning(f"Agent {name} scoring failed: {e}")
                scores.append((name, 0.0))
        
        # Sort by score descending
        scores.sort(key=lambda x: x[1], reverse=True)
        
        best_name, best_score = scores[0]
        
        # Build reasoning
        if len(scores) > 1:
            runner_up = scores[1]
            reasoning = (
                f"Selected '{best_name}' (score: {best_score:.2f}) "
                f"over '{runner_up[0]}' (score: {runner_up[1]:.2f})"
            )
        else:
            reasoning = f"Selected '{best_name}' (score: {best_score:.2f})"
        
        return RouteDecision(
            agent_name=best_name,
            confidence=best_score,
            reasoning=reasoning,
        )

    async def execute(
        self,
        task: str,
        context: AgentContext | None = None,
        agent_name: str | None = None,
    ) -> AgentResult:
        """
        Execute a task using the appropriate agent.
        
        Args:
            task: The task to execute
            context: Optional execution context
            agent_name: Optional specific agent to use (bypasses routing)
        """
        # Use specified agent or route
        if agent_name:
            agent = self._agents.get(agent_name)
            if not agent:
                return AgentResult(
                    success=False,
                    output=f"Unknown agent: {agent_name}. Available: {list(self._agents.keys())}",
                )
        else:
            decision = self.route(task)
            if not decision.agent_name:
                return AgentResult(
                    success=False,
                    output="No suitable agent found for this task.",
                )
            agent = self._agents[decision.agent_name]
            logger.info(f"Routed task to '{agent.name}': {decision.reasoning}")
        
        # Create context if not provided
        if context is None:
            context = AgentContext(task=task)
        else:
            context.task = task
        
        # Execute
        try:
            return await agent.execute(context)
        except Exception as e:
            logger.error(f"Agent execution failed: {e}")
            return AgentResult(
                success=False,
                output=f"Agent execution error: {e}",
            )

    def get_capabilities_summary(self) -> dict[str, Any]:
        """Get a summary of available agents and their capabilities."""
        return {
            "agents": [
                {
                    "name": agent.name,
                    "description": agent.description,
                    "capabilities": [c.value for c in agent.capabilities],
                }
                for agent in self._agents.values()
            ],
            "capability_map": {
                cap.value: agents
                for cap, agents in self._capability_map.items()
            },
        }


def create_default_router() -> AgentRouter:
    """Create a router with all default agents registered."""
    from src.agents.research import ResearchAgent
    from src.agents.browser import BrowserAgent
    from src.agents.writer import WriterAgent
    from src.agents.data import DataAgent
    from src.agents.system import SystemAgent
    from src.agents.coding.planner import PlannerAgent
    from src.agents.coding.engineer import CodingAgent
    from src.agents.coding.reviewer import ReviewerAgent
    
    router = AgentRouter()
    
    # Register all agents
    router.register(ResearchAgent())
    router.register(BrowserAgent())
    router.register(WriterAgent())
    router.register(DataAgent())
    router.register(SystemAgent())
    router.register(PlannerAgent())
    router.register(CodingAgent())
    router.register(ReviewerAgent())
    
    return router
