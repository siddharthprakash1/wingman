"""
Project Manager (Orchestrator) - Coordinates the Coding Agent Framework.
"""

from __future__ import annotations

import logging
from pathlib import Path

from src.config.settings import get_settings
from src.agents.coding.state import ProjectState, ProjectStep, ProjectStatus, StepStatus
from src.agents.coding.planner import PlannerAgent
from src.agents.coding.engineer import CodingAgent
from src.agents.coding.reviewer import ReviewerAgent
from src.memory.manager import MemoryManager

logger = logging.getLogger(__name__)


class ProjectManager:
    """
    Orchestrates the entire project lifecycle:
    Planning -> Coding -> Reviewing -> Completion.
    """

    def __init__(self):
        self.settings = get_settings()
        self.memory = MemoryManager()
        self.projects_dir = self.memory.workspace / "projects"
        self.projects_dir.mkdir(exist_ok=True)
        
        # Specialized Agents
        self.planner = PlannerAgent()
        self.coder = CodingAgent()
        self.reviewer = ReviewerAgent()
        
        self.current_project: ProjectState | None = None

    def create_project(self, name: str, prompt: str) -> ProjectState:
        """Initialize a new project."""
        project_dir = self.projects_dir / name
        project_dir.mkdir(exist_ok=True)
        
        state = ProjectState(
            name=name,
            prompt=prompt,
            workspace_path=str(project_dir),
            status=ProjectStatus.PLANNING,
        )
        self.current_project = state
        self._save_state()
        logger.info(f"Created project: {name}")
        return state

    def load_project(self, name: str) -> ProjectState | None:
        """Load an existing project."""
        state_path = self.projects_dir / name / "state.json"
        if not state_path.exists():
            return None
        
        self.current_project = ProjectState.load(state_path)
        logger.info(f"Loaded project: {name}")
        return self.current_project

    def list_projects(self) -> list[str]:
        """List all available projects."""
        return [p.name for p in self.projects_dir.iterdir() if p.is_dir()]

    async def run_next_step(self) -> str:
        """
        Execute the next logical phase of the project.
        Returns a status message describing what happened.
        """
        if not self.current_project:
            return "No active project."

        state = self.current_project

        # --- PLANNING PHASE ---
        if state.status == ProjectStatus.PLANNING:
            logger.info("Starting Planning Phase...")
            try:
                plan = await self.planner.create_plan(state.prompt)
                state.plan = plan
                state.status = ProjectStatus.CODING
                state.history.append("Plan created.")
                self._save_state()
                return f"Plan created with {len(plan)} steps. Moving to Coding phase."
            except Exception as e:
                logger.error(f"Planning failed: {e}")
                return f"Planning failed: {e}"

        # --- CODING/REVIEWING PHASE ---
        if state.status in (ProjectStatus.CODING, ProjectStatus.REVIEWING):
            # Find the first non-completed step
            step = next((s for s in state.plan if s.status != StepStatus.COMPLETED), None)
            
            if not step:
                state.status = ProjectStatus.COMPLETED
                state.history.append("All steps completed.")
                self._save_state()
                return "Project completed! All steps are done."

            # Update index
            state.current_step_index = step.id - 1

            # Execute Step (Coding)
            if step.status in (StepStatus.PENDING, StepStatus.FAILED):
                logger.info(f"Coding Step {step.id}: {step.title}")
                state.status = ProjectStatus.CODING
                self._save_state()
                
                result = await self.coder.execute_step(step)
                
                if result == StepStatus.COMPLETED:
                    step.status = StepStatus.IN_PROGRESS  # Ready for review
                    state.history.append(f"Step {step.id} coded. Ready for review.")
                    state.status = ProjectStatus.REVIEWING
                    self._save_state()
                    return f"Step {step.id} implementation finished. Starting review."
                else:
                    state.history.append(f"Step {step.id} failed coding: {step.error}")
                    self._save_state()
                    return f"Step {step.id} failed implementation."

            # Review Step
            elif step.status == StepStatus.IN_PROGRESS: # Using IN_PROGRESS as "Ready for Review"
                logger.info(f"Reviewing Step {step.id}: {step.title}")
                state.status = ProjectStatus.REVIEWING
                self._save_state()
                
                passed, feedback = await self.reviewer.review_step(step)
                
                if passed:
                    step.status = StepStatus.COMPLETED
                    step.review_feedback = feedback
                    state.history.append(f"Step {step.id} passed review.")
                    state.status = ProjectStatus.CODING  # Back to coding for next step
                    self._save_state()
                    return f"Step {step.id} passed review! Moving to next step."
                else:
                    step.status = StepStatus.FAILED
                    step.review_feedback = feedback
                    step.error = f"Review Failed: {feedback}"
                    state.history.append(f"Step {step.id} failed review.")
                    state.status = ProjectStatus.CODING # Retry coding
                    self._save_state()
                    return f"Step {step.id} failed review. Sending back to engineer."

        return "Unknown state."

    def _save_state(self):
        """Save current project state."""
        if self.current_project:
            path = self.projects_dir / self.current_project.name / "state.json"
            self.current_project.save(path)
