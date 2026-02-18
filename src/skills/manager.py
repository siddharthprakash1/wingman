"""
Skill Manager - Discovers and manages skills.

Skills are stored as markdown files in the workspace:
    ~/.wingman/workspace/skills/<skill_name>/SKILL.md

Each skill can also have:
- config.json - Skill-specific configuration
- tools/ - Custom tool scripts for the skill
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class Skill:
    """A skill definition."""
    name: str
    description: str
    instructions: str
    triggers: list[str] = field(default_factory=list)  # Keywords that auto-activate
    tools: list[str] = field(default_factory=list)  # Required tools
    config: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_path(cls, skill_dir: Path) -> Skill | None:
        """Load a skill from a directory."""
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            return None
        
        instructions = skill_md.read_text()
        
        # Parse frontmatter if present (---\n...\n---)
        description = ""
        triggers: list[str] = []
        tools: list[str] = []
        
        if instructions.startswith("---"):
            parts = instructions.split("---", 2)
            if len(parts) >= 3:
                frontmatter = parts[1].strip()
                instructions = parts[2].strip()
                
                # Parse YAML-like frontmatter
                for line in frontmatter.split("\n"):
                    if ":" in line:
                        key, value = line.split(":", 1)
                        key = key.strip().lower()
                        value = value.strip()
                        
                        if key == "description":
                            description = value
                        elif key == "triggers":
                            triggers = [t.strip() for t in value.split(",")]
                        elif key == "tools":
                            tools = [t.strip() for t in value.split(",")]
        
        # Load config if exists
        config: dict[str, Any] = {}
        config_path = skill_dir / "config.json"
        if config_path.exists():
            try:
                config = json.loads(config_path.read_text())
            except Exception as e:
                logger.warning(f"Failed to load skill config: {e}")
        
        return cls(
            name=skill_dir.name,
            description=description or f"Skill: {skill_dir.name}",
            instructions=instructions,
            triggers=triggers,
            tools=tools,
            config=config,
        )


class SkillManager:
    """
    Manages skill discovery and activation.
    
    Skills are discovered from the workspace skills/ directory.
    They can be activated manually or auto-activated based on triggers.
    """

    def __init__(self, skills_dir: Path):
        self.skills_dir = skills_dir
        self.skills_dir.mkdir(parents=True, exist_ok=True)
        self._skills: dict[str, Skill] = {}
        self._load_skills()

    def _load_skills(self) -> None:
        """Discover and load all skills."""
        self._skills.clear()
        
        if not self.skills_dir.exists():
            return
        
        for skill_dir in self.skills_dir.iterdir():
            if skill_dir.is_dir():
                skill = Skill.from_path(skill_dir)
                if skill:
                    self._skills[skill.name] = skill
                    logger.debug(f"Loaded skill: {skill.name}")
        
        logger.info(f"Loaded {len(self._skills)} skills")

    def get_skill(self, name: str) -> Skill | None:
        """Get a skill by name."""
        return self._skills.get(name)

    def list_skills(self) -> list[str]:
        """List all available skill names."""
        return list(self._skills.keys())

    def get_all_skills(self) -> list[Skill]:
        """Get all skills."""
        return list(self._skills.values())

    def find_matching_skill(self, text: str) -> Skill | None:
        """
        Find a skill that matches the input text based on triggers.
        Returns the first matching skill or None.
        """
        text_lower = text.lower()
        
        for skill in self._skills.values():
            for trigger in skill.triggers:
                if trigger.lower() in text_lower:
                    return skill
        
        return None

    def create_skill(
        self,
        name: str,
        description: str,
        instructions: str,
        triggers: list[str] | None = None,
        tools: list[str] | None = None,
    ) -> Skill:
        """Create a new skill."""
        skill_dir = self.skills_dir / name
        skill_dir.mkdir(parents=True, exist_ok=True)
        
        # Build SKILL.md with frontmatter
        content = f"""---
description: {description}
triggers: {', '.join(triggers or [])}
tools: {', '.join(tools or [])}
---

{instructions}
"""
        
        skill_md = skill_dir / "SKILL.md"
        skill_md.write_text(content)
        
        # Reload skills
        self._load_skills()
        
        return self._skills[name]

    def delete_skill(self, name: str) -> bool:
        """Delete a skill."""
        skill_dir = self.skills_dir / name
        if skill_dir.exists():
            import shutil
            shutil.rmtree(skill_dir)
            self._load_skills()
            return True
        return False

    def reload(self) -> None:
        """Reload all skills from disk."""
        self._load_skills()
