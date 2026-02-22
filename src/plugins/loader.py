"""
Plugin Loader - Discovers and loads plugins from the extensions directory.

Plugins are Python packages in the extensions/ directory that declare
their capabilities in a plugin.json or package.json file.

Enhanced with hot-reload, lifecycle management, and dependency tracking.
"""

from __future__ import annotations

import asyncio
import hashlib
import importlib
import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable

logger = logging.getLogger(__name__)


class PluginState(str, Enum):
    """Plugin lifecycle states."""
    DISCOVERED = "discovered"
    LOADING = "loading"
    LOADED = "loaded"
    ACTIVE = "active"
    FAILED = "failed"
    UNLOADING = "unloading"


class PluginType(str, Enum):
    """Types of plugins that can be loaded."""
    CHANNEL = "channel"
    TOOL = "tool"
    PROVIDER = "provider"
    MEMORY = "memory"
    AGENT = "agent"


@dataclass
class Plugin:
    """A loaded plugin with lifecycle management."""
    name: str
    version: str
    type: PluginType
    description: str = ""
    author: str = ""
    path: Path = field(default_factory=Path)
    config: dict[str, Any] = field(default_factory=dict)
    module: Any = None
    enabled: bool = True
    state: PluginState = PluginState.DISCOVERED
    dependencies: list[str] = field(default_factory=list)
    load_time: float | None = None
    last_reload: float | None = None
    checksum: str | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "type": self.type.value,
            "description": self.description,
            "author": self.author,
            "path": str(self.path),
            "enabled": self.enabled,
            "state": self.state.value,
            "dependencies": self.dependencies,
            "load_time": self.load_time,
            "last_reload": self.last_reload,
            "error": self.error,
        }

    def calculate_checksum(self) -> str:
        """Calculate checksum of plugin files."""
        hasher = hashlib.sha256()
        for py_file in sorted(self.path.glob("**/*.py")):
            try:
                hasher.update(py_file.read_bytes())
            except Exception:
                pass
        for manifest in ["plugin.json", "package.json"]:
            manifest_path = self.path / manifest
            if manifest_path.exists():
                hasher.update(manifest_path.read_bytes())
        return hasher.hexdigest()

    def needs_reload(self) -> bool:
        """Check if plugin files have changed since last load."""
        current_checksum = self.calculate_checksum()
        return current_checksum != self.checksum


