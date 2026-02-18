"""
Coding Agent Framework - Project State Definition.

Defines the data structures for managing project state, plan, and progress.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any


class ProjectStatus(str, Enum):
    PLANNING = "planning"
    CODING = "coding"
    REVIEWING = "reviewing"
    COMPLETED = "completed"
    FAILED = "failed"


class StepStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ProjectStep:
    """A single step in the project plan."""
    id: int
    title: str
    description: str
    status: StepStatus = StepStatus.PENDING
    files: list[str] = field(default_factory=list)
    code_changes: str | None = None
    review_feedback: str | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProjectStep:
        step = cls(**data)
        step.status = StepStatus(data.get("status", "pending"))
        return step


@dataclass
class ProjectState:
    """The complete state of a coding project."""
    name: str
    prompt: str
    workspace_path: str
    status: ProjectStatus = ProjectStatus.PLANNING
    plan: list[ProjectStep] = field(default_factory=list)
    current_step_index: int = 0
    history: list[str] = field(default_factory=list)  # Log of actions
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "prompt": self.prompt,
            "workspace_path": self.workspace_path,
            "phase": self.status.value,
            "status": self.status.value,
            "plan": [s.to_dict() for s in self.plan],
            "current_step_index": self.current_step_index,
            "history": self.history,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProjectState:
        state = cls(
            name=data["name"],
            prompt=data["prompt"],
            workspace_path=data["workspace_path"],
            status=ProjectStatus(data.get("status", "planning")),
            plan=[ProjectStep.from_dict(s) for s in data.get("plan", [])],
            current_step_index=data.get("current_step_index", 0),
            history=data.get("history", []),
        )
        return state

    def save(self, path: Path) -> None:
        """Save state to a JSON file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: Path) -> ProjectState:
        """Load state from a JSON file."""
        with open(path, "r") as f:
            data = json.load(f)
        return cls.from_dict(data)
