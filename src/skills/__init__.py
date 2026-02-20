"""
Skills System - Modular task-specific capabilities.

Skills are like "playbooks" - structured guides for accomplishing
specific tasks using the available tools. They're activated on-demand
and can be extended through the ClawHub-style SkillHub system.
"""

from src.skills.hub import SkillHub, Skill, SkillManifest
from src.skills.manager import SkillManager

__all__ = ["SkillHub", "Skill", "SkillManifest", "SkillManager"]
and injected into the system prompt only when relevant.

Skill structure:
    skills/
    ├── research/
    │   └── SKILL.md
    ├── coding/
    │   └── SKILL.md
    ├── writing/
    │   └── SKILL.md
    └── ...
"""

from src.skills.manager import SkillManager, Skill

__all__ = ["SkillManager", "Skill"]
