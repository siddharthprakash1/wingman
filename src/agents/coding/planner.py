"""
Planner Agent - Specialized in breaking down tasks into steps.
"""

from __future__ import annotations

import json
from typing import Any

from src.config.settings import get_settings
from src.providers.base import Message
from src.providers.manager import ProviderManager
from src.agents.coding.state import ProjectStep, StepStatus


class PlannerAgent:
    """Agent responsible for creating a development plan."""

    def __init__(self):
        self.settings = get_settings()
        self.provider_manager = ProviderManager(self.settings)

    async def create_plan(self, request: str) -> list[ProjectStep]:
        """Generate a list of steps for the given request."""
        system_prompt = (
            "You are an expert Software Architect.\n"
            "Your goal is to break down a complex user request into a step-by-step implementation plan.\n"
            "Each step should be clear, actionable, and focus on a specific component or file.\n"
            "Output MUST be a valid JSON array of objects with the following keys:\n"
            "- title: Short summary of the step\n"
            "- description: Detailed instructions for the developer\n"
            "- files: List of files to be created or modified (e.g., ['src/main.py'])\n"
            "\n"
            "Example Output:\n"
            "[\n"
            "  {\n"
            "    \"title\": \"Create Project Structure\",\n"
            "    \"description\": \"Set up the main directory and basic files.\",\n"
            "    \"files\": [\"README.md\", \"requirements.txt\"]\n"
            "  }\n"
            "]"
        )

        messages = [
            Message(role="system", content=system_prompt),
            Message(role="user", content=f"Create a plan for: {request}"),
        ]

        # Use Kimi (or default provider)
        provider = self.provider_manager.get_provider()
        response = await provider.chat(messages, temperature=0.7)

        content = response.content.strip()
        # Handle potential markdown code blocks in response
        if content.startswith("```json"):
            content = content.replace("```json", "").replace("```", "")
        elif content.startswith("```"):
            content = content.replace("```", "")
            
        try:
            steps_data = json.loads(content)
            steps = []
            for i, step_data in enumerate(steps_data):
                steps.append(
                    ProjectStep(
                        id=i + 1,
                        title=step_data.get("title", f"Step {i+1}"),
                        description=step_data.get("description", ""),
                        files=step_data.get("files", []),
                        status=StepStatus.PENDING,
                    )
                )
            return steps
        except json.JSONDecodeError:
            # Fallback if JSON fails - create one big step
            return [
                ProjectStep(
                    id=1,
                    title="Execute Request",
                    description=response.content,
                    files=[],
                    status=StepStatus.PENDING,
                )
            ]
