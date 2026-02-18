"""
CLI Commands - OpenClaw-style command line interface.

Commands:
- onboard: Guided setup wizard
- gateway: Start the server
- agent: Direct agent interaction
- channels: Manage channel connections
- doctor: Health diagnostics
- skills: Manage skills
- memory: Memory operations
"""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table

from src.config.settings import (
    Settings, load_settings, save_settings,
    DEFAULT_CONFIG_DIR, DEFAULT_CONFIG_PATH, DEFAULT_WORKSPACE,
)

console = Console()
app = typer.Typer(name="wingman", help="Personal AI Assistant - OpenClaw-style")

# Sub-apps for grouped commands
channels_app = typer.Typer(help="Channel management commands")
skills_app = typer.Typer(help="Skills management commands")
memory_app = typer.Typer(help="Memory management commands")

app.add_typer(channels_app, name="channels")
app.add_typer(skills_app, name="skills")
app.add_typer(memory_app, name="memory")


@app.command()
def onboard():
    """Interactive setup wizard for first-time configuration."""
    console.print(Panel.fit(
        "[bold blue]🦞 Welcome to Wingman Setup[/bold blue]\n\n"
        "Let's configure your personal AI assistant.",
        title="Setup Wizard",
    ))
    
    # Check if already configured
    if DEFAULT_CONFIG_PATH.exists():
        if not Confirm.ask("Configuration already exists. Overwrite?"):
            console.print("Setup cancelled.")
            return
    
    # Create directories
    DEFAULT_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    DEFAULT_WORKSPACE.mkdir(parents=True, exist_ok=True)
    
    # Start with default settings
    settings = Settings()
    
    # LLM Provider selection
    console.print("\n[bold]Step 1: Configure LLM Provider[/bold]")
    console.print("Choose your primary AI model provider:\n")
    console.print("  1. Gemini (Google) - Free tier available")
    console.print("  2. OpenAI (GPT-4)")
    console.print("  3. Kimi (Moonshot) - Free K2.5 model")
    console.print("  4. Ollama (Local)")
    console.print("  5. OpenRouter (Multiple models)")
    
    choice = Prompt.ask("Select provider", choices=["1", "2", "3", "4", "5"], default="1")
    
    if choice == "1":
        api_key = Prompt.ask("Enter Gemini API key (from aistudio.google.com)")
        settings.providers.gemini.api_key = api_key
        settings.agents.defaults.model = "gemini/gemini-2.5-flash"
    elif choice == "2":
        api_key = Prompt.ask("Enter OpenAI API key")
        settings.providers.openai.api_key = api_key
        settings.agents.defaults.model = "openai/gpt-4o"
    elif choice == "3":
        api_key = Prompt.ask("Enter Kimi API key (from platform.moonshot.cn)")
        settings.providers.kimi.api_key = api_key
        settings.agents.defaults.model = "kimi/kimi-k2.5"
    elif choice == "4":
        settings.agents.defaults.model = "ollama/llama3"
        console.print("Make sure Ollama is running: ollama serve")
    elif choice == "5":
        api_key = Prompt.ask("Enter OpenRouter API key")
        settings.providers.openrouter.api_key = api_key
        settings.agents.defaults.model = "openrouter/anthropic/claude-3-5-sonnet"
    
    # Save configuration
    save_settings(settings)
    console.print(f"\n✅ Configuration saved to {DEFAULT_CONFIG_PATH}")
    
    # Initialize workspace
    _init_workspace(DEFAULT_WORKSPACE)
    console.print(f"✅ Workspace initialized at {DEFAULT_WORKSPACE}")
    
    # Final instructions
    console.print(Panel.fit(
        "[bold green]Setup Complete![/bold green]\n\n"
        "Start the assistant:\n"
        "  [cyan]wingman gateway[/cyan]     Start the web server\n"
        "  [cyan]wingman agent -m 'Hi'[/cyan]  Chat directly\n\n"
        f"Web UI: http://127.0.0.1:18789",
        title="Next Steps",
    ))


@app.command()
def gateway(
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Host to bind to"),
    port: int = typer.Option(18789, "--port", "-p", help="Port to bind to"),
):
    """Start the Wingman Gateway server."""
    console.print(Panel.fit(
        f"[bold blue]🦞 Wingman Gateway[/bold blue]\n\n"
        f"Starting on {host}:{port}\n"
        f"Web UI: http://{host}:{port}",
    ))
    
    from src.gateway.server import start_gateway
    asyncio.run(start_gateway(host=host, port=port))


