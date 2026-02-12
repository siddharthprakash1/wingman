"""
CLI Application — the main command-line interface.

Provides commands matching PicoClaw's CLI:
  - onboard       Initialize workspace
  - agent -m MSG  Send a message
  - agent -i      Interactive chat
  - gateway       Start the gateway server
  - doctor        System diagnostics
  - config        Manage configuration
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text

from src.config.settings import (
    DEFAULT_CONFIG_DIR,
    DEFAULT_CONFIG_PATH,
    Settings,
    get_settings,
    load_settings,
    save_settings,
)

app = typer.Typer(
    name="wingman",
    help="Wingman — Your Personal AI Assistant",
    add_completion=False,
)
console = Console()


# ---------------------------------------------------------------------------
# onboard
# ---------------------------------------------------------------------------

@app.command()
def onboard():
    """Initialize the workspace and configure the assistant."""
    from src.memory.manager import MemoryManager

    console.print(Panel.fit(
        "[bold cyan]🦞 OpenClaw Mine — Setup Wizard[/bold cyan]\n\n"
        "Let's set up your personal AI assistant!",
        border_style="cyan",
    ))

    # 1. Create config directory
    DEFAULT_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    console.print(f"  📁 Config directory: [green]{DEFAULT_CONFIG_DIR}[/green]")

    # 2. Create or load config
    if DEFAULT_CONFIG_PATH.exists():
        console.print(f"  📄 Config already exists: [yellow]{DEFAULT_CONFIG_PATH}[/yellow]")
        settings = load_settings()
    else:
        # Copy example config
        example_config = Path(__file__).parent.parent.parent / "config.example.json"
        if example_config.exists():
            config_data = json.loads(example_config.read_text())
        else:
            config_data = Settings().model_dump()

        # Prompt for Kimi K2.5 API key (primary provider)
        console.print("\n[bold]LLM Provider Setup[/bold]")
        console.print(
            "  Kimi K2.5 is the default model (256K context, function calling)."
        )
        console.print(
            "  Get an API key at: [link=https://platform.moonshot.cn]https://platform.moonshot.cn[/link]"
        )
        kimi_key = Prompt.ask(
            "  Enter your Kimi API key (or press Enter to skip)",
            default="",
        )
        if kimi_key:
            config_data["providers"]["kimi"]["api_key"] = kimi_key
            console.print("  ✅ Kimi K2.5 API key saved")
        else:
            console.print("  ⏩ Skipped Kimi")

        # Optionally prompt for Gemini as fallback
        console.print(
            "\n  Optional: Get a free Gemini API key at: [link=https://aistudio.google.com]https://aistudio.google.com[/link]"
        )
        gemini_key = Prompt.ask(
            "  Enter your Gemini API key (or press Enter to skip)",
            default="",
        )
        if gemini_key:
            config_data["providers"]["gemini"]["api_key"] = gemini_key
            console.print("  ✅ Gemini API key saved (fallback)")
        else:
            console.print("  ⏩ Skipped Gemini")

        if not kimi_key and not gemini_key:
            console.print("  💡 Tip: Install Ollama for free local inference: [link=https://ollama.com]ollama.com[/link]")

        settings = Settings.model_validate(config_data)
        save_settings(settings)
        console.print(f"  ✅ Created config: [green]{DEFAULT_CONFIG_PATH}[/green]")

    # 3. Create workspace
    memory = MemoryManager(settings.workspace_path)
    memory.ensure_workspace()
    console.print(f"  ✅ Workspace ready: [green]{settings.workspace_path}[/green]")

    # 4. Summary
    console.print(Panel.fit(
        "[bold green]✅ Setup Complete![/bold green]\n\n"
        "Get started:\n"
        "  [cyan]openclaw-mine agent -m \"Hello!\"[/cyan]     — Quick chat\n"
        "  [cyan]openclaw-mine agent --interactive[/cyan]  — Interactive mode\n"
        "  [cyan]openclaw-mine gateway[/cyan]              — Start gateway\n"
        "  [cyan]openclaw-mine doctor[/cyan]               — System check\n",
        border_style="green",
    ))


# ---------------------------------------------------------------------------
# agent
# ---------------------------------------------------------------------------

@app.command()
def agent(
    message: str = typer.Option("", "-m", "--message", help="Message to send"),
    interactive: bool = typer.Option(False, "-i", "--interactive", help="Interactive chat mode"),
    session: str = typer.Option("", "-s", "--session", help="Session ID to resume"),
    stream: bool = typer.Option(True, "--stream/--no-stream", help="Stream response tokens"),
):
    """Send a message to the agent or start interactive chat."""
    if not message and not interactive:
        console.print("[yellow]Specify -m \"message\" or --interactive[/yellow]")
        raise typer.Exit(1)

    # Ensure workspace exists
    settings = load_settings()
    from src.memory.manager import MemoryManager
    memory = MemoryManager(settings.workspace_path)
    memory.ensure_workspace()

    if interactive:
        asyncio.run(_interactive_chat(session_id=session or None))
    elif message:
        asyncio.run(_single_message(message, session_id=session or None, stream=stream))


async def _single_message(message: str, session_id: str | None = None, stream: bool = True):
    """Process a single message and display the response."""
    from src.agent.loop import AgentSession

    session = AgentSession(session_id=session_id)
    console.print(f"[dim]Session: {session.session_id} | Model: {session.settings.agents.defaults.model}[/dim]\n")

    if stream:
        full_response = ""
        async for chunk in session.process_message_stream(message):
            print(chunk, end="", flush=True)
            full_response += chunk
        print()  # Newline after streaming
    else:
        response = await session.process_message(message)
        console.print(Markdown(response))

    session.save_session()


async def _interactive_chat(session_id: str | None = None):
    """Run interactive chat mode."""
    from src.agent.loop import AgentSession

    session = AgentSession(session_id=session_id)

    console.print(Panel.fit(
        "[bold cyan]🦞 OpenClaw Mine — Interactive Chat[/bold cyan]\n\n"
        f"Session: {session.session_id}\n"
        f"Model: {session.settings.agents.defaults.model}\n\n"
        "Type your message. Commands:\n"
        "  [dim]/quit[/dim]    — Exit\n"
        "  [dim]/clear[/dim]   — Clear history\n"
        "  [dim]/save[/dim]    — Save session\n"
        "  [dim]/tools[/dim]   — List tools\n"
        "  [dim]/memory[/dim]  — Show memory files",
        border_style="cyan",
    ))

    while True:
        try:
            user_input = Prompt.ask("\n[bold green]You[/bold green]")
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Goodbye! 🦞[/dim]")
            break

        if not user_input.strip():
            continue

        # Handle commands
        if user_input.startswith("/"):
            cmd = user_input.strip().lower()
            if cmd in ("/quit", "/exit", "/q"):
                session.save_session()
                console.print("[dim]Session saved. Goodbye! 🦞[/dim]")
                break
            elif cmd == "/clear":
                session.clear_history()
                console.print("[dim]History cleared.[/dim]")
                continue
            elif cmd == "/save":
                session.save_session()
                console.print("[dim]Session saved.[/dim]")
                continue
            elif cmd == "/tools":
                tools = session.tool_registry.list_tools()
                console.print(f"[dim]Available tools: {', '.join(tools)}[/dim]")
                continue
            elif cmd == "/memory":
                memories = session.memory.read_all_memory()
                for name, content in memories.items():
                    console.print(f"\n[bold]{name}[/bold]")
                    console.print(f"[dim]{content[:300]}...[/dim]" if len(content) > 300 else f"[dim]{content}[/dim]")
                continue
            else:
                console.print(f"[yellow]Unknown command: {cmd}[/yellow]")
                continue

        # Process the message
        console.print("\n[bold cyan]Assistant[/bold cyan]")
        try:
            response = await session.process_message(user_input)
            console.print(Markdown(response))
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


# ---------------------------------------------------------------------------
# gateway
# ---------------------------------------------------------------------------

@app.command()
def gateway(
    port: int = typer.Option(0, "--port", "-p", help="Port (default: from config)"),
    host: str = typer.Option("", "--host", help="Host (default: from config)"),
    verbose: bool = typer.Option(False, "-v", "--verbose", help="Verbose logging"),
):
    """Start the gateway server (control plane)."""
    import logging
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    settings = load_settings()
    actual_port = port or settings.gateway.port
    actual_host = host or settings.gateway.host

    text = Text(style="bold magenta")
    text.append("🦞 Wingman — Gateway\n\n")
    text.append(f"Starting on [green]{actual_host}:{actual_port}[/green]\n")
    text.append(f"WebChat UI: [link=http://localhost:{actual_port}]http://localhost:{actual_port}[/link]")
    console.print(Panel.fit(
        text,
        border_style="cyan",
    ))

    from src.gateway.server import start_gateway
    asyncio.run(start_gateway(host=actual_host, port=actual_port))


# ---------------------------------------------------------------------------
# doctor
# ---------------------------------------------------------------------------

@app.command()
def doctor():
    """Run system diagnostics and check configuration."""
    asyncio.run(_run_doctor())


async def _run_doctor():
    """Run diagnostics asynchronously."""
    console.print(Panel.fit(
        "[bold cyan]🦞 OpenClaw Mine — Doctor[/bold cyan]\n\n"
        "Running diagnostics...",
        border_style="cyan",
    ))

    settings = load_settings()

    # Check config
    if DEFAULT_CONFIG_PATH.exists():
        console.print("  ✅ Config file exists")
    else:
        console.print("  ❌ Config file missing — run: openclaw-mine onboard")
        return

    # Check workspace
    if settings.workspace_path.exists():
        console.print(f"  ✅ Workspace: {settings.workspace_path}")
    else:
        console.print(f"  ❌ Workspace missing: {settings.workspace_path}")

    # Check providers
    from src.providers.manager import ProviderManager
    pm = ProviderManager(settings)
    report = await pm.health_report()

    console.print("\n  [bold]LLM Providers:[/bold]")
    for name, info in report.items():
        status = info["status"]
        if status == "healthy":
            console.print(f"    ✅ {name}: {info['info']['model']}")
        elif status == "unhealthy":
            console.print(f"    ⚠️  {name}: unhealthy ({info['info']['model']})")
        else:
            console.print(f"    ❌ {name}: {info.get('error', 'unknown error')}")

    # Check tools
    from src.tools.registry import create_default_registry
    registry = create_default_registry()
    tools = registry.list_tools()
    console.print(f"\n  [bold]Tools:[/bold] {len(tools)} registered")
    for t in tools:
        console.print(f"    🔧 {t}")

    # Check channels
    console.print(f"\n  [bold]Channels:[/bold]")
    if settings.channels.webchat.enabled:
        console.print(f"    🌐 WebChat: port {settings.channels.webchat.port}")
    if settings.channels.telegram.enabled:
        console.print(f"    📱 Telegram: configured")
    if settings.channels.discord.enabled:
        console.print(f"    💬 Discord: configured")

    console.print("\n  [bold green]Done![/bold green]")


# ---------------------------------------------------------------------------
# config
# ---------------------------------------------------------------------------

@app.command()
def config(
    show: bool = typer.Option(False, "--show", help="Show current configuration"),
):
    """View or modify configuration."""
    settings = load_settings()

    if show or True:  # Default to showing config
        config_data = settings.model_dump()
        # Mask sensitive values
        if config_data.get("providers", {}).get("gemini", {}).get("api_key"):
            key = config_data["providers"]["gemini"]["api_key"]
            if len(key) > 8:
                config_data["providers"]["gemini"]["api_key"] = key[:4] + "..." + key[-4:]
        if config_data.get("providers", {}).get("openrouter", {}).get("api_key"):
            key = config_data["providers"]["openrouter"]["api_key"]
            if len(key) > 8:
                config_data["providers"]["openrouter"]["api_key"] = key[:4] + "..." + key[-4:]

        console.print_json(json.dumps(config_data, indent=2))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()
