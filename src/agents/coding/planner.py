"""
Planner Agent - Specialized in breaking down tasks into implementation steps.

The Planner analyzes complex requests and creates structured, actionable
plans that other agents (Engineer, Reviewer) can execute.
"""

from __future__ import annotations

import json
from typing import Any

from src.agents.base import BaseAgent, AgentCapability, AgentContext, AgentResult
from src.config.settings import get_settings
from src.providers.base import Message
from src.providers.manager import ProviderManager
from src.agents.coding.state import ProjectStep, StepStatus


class PlannerAgent(BaseAgent):
    """Agent responsible for creating development plans."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.settings = get_settings()
        self.provider_manager = ProviderManager(self.settings)

    @property
    def name(self) -> str:
        return "planner"

    @property
    def description(self) -> str:
        return "Breaks down complex tasks into structured implementation plans."

    @property
    def capabilities(self) -> list[AgentCapability]:
        return [AgentCapability.PLANNING]

    def get_allowed_tools(self) -> list[str]:
        return ["read_file", "list_dir", "web_search"]

    def get_system_prompt(self, context: AgentContext) -> str:
        return """You are a Software Architect and Planning Agent.

Your role is to analyze complex requests and create structured, actionable plans.

## Planning Principles
1. Break down into atomic, testable steps
2. Order steps by dependencies
3. Identify files to create/modify
4. Consider edge cases and error handling
5. Include testing steps

## Output Format
Provide a JSON array of steps:
```json
[
  {
    "title": "Step title",
    "description": "Detailed description",
    "files": ["path/to/file.py"]
  }
]
```

Be thorough but practical. Each step should be completable in one coding session."""

    def can_handle(self, task: str) -> float:
        keywords = ["plan", "design", "architect", "break down", "structure", "organize"]
        task_lower = task.lower()
        matches = sum(1 for kw in keywords if kw in task_lower)
        return min(0.3 + (matches * 0.15), 0.9)

    async def create_plan(self, request: str) -> list[ProjectStep]:
        """Generate a list of steps for the given request."""
        system_prompt = (
            "You are an expert Software Architect.\n"
            "Your goal is to break down a complex user request into a step-by-step implementation plan.\n"
            "Each step should be clear, actionable, and focus on a specific component or file.\n"
            "Output MUST be a valid JSON array of objects with the following keys:\n"
            "- title: Short summary of the step\n"
            "- description: Detailed instructions for the developer\n"
            "- files: List of files to be created or modified (e.g., ['src/apps/new_project/main.py'])\n"
            "\n"
            "IMPORTANT: When creating a NEW standalone application or game, ALWAYS create it in a new subdirectory under `src/apps/<project_name>/`. Do NOT modify the root `src/` directory unless specifically asked to edit the framework itself.\n"
            "\n"
            "Example Output:\n"
            "[\n"
            "  {\n"
            "    \"title\": \"Create Project Structure\",\n"
            "    \"description\": \"Set up the main directory and basic files in src/apps/my_new_app.\",\n"
            "    \"files\": [\"src/apps/my_new_app/README.md\", \"src/apps/my_new_app/requirements.txt\"]\n"
            "  }\n"
            "]"
        )

        messages = [
            Message(role="system", content=system_prompt),
            Message(role="user", content=f"Create a plan for: {request}"),
        ]

        # Use OpenAI (Strong Model)
        provider = self.provider_manager.get_provider("openai")
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