@app.command()
def agent(
    message: str = typer.Option(None, "--message", "-m", help="Message to send"),
    session: str = typer.Option("main", "--session", "-s", help="Session ID"),
    stream: bool = typer.Option(False, "--stream", help="Stream output"),
):
    """Send a message directly to the agent (bypass gateway)."""
    from src.core.runtime import AgentRuntime
    
    settings = load_settings()
    runtime = AgentRuntime(settings=settings)
    
    if message:
        # Single message mode
        if stream:
            async def run_stream():
                async for chunk in runtime.process_message_stream(message, channel="cli"):
                    console.print(chunk, end="")
                console.print()
            asyncio.run(run_stream())
        else:
            response = asyncio.run(runtime.process_message(message, channel="cli"))
            console.print(response)
    else:
        # Interactive mode
        console.print("[bold]Interactive mode[/bold] (type 'exit' to quit)\n")
        while True:
            try:
                user_input = Prompt.ask("[cyan]You[/cyan]")
                if user_input.lower() in ("exit", "quit", "q"):
                    break
                
                response = asyncio.run(runtime.process_message(user_input, channel="cli"))
                console.print(f"[green]Assistant[/green]: {response}\n")
            except KeyboardInterrupt:
                break
        
        console.print("\nGoodbye!")


@app.command()
def doctor():
    """Check system health and configuration."""
    console.print("[bold]🩺 System Health Check[/bold]\n")
    
    settings = load_settings()
    
    # Configuration
    table = Table(title="Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    table.add_column("Status")
    
    table.add_row("Config Path", str(DEFAULT_CONFIG_PATH), "✅" if DEFAULT_CONFIG_PATH.exists() else "❌")
    table.add_row("Workspace", str(settings.workspace_path), "✅" if settings.workspace_path.exists() else "❌")
    table.add_row("Default Model", settings.agents.defaults.model, "✅")
    
    console.print(table)
    
    # Providers
    console.print("\n[bold]Provider Status[/bold]")
    providers_table = Table()
    providers_table.add_column("Provider")
    providers_table.add_column("Configured")
    
    providers_table.add_row("Gemini", "✅" if settings.providers.gemini.api_key else "❌")
    providers_table.add_row("OpenAI", "✅" if settings.providers.openai.api_key else "❌")
    providers_table.add_row("Kimi", "✅" if settings.providers.kimi.api_key else "❌")
    providers_table.add_row("Ollama", "✅ (always available)")
    providers_table.add_row("OpenRouter", "✅" if settings.providers.openrouter.api_key else "❌")
    
    console.print(providers_table)
    
    # Workspace files
    console.print("\n[bold]Workspace Files[/bold]")
    workspace = settings.workspace_path
    files = ["IDENTITY.md", "SOUL.md", "AGENTS.md", "USER.md", "MEMORY.md", "TOOLS.md"]
    for f in files:
        path = workspace / f
        status = "✅" if path.exists() else "❌ (will be created)"
        console.print(f"  {f}: {status}")


# --- Channel Commands ---

@channels_app.command("list")
def channels_list():
    """List configured channels."""
    settings = load_settings()
    
    table = Table(title="Channels")
    table.add_column("Channel")
    table.add_column("Enabled")
    table.add_column("Status")
    
    table.add_row("Telegram", "✅" if settings.channels.telegram.enabled else "❌", 
                  "Token set" if settings.channels.telegram.token else "Not configured")
    table.add_row("Discord", "✅" if settings.channels.discord.enabled else "❌",
                  "Token set" if settings.channels.discord.token else "Not configured")
    table.add_row("WebChat", "✅" if settings.channels.webchat.enabled else "❌",
                  f"Port {settings.channels.webchat.port}")
    
    console.print(table)


@channels_app.command("login")
def channels_login(channel: str):
    """Configure/authenticate a channel."""
    settings = load_settings()
    
    if channel == "telegram":
        token = Prompt.ask("Enter Telegram bot token")
        settings.channels.telegram.token = token
        settings.channels.telegram.enabled = True
        save_settings(settings)
        console.print("✅ Telegram configured. Restart gateway to apply.")
    elif channel == "discord":
        token = Prompt.ask("Enter Discord bot token")
        settings.channels.discord.token = token
        settings.channels.discord.enabled = True
        save_settings(settings)
        console.print("✅ Discord configured. Restart gateway to apply.")
    else:
        console.print(f"Unknown channel: {channel}")


# --- Skills Commands ---

@skills_app.command("list")
def skills_list():
    """List available skills."""
    settings = load_settings()
    skills_dir = settings.workspace_path / "skills"
    
    if not skills_dir.exists():
        console.print("No skills directory found.")
        return
    
    from src.skills.manager import SkillManager
    manager = SkillManager(skills_dir)
    
    table = Table(title="Skills")
    table.add_column("Name")
    table.add_column("Description")
    table.add_column("Triggers")
    
    for skill in manager.get_all_skills():
        table.add_row(skill.name, skill.description, ", ".join(skill.triggers))
    
    console.print(table)


@skills_app.command("create")
def skills_create(name: str):
    """Create a new skill."""
    settings = load_settings()
    skills_dir = settings.workspace_path / "skills"
    
    from src.skills.manager import SkillManager
    manager = SkillManager(skills_dir)
    
    description = Prompt.ask("Skill description")
    triggers = Prompt.ask("Trigger keywords (comma-separated)")
    
    instructions = Prompt.ask("Skill instructions (or path to file)")
    if Path(instructions).exists():
        instructions = Path(instructions).read_text()
    
    skill = manager.create_skill(
        name=name,
        description=description,
        instructions=instructions,
        triggers=[t.strip() for t in triggers.split(",")],
    )
    
    console.print(f"✅ Created skill: {skill.name}")


# --- Memory Commands ---

@memory_app.command("search")
def memory_search(query: str, limit: int = 5):
    """Search memory for relevant context."""
    settings = load_settings()
    
    from src.memory.search import MemorySearch
    search = MemorySearch(settings.workspace_path)
    
    results = asyncio.run(search.search(query, limit=limit))
    
    if not results:
        console.print("No results found.")
        return
    
    for entry, score in results:
        console.print(Panel(
            entry.content[:200] + "..." if len(entry.content) > 200 else entry.content,
            title=f"[{entry.source}] Score: {score:.2f}",
        ))


@memory_app.command("rebuild")
def memory_rebuild():
    """Rebuild the memory search index."""
    settings = load_settings()
    
    from src.memory.search import MemorySearch
    search = MemorySearch(settings.workspace_path)
    
    count = asyncio.run(search.rebuild_index())
    console.print(f"✅ Rebuilt index with {count} entries")


# --- Helper Functions ---

def _init_workspace(workspace: Path):
    """Initialize workspace with default files."""
    workspace.mkdir(parents=True, exist_ok=True)
    
    # Create subdirectories
    (workspace / "sessions").mkdir(exist_ok=True)
    (workspace / "memory").mkdir(exist_ok=True)
    (workspace / "skills").mkdir(exist_ok=True)
    (workspace / "cron").mkdir(exist_ok=True)
    
    # Create default files if they don't exist
    defaults = {
        "IDENTITY.md": """# Identity

You are Wingman, a helpful personal AI assistant.

You run locally on the user's machine and can:
- Execute shell commands
- Read and write files
- Search the web
- Manage schedules and reminders
- Help with coding and research

You are private, capable, and always ready to help.
""",
        "SOUL.md": """# Personality

## Tone
- Friendly but professional
- Concise and clear
- Helpful and proactive

## Communication Style
- Use markdown for formatting
- Provide examples when helpful
- Ask clarifying questions when needed
- Explain your reasoning for complex tasks

## Principles
- Privacy first - never share user data
- Be honest about limitations
- Verify before destructive operations
- Learn and remember user preferences
""",
        "AGENTS.md": """# Agent Guidelines

## Core Rules
1. Always explain what you're doing before executing commands
2. Ask for confirmation before destructive operations
3. Save important information to MEMORY.md
4. Use appropriate tools for each task

## Tool Usage
- Use `bash` for system commands
- Use `read_file`/`write_file` for file operations
- Use `web_search` for current information
- Use `memory_append` to save user preferences

## Safety
- Never expose API keys or credentials
- Verify file paths before writing
- Be cautious with `rm` and similar commands
""",
        "USER.md": """# User Preferences

(The assistant will learn and update this file over time)

## Preferences
- (To be discovered)

## Projects
- (To be discovered)

## Notes
- (To be discovered)
""",
        "MEMORY.md": """# Long-Term Memory

This file contains important facts and preferences learned over time.

## Key Facts
- (To be discovered)

## User Preferences  
- (To be discovered)

## Important Dates
- (To be discovered)
""",
        "TOOLS.md": """# Tool Conventions

## Shell Commands
- Use absolute paths when possible
- Check command success before proceeding
- Use `--help` flags to verify syntax

## File Operations
- Always check if file exists before reading
- Create parent directories when writing
- Use edit_file for precise modifications

## Web Search
- Use specific, targeted queries
- Verify information from multiple sources
""",
    }
    
    for filename, content in defaults.items():
        path = workspace / filename
        if not path.exists():
            path.write_text(content)


if __name__ == "__main__":
    app()
