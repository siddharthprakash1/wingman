"""
Tool Registry — register and dispatch tools for the agent.

Tools are registered with decorators and automatically converted
to OpenAI-compatible function calling format for the LLM.
"""

from __future__ import annotations

import asyncio
import inspect
import json
import logging
from typing import Any, Callable, Coroutine

from src.providers.base import ToolCall, ToolDefinition

logger = logging.getLogger(__name__)

# Default timeout for tool execution (5 minutes)
TOOL_TIMEOUT = 300


# Type for tool functions
ToolFunc = Callable[..., Coroutine[Any, Any, str] | str]


class ToolRegistry:
    """
    Registry of available tools.

    Tools are registered with metadata (name, description, parameters)
    and can be dispatched by name.
    """

    def __init__(self):
        self._tools: dict[str, RegisteredTool] = {}

    def register(
        self,
        name: str,
        description: str,
        parameters: dict[str, Any],
        func: ToolFunc,
    ) -> None:
        """Register a tool function."""
        self._tools[name] = RegisteredTool(
            name=name,
            description=description,
            parameters=parameters,
            func=func,
        )
        logger.debug(f"Registered tool: {name}")

    def get_definitions(self) -> list[ToolDefinition]:
        """Get all tool definitions for the LLM."""
        return [
            ToolDefinition(
                name=tool.name,
                description=tool.description,
                parameters=tool.parameters,
            )
            for tool in self._tools.values()
        ]

    async def execute(self, tool_call: ToolCall, timeout: int = TOOL_TIMEOUT) -> str:
        """
        Execute a tool call and return the result as a string.

        Args:
            tool_call: The tool call from the LLM.
            timeout: Maximum execution time in seconds (default: 300).

        Returns:
            The tool result as a string.
        """
        tool = self._tools.get(tool_call.name)
        if not tool:
            return f"❌ Unknown tool: {tool_call.name}. Available: {list(self._tools.keys())}"

        try:
            logger.info(f"Executing tool: {tool_call.name} with args: {tool_call.arguments}")
            result = tool.func(**tool_call.arguments)

            # Handle async functions with timeout
            if inspect.isawaitable(result):
                try:
                    result = await asyncio.wait_for(result, timeout=timeout)
                except asyncio.TimeoutError:
                    return f"❌ Tool '{tool_call.name}' timed out after {timeout}s"

            # Ensure result is a string
            if not isinstance(result, str):
                result = json.dumps(result, indent=2, ensure_ascii=False)

            # Truncate very long results
            max_len = 50000
            if len(result) > max_len:
                result = result[:max_len] + f"\n... (truncated, {len(result)} total chars)"

            return result

        except asyncio.TimeoutError:
            return f"❌ Tool '{tool_call.name}' timed out after {timeout}s"
        except Exception as e:
            error_msg = f"❌ Tool '{tool_call.name}' failed: {type(e).__name__}: {e}"
            logger.error(error_msg)
            return error_msg

    def list_tools(self) -> list[str]:
        """List all registered tool names."""
        return list(self._tools.keys())


class RegisteredTool:
    """A registered tool with its metadata and function."""

    def __init__(
        self,
        name: str,
        description: str,
        parameters: dict[str, Any],
        func: ToolFunc,
    ):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.func = func


def create_default_registry() -> ToolRegistry:
    """
    Create a ToolRegistry with all built-in tools registered.

    This is the main entry point — it imports and registers all
    built-in tools (shell, filesystem, web_search, etc.).
    """
    from src.tools.shell import register_shell_tools
    from src.tools.filesystem import register_filesystem_tools
    from src.tools.web_search import register_web_search_tools
    from src.tools.cron import register_cron_tools
    # New tools
    from src.tools.macos import register_macos_tools
    from src.tools.media import register_media_tools
    from src.tools.desktop import register_desktop_tools
    from src.tools.system_pkg import register_package_tools
    # AI-powered extraction and browser tools
    from src.tools.extraction import register_extraction_tools
    from src.tools.browser_use import register_browser_use_tools
    # Document ingestion and knowledge base tools
    from src.tools.documents import register_document_tools
    # Multi-agent communication tools
    from src.tools.sessions import register_session_tools

    registry = ToolRegistry()
    register_shell_tools(registry)
    register_filesystem_tools(registry)
    register_web_search_tools(registry)
    register_cron_tools(registry)
    # Register new tools
    register_macos_tools(registry)
    register_media_tools(registry)
    register_desktop_tools(registry)
    register_package_tools(registry)
    # Register AI-powered tools
    register_extraction_tools(registry)
    register_browser_use_tools(registry)
    # Register document/knowledge base tools
    register_document_tools(registry)
    # Register multi-agent session tools
    register_session_tools(registry)

    return registry
