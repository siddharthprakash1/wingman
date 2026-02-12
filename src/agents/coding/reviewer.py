"""
Reviewer Agent - Validates the code implementation.
"""

from __future__ import annotations

import logging

from src.config.settings import get_settings
from src.providers.base import Message
from src.providers.manager import ProviderManager
from src.tools.registry import create_default_registry
from src.agents.coding.state import ProjectStep, StepStatus

logger = logging.getLogger(__name__)


class ReviewerAgent:
    """Agent responsible for reviewing code changes."""

    def __init__(self):
        self.settings = get_settings()
        self.provider_manager = ProviderManager(self.settings)
        self.tool_registry = create_default_registry()

    async def review_step(self, step: ProjectStep) -> tuple[bool, str]:
        """
        Review the implementation of a step.
        Returns: (passed: bool, feedback: str)
        """
        system_prompt = (
            "You are a Senior Code Reviewer.\n"
            "Your task is to verify if the implementation matches the requirements.\n"
            f"**Step**: {step.title}\n"
            f"**Description**: {step.description}\n"
            f"**Files**: {', '.join(step.files)}\n"
            "\n"
            "1. Read the modified files (using `read_file`).\n"
            "2. If applicable, run basic checks (e.g., check syntax, or run a test).\n"
            "3. Assess if the code meets the requirements.\n"
            "4. Provide a distinct 'PASS' or 'FAIL' verdict.\n"
            "5. If FAIL, provide clear feedback on what to fix.\n"
        )

        messages = [
            Message(role="system", content=system_prompt),
            Message(role="user", content="Please review the changes."),
        ]

        tools = self.tool_registry.get_definitions()
        provider = self.provider_manager.get_provider()
        
        # Max review iterations (read file -> think -> verdict)
        max_iterations = 5
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            response = await provider.chat(messages, tools=tools, temperature=0.1)
            
            messages.append(Message(role="assistant", content=response.content, tool_calls=response.tool_calls))

            if response.has_tool_calls:
                for tool_call in response.tool_calls:
                    result = await self.tool_registry.execute(tool_call)
                    messages.append(Message(role="tool", content=result, tool_call_id=tool_call.id, name=tool_call.name))
            else:
                # Interpret final verdict
                content = response.content.upper()
                if "PASS" in content:
                    return True, response.content
                elif "FAIL" in content:
                    return False, response.content
                
                # If ambiguous, ask for verdict
                messages.append(Message(role="user", content="Please state clearly: PASS or FAIL?"))

        return False, "Review inconclusive/timed out"
