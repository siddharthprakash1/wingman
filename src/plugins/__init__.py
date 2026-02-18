"""
Plugin System - Extensibility framework for OpenClaw-like architecture.

Plugins can extend:
- Channels: Add new messaging platforms
- Tools: Add custom tools
- Providers: Add new LLM providers
- Memory: Custom memory backends
- Agents: Custom specialized agents
"""

from src.plugins.loader import PluginLoader, Plugin, PluginType

__all__ = ["PluginLoader", "Plugin", "PluginType"]
