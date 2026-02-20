"""
Skill Hub - ClawHub-style community skill discovery and management.

Enables discovering, installing, and hot-reloading community-contributed
skills that extend Wingman's capabilities.
"""

from __future__ import annotations

import asyncio
import hashlib
import importlib
import json
import logging
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

logger = logging.getLogger(__name__)


@dataclass
class SkillManifest:
    """Skill metadata and configuration."""
    
    name: str
    version: str
    description: str
    author: str
    dependencies: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
    entry_point: str = "register_tools"  # Function to call for registration
    tags: list[str] = field(default_factory=list)
    license: str = "MIT"
    repository: str = ""
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SkillManifest:
        """Create manifest from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "dependencies": self.dependencies,
            "tools": self.tools,
            "entry_point": self.entry_point,
            "tags": self.tags,
            "license": self.license,
            "repository": self.repository,
        }


@dataclass
class Skill:
    """A loaded skill with metadata."""
    
    manifest: SkillManifest
    module: Any
    path: Path
    loaded_at: datetime = field(default_factory=datetime.now)
    enabled: bool = True
    
    def get_checksum(self) -> str:
        """Get file checksum for hot-reload detection."""
        if not self.path.exists():
            return ""
        content = self.path.read_bytes()
        return hashlib.sha256(content).hexdigest()


class SkillHub:
    """
    ClawHub-style skill management system.
    
    Features:
    - Discover and install community skills
    - Hot-reload skills when files change
    - Dependency management
    - Skill versioning and updates
    """
    
    def __init__(self, skills_dir: Path | None = None):
        self.skills_dir = skills_dir or Path.home() / ".wingman" / "skills"
        self.skills_dir.mkdir(parents=True, exist_ok=True)
        
        self._loaded_skills: dict[str, Skill] = {}
        self._file_checksums: dict[str, str] = {}
        self._hot_reload_enabled = True
        self._watcher_task: asyncio.Task | None = None
    
    def discover_local_skills(self) -> list[SkillManifest]:
        """Discover skills installed locally."""
        manifests = []
        
        for skill_dir in self.skills_dir.iterdir():
            if not skill_dir.is_dir():
                continue
            
            manifest_path = skill_dir / "manifest.json"
            if manifest_path.exists():
                try:
                    data = json.loads(manifest_path.read_text())
                    manifest = SkillManifest.from_dict(data)
                    manifests.append(manifest)
                except Exception as e:
                    logger.error(f"Failed to load manifest for {skill_dir.name}: {e}")
        
        return manifests
    
    def load_skill(self, skill_name: str) -> Skill:
        """
        Load a skill by name.
        
        Args:
            skill_name: Name of the skill to load
            
        Returns:
            Loaded Skill instance
        """
        skill_dir = self.skills_dir / skill_name
        if not skill_dir.exists():
            raise FileNotFoundError(f"Skill not found: {skill_name}")
        
        # Load manifest
        manifest_path = skill_dir / "manifest.json"
        if not manifest_path.exists():
            raise FileNotFoundError(f"Manifest not found for skill: {skill_name}")
        
        manifest_data = json.loads(manifest_path.read_text())
        manifest = SkillManifest.from_dict(manifest_data)
        
        # Load Python module
        init_file = skill_dir / "__init__.py"
        if not init_file.exists():
            raise FileNotFoundError(f"Skill module not found: {skill_name}/__init__.py")
        
        spec = importlib.util.spec_from_file_location(
            f"wingman.skills.{skill_name}",
            init_file
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Create skill instance
        skill = Skill(
            manifest=manifest,
            module=module,
            path=init_file,
        )
        
        # Store checksum for hot-reload
        self._file_checksums[skill_name] = skill.get_checksum()
        
        self._loaded_skills[skill_name] = skill
        logger.info(f"Loaded skill: {skill_name} v{manifest.version}")
        
        return skill
    
    def unload_skill(self, skill_name: str) -> None:
        """Unload a skill."""
        if skill_name in self._loaded_skills:
            del self._loaded_skills[skill_name]
            self._file_checksums.pop(skill_name, None)
            logger.info(f"Unloaded skill: {skill_name}")
    
    def reload_skill(self, skill_name: str) -> Skill:
        """Reload a skill (hot-reload)."""
        logger.info(f"Reloading skill: {skill_name}")
        self.unload_skill(skill_name)
        return self.load_skill(skill_name)
    
    def register_skill_tools(self, skill_name: str, registry: Any) -> None:
        """
        Register a skill's tools with the tool registry.
        
        Args:
            skill_name: Name of the skill
            registry: ToolRegistry instance
        """
        if skill_name not in self._loaded_skills:
            raise ValueError(f"Skill not loaded: {skill_name}")
        
        skill = self._loaded_skills[skill_name]
        entry_point = skill.manifest.entry_point
        
        if not hasattr(skill.module, entry_point):
            raise AttributeError(
                f"Skill {skill_name} missing entry point: {entry_point}"
            )
        
        register_func = getattr(skill.module, entry_point)
        register_func(registry)
        
        logger.info(f"Registered tools from skill: {skill_name}")
    
    async def check_for_updates(self) -> dict[str, bool]:
        """
        Check all loaded skills for file changes (for hot-reload).
        
        Returns:
            Dict mapping skill names to whether they changed
        """
        changes = {}
        
        for skill_name, skill in self._loaded_skills.items():
            if not skill.enabled:
                continue
            
            current_checksum = skill.get_checksum()
            old_checksum = self._file_checksums.get(skill_name, "")
            
            if current_checksum != old_checksum:
                changes[skill_name] = True
                logger.info(f"Detected changes in skill: {skill_name}")
            else:
                changes[skill_name] = False
        
        return changes
    
    async def hot_reload_watcher(self, check_interval: int = 5) -> None:
        """
        Background task that watches for skill file changes and hot-reloads.
        
        Args:
            check_interval: Seconds between checks (default: 5)
        """
        logger.info("Starting skill hot-reload watcher")
        
        while self._hot_reload_enabled:
            try:
                changes = await self.check_for_updates()
                
                for skill_name, changed in changes.items():
                    if changed:
                        try:
                            self.reload_skill(skill_name)
                        except Exception as e:
                            logger.error(f"Failed to reload skill {skill_name}: {e}")
                
                await asyncio.sleep(check_interval)
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Hot-reload watcher error: {e}")
                await asyncio.sleep(check_interval)
        
        logger.info("Stopped skill hot-reload watcher")
    
    def start_hot_reload(self, check_interval: int = 5) -> None:
        """Start the hot-reload watcher."""
        if self._watcher_task and not self._watcher_task.done():
            logger.warning("Hot-reload watcher already running")
            return
        
        try:
            loop = asyncio.get_event_loop()
            self._watcher_task = loop.create_task(
                self.hot_reload_watcher(check_interval)
            )
        except RuntimeError:
            logger.error("No event loop available for hot-reload watcher")
    
    def stop_hot_reload(self) -> None:
        """Stop the hot-reload watcher."""
        self._hot_reload_enabled = False
        
        if self._watcher_task and not self._watcher_task.done():
            self._watcher_task.cancel()
    
    def get_skill_info(self, skill_name: str) -> dict[str, Any]:
        """Get detailed information about a skill."""
        if skill_name not in self._loaded_skills:
            raise ValueError(f"Skill not loaded: {skill_name}")
        
        skill = self._loaded_skills[skill_name]
        return {
            "name": skill.manifest.name,
            "version": skill.manifest.version,
            "description": skill.manifest.description,
            "author": skill.manifest.author,
            "tools": skill.manifest.tools,
            "dependencies": skill.manifest.dependencies,
            "tags": skill.manifest.tags,
            "enabled": skill.enabled,
            "loaded_at": skill.loaded_at.isoformat(),
            "path": str(skill.path),
        }
    
    def list_loaded_skills(self) -> list[str]:
        """List all currently loaded skills."""
        return list(self._loaded_skills.keys())
    
    def install_skill(self, source_path: Path, skill_name: str) -> None:
        """
        Install a skill from a source directory.
        
        Args:
            source_path: Path to skill source directory
            skill_name: Name for the installed skill
        """
        if not source_path.exists():
            raise FileNotFoundError(f"Source path not found: {source_path}")
        
        dest_path = self.skills_dir / skill_name
        
        if dest_path.exists():
            raise FileExistsError(f"Skill already installed: {skill_name}")
        
        # Copy skill files
        shutil.copytree(source_path, dest_path)
        logger.info(f"Installed skill: {skill_name} from {source_path}")
    
    def uninstall_skill(self, skill_name: str) -> None:
        """Uninstall a skill."""
        # Unload if loaded
        if skill_name in self._loaded_skills:
            self.unload_skill(skill_name)
        
        # Remove files
        skill_dir = self.skills_dir / skill_name
        if skill_dir.exists():
            shutil.rmtree(skill_dir)
            logger.info(f"Uninstalled skill: {skill_name}")


# Global skill hub instance
_skill_hub: SkillHub | None = None


def get_skill_hub() -> SkillHub:
    """Get the global skill hub instance."""
    global _skill_hub
    if _skill_hub is None:
        _skill_hub = SkillHub()
    return _skill_hub
