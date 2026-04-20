"""
Centralized filesystem paths for Wingman.

Single source of truth for every ~/.wingman/* subdirectory. Prefer importing
from here over rebuilding `Path.home() / ".wingman" / ...` ad hoc.
"""

from __future__ import annotations

from datetime import date as _date
from pathlib import Path

CONFIG_DIR: Path = Path.home() / ".wingman"
CONFIG_FILE: Path = CONFIG_DIR / "config.json"

WORKSPACE_DIR: Path = CONFIG_DIR / "workspace"
SESSIONS_DIR: Path = CONFIG_DIR / "sessions"
SKILLS_DIR: Path = CONFIG_DIR / "skills"
VECTOR_STORE_DIR: Path = CONFIG_DIR / "vector_store"
LOG_DIR: Path = CONFIG_DIR / "logs"
BRIEFS_DIR: Path = CONFIG_DIR / "briefs"

SWARM_DIR: Path = CONFIG_DIR / "swarm"
SWARM_TRENDS_DIR: Path = SWARM_DIR / "trends"
SWARM_RESEARCH_DIR: Path = SWARM_DIR / "research"
SWARM_IDEAS_DIR: Path = SWARM_DIR / "ideas"
SWARM_ANALYSIS_DIR: Path = SWARM_DIR / "analysis"
SWARM_ARCHITECTURE_DIR: Path = SWARM_DIR / "architecture"
SWARM_PROJECTS_DIR: Path = SWARM_DIR / "projects"
SWARM_TESTS_DIR: Path = SWARM_DIR / "tests"
SWARM_DEVOPS_DIR: Path = SWARM_DIR / "devops"
SWARM_DOCS_DIR: Path = SWARM_DIR / "docs"
SWARM_DECISIONS_DIR: Path = SWARM_DIR / "decisions"

_ALL_DIRS: tuple[Path, ...] = (
    CONFIG_DIR,
    WORKSPACE_DIR,
    SESSIONS_DIR,
    SKILLS_DIR,
    VECTOR_STORE_DIR,
    LOG_DIR,
    BRIEFS_DIR,
    SWARM_DIR,
    SWARM_TRENDS_DIR,
    SWARM_RESEARCH_DIR,
    SWARM_IDEAS_DIR,
    SWARM_ANALYSIS_DIR,
    SWARM_ARCHITECTURE_DIR,
    SWARM_PROJECTS_DIR,
    SWARM_TESTS_DIR,
    SWARM_DEVOPS_DIR,
    SWARM_DOCS_DIR,
    SWARM_DECISIONS_DIR,
)


def ensure_dirs() -> None:
    """Create every Wingman directory if missing. Safe to call repeatedly."""
    for d in _ALL_DIRS:
        d.mkdir(parents=True, exist_ok=True)


def brief_path(for_date: _date | None = None) -> Path:
    """Path to today's (or a specific day's) morning brief markdown."""
    d = for_date or _date.today()
    BRIEFS_DIR.mkdir(parents=True, exist_ok=True)
    return BRIEFS_DIR / f"{d.isoformat()}.md"


def session_path(session_id: str) -> Path:
    """Path to a session's JSONL transcript."""
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    return SESSIONS_DIR / f"{session_id}.jsonl"
