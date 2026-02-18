"""
Engineer/Coding Agent - Implements code based on plans or direct requests.

The Engineer writes, modifies, and debugs code. It can work autonomously
on implementation tasks using filesystem and shell tools.
"""

from __future__ import annotations

import logging
from typing import Any

from src.agents.base import BaseAgent, AgentCapability, AgentContext, AgentResult
from src.config.settings import get_settings
from src.providers.base import Message
from src.providers.manager import ProviderManager
from src.tools.registry import create_default_registry
from src.agents.coding.state import ProjectStep, StepStatus

logger = logging.getLogger(__name__)


class CodingAgent(BaseAgent):
    """Agent responsible for writing and modifying code."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.settings = get_settings()
        self.provider_manager = ProviderManager(self.settings)
        self.tool_registry = create_default_registry()

    @property
    def name(self) -> str:
        return "engineer"

    @property
    def description(self) -> str:
        return "Writes, modifies, and debugs code based on specifications."

    @property
    def capabilities(self) -> list[AgentCapability]:
        return [AgentCapability.CODING]

    def get_allowed_tools(self) -> list[str]:
        return [
            "read_file", "write_file", "edit_file", "list_dir",
            "bash", "web_search",
        ]

    def get_system_prompt(self, context: AgentContext) -> str:
        return f"""You are an Expert Software Engineer.

## Your Role
You implement code based on specifications. You:
- Write clean, well-documented code
- Follow best practices and conventions
- Handle errors appropriately
- Test your implementations

## Guidelines
1. Read existing code first to understand patterns
2. Use consistent styling with the codebase
3. Add appropriate error handling
4. Verify your changes compile/run
5. Keep changes focused and minimal

## Available Tools
- `read_file`: Read file contents
- `write_file`: Create new files
- `edit_file`: Modify existing files
- `list_dir`: Browse directories
- `bash`: Run commands (compile, test, etc.)

## Workspace
Working directory: {context.workspace_path or 'current directory'}

## Current Task
{context.task}

Work autonomously. When done, summarize what you implemented."""

    def can_handle(self, task: str) -> float:
        keywords = [
            "code", "implement", "create", "build", "fix", "debug",
            "function", "class", "module", "api", "feature", "bug",
            "refactor", "optimize", "program", "develop",
        ]
        task_lower = task.lower()
        matches = sum(1 for kw in keywords if kw in task_lower)
        return min(0.35 + (matches * 0.12), 0.95)

    async def execute_step(self, step: ProjectStep) -> StepStatus:
        """Execute the given step by writing code/running commands."""
        step.status = StepStatus.IN_PROGRESS
        
        system_prompt = (
            "You are an expert Software Engineer.\n"
            "Your task is to implement the following step from the project plan:\n"
            f"**Title**: {step.title}\n"
            f"**Description**: {step.description}\n"
            f"**Target Files**: {', '.join(step.files)}\n"
            "\n"
            "You have access to filesystem and shell tools.\n"
            "1. Create/Edit necessary files.\n"
            "2. Run verification commands if applicable (e.g., python -m py_compile).\n"
            "3. Once complete, call the 'task_complete' tool (simulated by just stopping).\n"
            "\n"
            "Work autonomously. Do not ask for user input unless absolutely necessary."
        )

        messages = [
            Message(role="system", content=system_prompt),
            Message(role="user", content="Start implementation."),
        ]

        # Tool definitions
        tools = self.tool_registry.get_definitions()
        
        # Inner loop for tool execution
        max_iterations = 15
        iteration = 0
        provider = self.provider_manager.get_provider("openai")

        while iteration < max_iterations:
            iteration += 1
            logger.info(f"Coding Agent iteration {iteration} for step {step.id}")

            try:
                response = await provider.chat(
                    messages=messages,
                    tools=tools,
                    temperature=0.2,  # Lower temp for coding
                )
            except Exception as e:
                logger.error(f"Coding Agent LLM error: {e}")
                step.error = str(e)
                return StepStatus.FAILED

            # Add assistant response to history
            assistant_msg = Message(
                role="assistant",
                content=response.content,
                tool_calls=response.tool_calls,
            )
            messages.append(assistant_msg)

            if response.has_tool_calls:
                for tool_call in response.tool_calls:
                    logger.info(f"Coding tool call: {tool_call.name}")
                    result = await self.tool_registry.execute(tool_call)
                    
                    # Add result
                    messages.append(Message(
                        role="tool",
                        content=result,
                        tool_call_id=tool_call.id,
                        name=tool_call.name,
                    ))
            else:
                # No tool calls usually means completion or asking for info
                # We'll treat a text response as "Done" if it says so, or continue if ambiguous
                # For simplicity, if it stops calling tools, we assume it's done for this step
                if "done" in response.content.lower() or "complete" in response.content.lower():
                    step.status = StepStatus.COMPLETED
                    step.code_changes = response.content
                    return StepStatus.COMPLETED
                
                # If just text, maybe it's thinking. Let's nudge it.
                messages.append(Message(role="user", content="Continue if there is more work, or say 'Task Complete'."))

        step.error = "Max iterations reached"
        return StepStatus.FAILED
