"""
Base Agent - Common interface for all specialized agents.

Each agent has:
- A specific role/capability
- Access to tools relevant to their domain
- A specialized system prompt
- The ability to delegate to other agents
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, AsyncIterator

from src.core.protocol import Message, ToolCall, ToolDefinition, LLMResponse
from src.config.settings import Settings, get_settings
from src.providers.manager import ProviderManager
from src.tools.registry import ToolRegistry, create_default_registry

logger = logging.getLogger(__name__)


class AgentCapability(str, Enum):
    """Capabilities that agents can have."""
    PLANNING = "planning"           # Task decomposition
    CODING = "coding"               # Code generation/modification
    REVIEWING = "reviewing"         # Code review
    RESEARCH = "research"           # Web research
    BROWSER = "browser"             # Web automation
    WRITING = "writing"             # Content creation
    DATA = "data"                   # Data analysis
    SYSTEM = "system"               # System administration
    MEMORY = "memory"               # Memory management
    GENERAL = "general"             # General conversation


@dataclass
class AgentContext:
    """Context passed to agents for task execution."""
    task: str                               # The task to perform
    session_id: str = ""                    # Current session
    parent_agent: str | None = None         # Agent that delegated this task
    workspace_path: str = ""                # Working directory
    max_iterations: int = 25                # Max tool iterations
    temperature: float = 0.7                # LLM temperature
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentResult:
    """Result from agent execution."""
    success: bool
    output: str
    artifacts: list[str] = field(default_factory=list)  # Created files, etc.
    metadata: dict[str, Any] = field(default_factory=dict)
    delegated_to: str | None = None  # If task was delegated


class BaseAgent(ABC):
    """
    Abstract base class for all agents.
    
    Agents are specialized executors that:
    1. Have domain-specific knowledge (via system prompts)
    2. Can use tools relevant to their domain
    3. Can delegate to other agents
    4. Return structured results
    """

    def __init__(
        self,
        settings: Settings | None = None,
        tool_registry: ToolRegistry | None = None,
        provider_name: str | None = None,
    ):
        self.settings = settings or get_settings()
        self.provider_manager = ProviderManager(self.settings)
        self.tool_registry = tool_registry or create_default_registry()
        self.provider_name = provider_name  # Specific provider for this agent

    @property
    @abstractmethod
    def name(self) -> str:
        """Agent name identifier."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of the agent."""
        ...

    @property
    @abstractmethod
    def capabilities(self) -> list[AgentCapability]:
        """List of capabilities this agent has."""
        ...

    @abstractmethod
    def get_system_prompt(self, context: AgentContext) -> str:
        """Build the system prompt for this agent."""
        ...

    def get_allowed_tools(self) -> list[str]:
        """
        Get list of tool names this agent can use.
        Override to restrict tools. Empty list = all tools.
        """
        return []

    def get_tool_definitions(self) -> list[ToolDefinition]:
        """Get filtered tool definitions for this agent."""
        all_tools = self.tool_registry.get_definitions()
        allowed = self.get_allowed_tools()
        
        if not allowed:
            return all_tools
        
        return [t for t in all_tools if t.name in allowed]

    async def execute(self, context: AgentContext) -> AgentResult:
        """
        Execute the agent's task.
        
        This is the main entry point. Runs the agent loop:
        1. Build system prompt
        2. Call LLM
        3. Execute tools
        4. Repeat until done or max iterations
        """
        logger.info(f"Agent '{self.name}' starting task: {context.task[:100]}")
        
        system_prompt = self.get_system_prompt(context)
        messages = [
            Message(role="system", content=system_prompt),
            Message(role="user", content=context.task),
        ]
        
        tools = self.get_tool_definitions()
        provider = self.provider_manager.get_provider(self.provider_name)
        
        iteration = 0
        artifacts: list[str] = []
        
        while iteration < context.max_iterations:
            iteration += 1
            logger.debug(f"Agent '{self.name}' iteration {iteration}")
            
            try:
                response = await provider.chat(
                    messages=messages,
                    tools=tools,
                    temperature=context.temperature,
                )
            except Exception as e:
                logger.error(f"Agent '{self.name}' LLM error: {e}")
                return AgentResult(
                    success=False,
                    output=f"LLM error: {e}",
                )
            
            # Add assistant response
            messages.append(Message(
                role="assistant",
                content=response.content,
                tool_calls=response.tool_calls,
            ))
            
            if response.has_tool_calls:
                for tool_call in response.tool_calls:
                    logger.info(f"Agent '{self.name}' calling tool: {tool_call.name}")
                    
                    result = await self.tool_registry.execute(tool_call)
                    
                    # Track file artifacts
                    if tool_call.name in ("write_file", "edit_file"):
                        path = tool_call.arguments.get("path", "")
                        if path and "✅" in result:
                            artifacts.append(path)
                    
                    messages.append(Message(
                        role="tool",
                        content=result,
                        tool_call_id=tool_call.id,
                        name=tool_call.name,
                    ))
                
                continue
            
            else:
                # No tool calls - agent is done
                return AgentResult(
                    success=True,
                    output=response.content,
                    artifacts=artifacts,
                )
        
        # Max iterations reached
        return AgentResult(
            success=False,
            output=f"Max iterations ({context.max_iterations}) reached",
            artifacts=artifacts,
        )

    async def execute_stream(
        self,
        context: AgentContext,
    ) -> AsyncIterator[str]:
        """
        Execute with streaming output.
        Yields text chunks as they arrive.
        """
        system_prompt = self.get_system_prompt(context)
        messages = [
            Message(role="system", content=system_prompt),
            Message(role="user", content=context.task),
        ]
        
        provider = self.provider_manager.get_provider(self.provider_name)
        
        async for chunk in provider.chat_stream(
            messages=messages,
            temperature=context.temperature,
        ):
            yield chunk

    def can_handle(self, task: str) -> float:
        """
        Return a confidence score (0-1) for handling this task.
        Used by the router to select the best agent.
        """
        # Default implementation - subclasses should override
        return 0.5


class DelegatingAgent(BaseAgent):
    """
    An agent that can delegate tasks to other agents.
    
    This is used for complex tasks that require multiple
    specialized agents working together.
    """

    def __init__(
        self,
        agents: dict[str, BaseAgent],
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.agents = agents

    async def delegate(
        self,
        agent_name: str,
        task: str,
        context: AgentContext,
    ) -> AgentResult:
        """Delegate a subtask to another agent."""
        agent = self.agents.get(agent_name)
        if not agent:
            return AgentResult(
                success=False,
                output=f"Unknown agent: {agent_name}",
            )
        
        # Create child context
        child_context = AgentContext(
            task=task,
            session_id=context.session_id,
            parent_agent=self.name,
            workspace_path=context.workspace_path,
            max_iterations=context.max_iterations,
            metadata=context.metadata,
        )
        
        return await agent.execute(child_context)
