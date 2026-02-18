"""
System Package Tools — Homebrew, Pip, Npm.
"""

from __future__ import annotations

import logging
import subprocess
from typing import Optional

from src.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


def brew_install(package: str) -> str:
    """Install a package via Homebrew."""
    try:
        result = subprocess.run(['brew', 'install', package],
                              capture_output=True, text=True, check=True, timeout=300)
        return f"Brew installed {package}:\n{result.stdout[:500]}"
    except subprocess.CalledProcessError as e:
        return f"Error installing {package}: {e.stderr[:500]}"
    except Exception as e:
        return f"Error: {e}"


def pip_install(package: str) -> str:
    """Install a Python package via pip."""
    try:
        result = subprocess.run(['pip', 'install', package],
                              capture_output=True, text=True, check=True, timeout=180)
        return f"Pip installed {package}:\n{result.stdout[:500]}"
    except subprocess.CalledProcessError as e:
        return f"Error installing {package}: {e.stderr[:500]}"
    except Exception as e:
        return f"Error: {e}"


def npm_install(package: str, global_install: bool = False) -> str:
    """Install an npm package."""
    try:
        cmd = ['npm', 'install']
        if global_install:
            cmd.append('-g')
        cmd.append(package)
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=180)
        return f"Npm installed {package}:\n{result.stdout[:500]}"
    except subprocess.CalledProcessError as e:
        return f"Error installing {package}: {e.stderr[:500]}"
    except Exception as e:
        return f"Error: {e}"


def register_package_tools(registry: ToolRegistry):
    """Register package manager tools."""
    registry.register(
        name="brew_install",
        description="Install a package using Homebrew",
        parameters={
            "type": "object",
            "properties": {
                "package": {
                    "type": "string",
                    "description": "Package name to install",
                },
            },
            "required": ["package"],
        },
        func=brew_install,
    )
    registry.register(
        name="pip_install",
        description="Install a Python package using pip",
        parameters={
            "type": "object",
            "properties": {
                "package": {
                    "type": "string",
                    "description": "Package name to install",
                },
            },
            "required": ["package"],
        },
        func=pip_install,
    )
    registry.register(
        name="npm_install",
        description="Install a Node.js package using npm",
        parameters={
            "type": "object",
            "properties": {
                "package": {
                    "type": "string",
                    "description": "Package name to install",
                },
                "global_install": {
                    "type": "boolean",
                    "description": "Install globally with -g flag (default: False)",
                    "default": False,
                },
            },
            "required": ["package"],
        },
        func=npm_install,
    )
