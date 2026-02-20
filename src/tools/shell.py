"""
Shell tool — execute commands on the local machine.

Enforces workspace sandboxing and command validation for security.
"""

from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path



# Dangerous command patterns that require extra scrutiny
DANGEROUS_PATTERNS = [
    'rm -rf /', 'rm -rf /*', 'mkfs', 'dd if=', ':(){:|:&};:',  # Destructive
    '>/dev/sda', '>/dev/hda',  # Disk operations
    'curl | sh', 'wget | sh', 'curl | bash', 'wget | bash',  # Blind execution
    'chmod 777', 'chmod -R 777',  # Unsafe permissions
    'chmod 666', 'chown -R', 'chgrp -R',  # Permission changes
    'kill -9 1', 'pkill -9', 'killall -9',  # System process kills
    '>/etc/', '>/var/', '>/boot/', '>/sys/',  # System file writes
    'nc -l', 'ncat -l',  # Network listeners
]

# High-risk commands that should be carefully validated
HIGH_RISK_COMMANDS = [
    'rm', 'rmdir', 'del', 'format', 'fdisk', 'mkfs',
    'dd', 'shred', 'chmod', 'chown', 'sudo', 'su',
    'curl', 'wget', 'nc', 'ncat', 'telnet',
    'python', 'python3', 'perl', 'ruby', 'node',  # Interpreters can be misused
]
def _validate_command(command: str, session_id: str | None = None) -> tuple[bool, str]:
    """Validate shell command for security issues.
    
    Returns:
        (is_safe, error_message)
    """
    audit = get_audit()
    settings = get_settings()
    
    # Check blocked commands from config
    blocked_commands = settings.tools.shell.blocked_commands
    command_lower = command.lower()
    
    for blocked in blocked_commands:
        if blocked in command_lower:
            audit.log_blocked_command(command, f"Matches blocked pattern: {blocked}", session_id)
            return False, f"Blocked command pattern: {blocked}"
    
    # Check for dangerous patterns
    for pattern in DANGEROUS_PATTERNS:
        if pattern in command_lower:
            audit.log_blocked_command(command, f"Dangerous pattern: {pattern}", session_id)
            return False, f"Dangerous command pattern detected: {pattern}"
    
    # Check for command injection attempts
    if any(char in command for char in [';', '&&', '||', '|', '`', '$(']):
        # These are valid in many cases, but log them
        logger.warning(f"Command contains shell operators: {command[:100]}")
    
    # Warn about high-risk commands (don't block, but log)
    first_word = command.split()[0] if command.split() else ''
    if first_word in HIGH_RISK_COMMANDS:
        logger.warning(f"High-risk command executed: {first_word}")
    
    return True, ""
    Returns:
        (is_safe, error_message)
    """
    # Check for dangerous patterns
    command_lower = command.lower()
    for pattern in DANGEROUS_PATTERNS:
        if pattern in command_lower:
            return False, f"Dangerous command pattern detected: {pattern}"
    
    # Check for command injection attempts
    if any(char in command for char in [';', '&&', '||', '|', '`', '$(']):
        # These are valid in many cases, but log them
        logger.warning(f"Command contains shell operators: {command[:100]}")
    
    # Warn about high-risk commands (don't block, but log)
    first_word = command.split()[0] if command.split() else ''
    if first_word in HIGH_RISK_COMMANDS:
        logger.warning(f"High-risk command executed: {first_word}")
    
    return True, ""

async def bash_execute(command: str, timeout: int = 60, working_directory: str = "") -> str:
    """
    Execute a shell command and return stdout+stderr.

    Args:
        command: The shell command to execute.
        timeout: Maximum execution time in seconds (default: 60).
        working_directory: Optional working directory for the command.

    Returns:
        Combined stdout and stderr output.
    """
    # Validate command for security issues
    is_safe, error_msg = _validate_command(command)
    if not is_safe:
        return f"❌ Command blocked: {error_msg}"
    
    # Determine working directory
    if working_directory:
        cwd = Path(working_directory).expanduser().resolve()
    elif _is_workspace_restricted():
        cwd = _get_workspace_root()
    else:
        cwd = Path(os.getcwd())
    
    # Ensure cwd exists
    cwd.mkdir(parents=True, exist_ok=True)
    
    # If workspace-restricted, verify cwd is within workspace
    if _is_workspace_restricted():
        workspace_root = _get_workspace_root()
        try:
            cwd.relative_to(workspace_root)
        except ValueError:
            return f"❌ Working directory must be within workspace: {workspace_root}"

    try:
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(cwd),
            env={**os.environ, "PAGER": "cat"},
        )

        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=timeout,
        )

        output_parts = []
        if stdout:
            output_parts.append(stdout.decode("utf-8", errors="replace"))
        if stderr:
            output_parts.append(f"[stderr]\n{stderr.decode('utf-8', errors='replace')}")
        if process.returncode != 0:
            output_parts.append(f"\n[exit code: {process.returncode}]")

        result = "\n".join(output_parts).strip()
        return result if result else "(no output)"

    except asyncio.TimeoutError:
        try:
            process.kill()
        except Exception:
            pass
        return f"❌ Command timed out after {timeout}s: {command}"
    except Exception as e:
        return f"❌ Command failed: {e}"


def register_shell_tools(registry: ToolRegistry) -> None:
    """Register shell tools with the registry."""
    registry.register(
        name="bash",
        description=(
            "Execute a shell command on the local machine. "
            "Returns stdout and stderr. Use for running scripts, "
            "installing packages, checking system info, etc."
        ),
        parameters={
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The shell command to execute",
                },
                "timeout": {
                    "type": "integer",
                    "description": "Max execution time in seconds (default: 60)",
                    "default": 60,
                },
                "working_directory": {
                    "type": "string",
                    "description": "Working directory for the command (optional)",
                    "default": "",
                },
            },
            "required": ["command"],
        },
        func=bash_execute,
    )
