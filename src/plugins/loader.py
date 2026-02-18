"""
Plugin Loader - Discovers and loads plugins from the extensions directory.

Plugins are Python packages in the extensions/ directory that declare
their capabilities in a plugin.json or package.json file.
"""

from __future__ import annotations

import importlib
import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable

logger = logging.getLogger(__name__)


class PluginType(str, Enum):
    """Types of plugins that can be loaded."""
    CHANNEL = "channel"
    TOOL = "tool"
    PROVIDER = "provider"
    MEMORY = "memory"
    AGENT = "agent"


@dataclass
class Plugin:
    """A loaded plugin."""
    name: str
    version: str
    type: PluginType
    description: str = ""
    author: str = ""
    path: Path = field(default_factory=Path)
    config: dict[str, Any] = field(default_factory=dict)
    module: Any = None
    enabled: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "type": self.type.value,
            "description": self.description,
            "author": self.author,
            "path": str(self.path),
            "enabled": self.enabled,
        }


class PluginLoader:
    """
    Discovers and loads plugins from the extensions directory.
    
    Plugin structure:
        extensions/
        ├── my-channel-plugin/
        │   ├── plugin.json
        │   └── __init__.py
        ├── my-tool-plugin/
        │   ├── plugin.json
        │   └── __init__.py
        └── ...
    
    plugin.json format:
    {
        "name": "plugin-name",
        "version": "1.0.0",
        "type": "channel|tool|provider|memory|agent",
        "description": "Plugin description",
        "author": "Author name",
        "main": "__init__.py",
        "config": {}
    }
    """

    def __init__(self, extensions_dir: Path):
        self.extensions_dir = extensions_dir
        self.extensions_dir.mkdir(parents=True, exist_ok=True)
        self._plugins: dict[str, Plugin] = {}
        self._hooks: dict[str, list[Callable]] = {}

    def discover(self) -> list[Plugin]:
        """Discover all plugins in the extensions directory."""
        discovered = []
        
        if not self.extensions_dir.exists():
            return discovered
        
        for plugin_dir in self.extensions_dir.iterdir():
            if not plugin_dir.is_dir():
                continue
            
            # Look for plugin.json or package.json
            manifest_path = plugin_dir / "plugin.json"
            if not manifest_path.exists():
                manifest_path = plugin_dir / "package.json"
            
            if not manifest_path.exists():
                continue
            
            try:
                manifest = json.loads(manifest_path.read_text())
                
                # Check for openclaw.extensions in package.json
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
                )
                
                discovered.append(plugin)
                logger.info(f"Discovered plugin: {plugin.name} ({plugin.type.value})")
                
            except Exception as e:
                logger.warning(f"Failed to parse plugin manifest in {plugin_dir}: {e}")
        
        return discovered

    def load(self, plugin: Plugin) -> bool:
        """Load a plugin module."""
        try:
            # Add plugin directory to path temporarily
            import sys
            sys.path.insert(0, str(plugin.path.parent))
            
            try:
                # Import the plugin module
                module = importlib.import_module(plugin.path.name)
                plugin.module = module
                
                # Call setup if it exists
                if hasattr(module, "setup"):
                    module.setup(self)
                
                self._plugins[plugin.name] = plugin
                logger.info(f"Loaded plugin: {plugin.name}")
                return True
                
            finally:
                sys.path.remove(str(plugin.path.parent))
                
        except Exception as e:
            logger.error(f"Failed to load plugin {plugin.name}: {e}")
            return False

    def load_all(self) -> int:
        """Discover and load all plugins."""
        plugins = self.discover()
        loaded = 0
        
        for plugin in plugins:
            if self.load(plugin):
                loaded += 1
        
        return loaded

    def get_plugin(self, name: str) -> Plugin | None:
        """Get a loaded plugin by name."""
        return self._plugins.get(name)

    def get_plugins_by_type(self, plugin_type: PluginType) -> list[Plugin]:
        """Get all plugins of a specific type."""
        return [p for p in self._plugins.values() if p.type == plugin_type]

    def list_plugins(self) -> list[Plugin]:
        """List all loaded plugins."""
        return list(self._plugins.values())

    def unload(self, name: str) -> bool:
        """Unload a plugin."""
        plugin = self._plugins.get(name)
        if not plugin:
            return False
        
        try:
            # Call teardown if it exists
            if plugin.module and hasattr(plugin.module, "teardown"):
                plugin.module.teardown(self)
            
            del self._plugins[name]
            logger.info(f"Unloaded plugin: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unload plugin {name}: {e}")
            return False

    def reload(self, name: str) -> bool:
        """Reload a plugin."""
        plugin = self._plugins.get(name)
        if not plugin:
            return False
        
        path = plugin.path
        self.unload(name)
        
        # Re-discover from path
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
            )
            
            return self.load(new_plugin)
        
        return False

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
        # This would integrate with the ToolRegistry
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