class PluginLoader:
    """
    Discovers and loads plugins from the extensions directory.

    Plugin structure:
        extensions/
        +-- my-channel-plugin/
        |   +-- plugin.json
        |   +-- __init__.py
        +-- my-tool-plugin/
            +-- plugin.json
            +-- __init__.py
    """

    def __init__(self, extensions_dir: Path):
        self.extensions_dir = extensions_dir
        self.extensions_dir.mkdir(parents=True, exist_ok=True)
        self._plugins: dict[str, Plugin] = {}
        self._hooks: dict[str, list[Callable]] = {}
        self._hot_reload_task = None
        self._hot_reload_enabled = False

    def discover(self) -> list[Plugin]:
        """Discover all plugins in the extensions directory."""
        discovered = []

        if not self.extensions_dir.exists():
            return discovered

        for plugin_dir in self.extensions_dir.iterdir():
            if not plugin_dir.is_dir():
                continue

            manifest_path = plugin_dir / "plugin.json"
            if not manifest_path.exists():
                manifest_path = plugin_dir / "package.json"

            if not manifest_path.exists():
                continue

            try:
                manifest = json.loads(manifest_path.read_text())

                if "openclaw" in manifest:
                    manifest = manifest["openclaw"]

                plugin = Plugin(
                    name=manifest.get("name", plugin_dir.name),
                    version=manifest.get("version", "0.0.0"),
                    type=PluginType(manifest.get("type", "tool")),
                    description=manifest.get("description", ""),
                    author=manifest.get("author", ""),
                    path=plugin_dir,
                    config=manifest.get("config", {}),
                    dependencies=manifest.get("dependencies", []),
                    state=PluginState.DISCOVERED,
                )

                plugin.checksum = plugin.calculate_checksum()
                discovered.append(plugin)
                logger.info(f"Discovered plugin: {plugin.name} ({plugin.type.value})")

            except Exception as e:
                logger.warning(f"Failed to read plugin manifest at {plugin_dir}: {e}")

        return discovered

    def load(self, plugin: Plugin) -> bool:
        """Load a plugin module with lifecycle management."""
        try:
            plugin.state = PluginState.LOADING
            start_time = time.time()

            # Check dependencies
            for dep in plugin.dependencies:
                if dep not in self._plugins or self._plugins[dep].state != PluginState.ACTIVE:
                    raise RuntimeError(f"Dependency not loaded: {dep}")

            import sys
            sys.path.insert(0, str(plugin.path.parent))

            try:
                module = importlib.import_module(plugin.path.name)
                plugin.module = module

                if hasattr(module, "setup"):
                    module.setup(self)

                plugin.state = PluginState.LOADED
                plugin.load_time = time.time() - start_time

                if hasattr(module, "activate"):
                    module.activate(self)

                plugin.state = PluginState.ACTIVE
                self._plugins[plugin.name] = plugin
                logger.info(f"Loaded plugin: {plugin.name} in {plugin.load_time:.2f}s")

                return True

            finally:
                if str(plugin.path.parent) in sys.path:
                    sys.path.remove(str(plugin.path.parent))

        except Exception as e:
            plugin.state = PluginState.FAILED
            plugin.error = str(e)
            logger.error(f"Failed to load plugin {plugin.name}: {e}")
            return False

    def unload(self, name: str) -> bool:
        """Unload a plugin with lifecycle management."""
        plugin = self._plugins.get(name)
        if not plugin:
            return False

        try:
            plugin.state = PluginState.UNLOADING

            if plugin.module and hasattr(plugin.module, "deactivate"):
                plugin.module.deactivate(self)

            if plugin.module and hasattr(plugin.module, "teardown"):
                plugin.module.teardown(self)

            del self._plugins[name]
            logger.info(f"Unloaded plugin: {name}")
            return True

        except Exception as e:
            logger.error(f"Failed to unload plugin {name}: {e}")
            return False

    def reload(self, name: str) -> bool:
        """Reload a plugin with hot-reload support."""
        plugin = self._plugins.get(name)
        if not plugin:
            return False

        logger.info(f"Reloading plugin: {name}")
        path = plugin.path
        self.unload(name)

        manifest_path = path / "plugin.json"
        if not manifest_path.exists():
            manifest_path = path / "package.json"

        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text())
            if "openclaw" in manifest:
                manifest = manifest["openclaw"]

            new_plugin = Plugin(
                name=manifest.get("name", path.name),
                version=manifest.get("version", "0.0.0"),
                type=PluginType(manifest.get("type", "tool")),
                description=manifest.get("description", ""),
                author=manifest.get("author", ""),
                path=path,
                config=manifest.get("config", {}),
                dependencies=manifest.get("dependencies", []),
                state=PluginState.DISCOVERED,
            )

            new_plugin.checksum = new_plugin.calculate_checksum()
            new_plugin.last_reload = time.time()
            return self.load(new_plugin)

        return False

    def enable_hot_reload(self, interval_seconds: int = 5):
        """Enable automatic hot-reload monitoring."""
        if self._hot_reload_enabled:
            logger.warning("Hot reload already enabled")
            return

        self._hot_reload_enabled = True
        self._hot_reload_task = asyncio.create_task(
            self._hot_reload_loop(interval_seconds)
        )
        logger.info(f"Hot reload enabled (interval: {interval_seconds}s)")

    def disable_hot_reload(self):
        """Disable automatic hot-reload monitoring."""
        self._hot_reload_enabled = False
        if self._hot_reload_task:
            self._hot_reload_task.cancel()
            self._hot_reload_task = None
        logger.info("Hot reload disabled")

    async def _hot_reload_loop(self, interval_seconds: int):
        """Background loop for hot-reload monitoring."""
        while self._hot_reload_enabled:
            try:
                for plugin in list(self._plugins.values()):
                    if plugin.needs_reload():
                        logger.info(f"Plugin {plugin.name} changed, reloading...")
                        self.reload(plugin.name)
                await asyncio.sleep(interval_seconds)
            except Exception as e:
                logger.error(f"Hot reload error: {e}")
                await asyncio.sleep(interval_seconds)

    # --- Hook System ---

    def register_hook(self, event: str, callback: Callable) -> None:
        """Register a callback for an event hook."""
        if event not in self._hooks:
            self._hooks[event] = []
        self._hooks[event].append(callback)

    def unregister_hook(self, event: str, callback: Callable) -> None:
        """Unregister a callback from an event hook."""
        if event in self._hooks:
            self._hooks[event].remove(callback)

    async def emit(self, event: str, *args, **kwargs) -> list[Any]:
        """Emit an event to all registered hooks."""
        results = []
        for callback in self._hooks.get(event, []):
            try:
                result = callback(*args, **kwargs)
                if hasattr(result, "__await__"):
                    result = await result
                results.append(result)
            except Exception as e:
                logger.error(f"Hook callback error for {event}: {e}")
        return results

    # --- Plugin API ---

    def register_tool(self, name: str, definition: dict, func: Callable) -> None:
        """API for plugins to register tools."""
        logger.info(f"Plugin registered tool: {name}")

    def register_channel(self, name: str, adapter_class: type) -> None:
        """API for plugins to register channel adapters."""
        logger.info(f"Plugin registered channel: {name}")

    def register_provider(self, name: str, provider_class: type) -> None:
        """API for plugins to register LLM providers."""
        logger.info(f"Plugin registered provider: {name}")

    def register_agent(self, name: str, agent_class: type) -> None:
        """API for plugins to register agents."""
        logger.info(f"Plugin registered agent: {name}")
