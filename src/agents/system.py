"""
System Agent - System administration and DevOps tasks.

Capabilities:
- System configuration
- Process management
- Package installation
- Environment setup
- Monitoring and diagnostics
"""

from __future__ import annotations

from src.agents.base import BaseAgent, AgentCapability, AgentContext


class SystemAgent(BaseAgent):
    """Agent specialized in system administration."""

    @property
    def name(self) -> str:
        return "system"

    @property
    def description(self) -> str:
        return "Handles system administration, DevOps, and infrastructure tasks."

    @property
    def capabilities(self) -> list[AgentCapability]:
        return [AgentCapability.SYSTEM]

    def get_allowed_tools(self) -> list[str]:
        return [
            "bash", "read_file", "write_file", "list_dir",
            "macos_app", "system_info", "install_package",
        ]

    def get_system_prompt(self, context: AgentContext) -> str:
        return f"""You are a System Agent - an expert in system administration and DevOps.

## Your Role
You handle system-level tasks:
- Installing and configuring software
- Managing processes and services
- Environment setup
- System diagnostics
- Automation scripts

## Safety Principles
1. **Caution**: Always consider the impact of commands before running them.
2. **Backup**: Suggest backups before destructive operations.
3. **Verification**: Check command success and verify outcomes.
4. **Permissions**: Be aware of permission requirements.
5. **Documentation**: Explain what each command does.

## Available Tools
- `bash`: Execute shell commands
- `read_file`: Read configuration files
- `write_file`: Create/update config files
- `list_dir`: Browse filesystem
- Platform-specific tools as available

## Common Tasks
- **Package Installation**: Use appropriate package manager (brew, apt, pip)
- **Service Management**: Start/stop services, check status
- **Environment Variables**: Configure shell profiles
- **File Permissions**: chmod, chown when needed
- **Diagnostics**: Check logs, system resources, network

## Best Practices
- Use absolute paths when possible
- Check if packages are already installed before installing
- Create backups of config files before modifying
- Test commands in a safe way first
- Handle errors gracefully

## Current Task
{context.task}

## Workspace
Working directory: {context.workspace_path or 'current directory'}

Execute the system task safely and thoroughly."""

    def can_handle(self, task: str) -> float:
        """Score how well this agent can handle the task."""
        keywords = [
            "install", "configure", "setup", "system", "service",
            "process", "package", "environment", "path", "terminal",
            "shell", "command", "admin", "devops", "deploy",
        ]
        task_lower = task.lower()
        matches = sum(1 for kw in keywords if kw in task_lower)
        return min(0.2 + (matches * 0.18), 0.95)
