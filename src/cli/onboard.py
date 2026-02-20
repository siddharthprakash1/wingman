"""
Setup wizard for Wingman AI.

Interactive onboarding process to configure the assistant.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table

console = Console()


def print_welcome():
    """Print welcome banner."""
    welcome_text = """
    [bold cyan]🤖 Welcome to Wingman AI[/bold cyan]
    
    Your enterprise-grade AI assistant with OpenClaw architecture.
    
    This wizard will help you:
    • Choose an LLM provider
    • Configure API keys
    • Set up your workspace
    • Enable optional features
    """
    console.print(Panel(welcome_text, title="Setup Wizard", border_style="cyan"))


def check_environment() -> dict:
    """Check current environment and existing configuration."""
    console.print("\n[bold]Checking environment...[/bold]")
    
    env_status = {
        "python_version": sys.version,
        "workspace_exists": (Path.home() / ".wingman").exists(),
        "config_exists": (Path.home() / ".wingman" / "config.json").exists(),
        "env_file_exists": Path(".env").exists(),
    }
    
    # Check for existing API keys in environment
    env_keys = {
        "KIMI_API_KEY": os.getenv("KIMI_API_KEY"),
        "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY"),
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "TELEGRAM_BOT_TOKEN": os.getenv("TELEGRAM_BOT_TOKEN"),
        "DISCORD_BOT_TOKEN": os.getenv("DISCORD_BOT_TOKEN"),
    }
    
    # Display status
    table = Table(title="Environment Status")
    table.add_column("Item", style="cyan")
    table.add_column("Status", style="green")
    
    table.add_row("Python Version", f"{sys.version_info.major}.{sys.version_info.minor}")
    table.add_row(
        "Workspace",
        "✓ Exists" if env_status["workspace_exists"] else "✗ Not created"
    )
    table.add_row(
        "Configuration",
        "✓ Found" if env_status["config_exists"] else "✗ Not found"
    )
    table.add_row(
        ".env File",
        "✓ Exists" if env_status["env_file_exists"] else "✗ Not found"
    )
    
    console.print(table)
    
    # Check API keys
    has_keys = False
    for key, value in env_keys.items():
        if value:
            console.print(f"✓ Found {key}", style="green")
            has_keys = True
    
    if not has_keys:
        console.print("✗ No API keys found in environment", style="yellow")
    
    return env_status


def choose_provider() -> tuple[str, str]:
    """Let user choose LLM provider."""
    console.print("\n[bold]Choose your LLM provider:[/bold]\n")
    
    providers = {
        "1": ("Kimi K2.5", "kimi", "https://platform.moonshot.cn", "Free tier available ⭐"),
        "2": ("Google Gemini", "gemini", "https://aistudio.google.com/app/apikey", "Free tier available"),
        "3": ("OpenAI", "openai", "https://platform.openai.com/api-keys", "Paid only"),
        "4": ("Ollama (Local)", "ollama", "http://localhost:11434", "No API key needed"),
        "5": ("OpenRouter", "openrouter", "https://openrouter.ai", "Paid - multi-model"),
    }
    
    table = Table()
    table.add_column("#", style="cyan")
    table.add_column("Provider", style="green")
    table.add_column("Notes", style="yellow")
    
    for key, (name, _, _, notes) in providers.items():
        table.add_row(key, name, notes)
    
    console.print(table)
    
    choice = Prompt.ask(
        "\n[cyan]Select provider[/cyan]",
        choices=list(providers.keys()),
        default="1"
    )
    
    name, provider_id, url, _ = providers[choice]
    
    console.print(f"\n✓ Selected: [bold]{name}[/bold]")
    
    if provider_id != "ollama":
        console.print(f"Get your API key at: [link]{url}[/link]")
        api_key = Prompt.ask(f"\n[cyan]Enter your {name} API key[/cyan]", password=True)
        return provider_id, api_key
    else:
        console.print("\n[yellow]Ollama requires local installation:[/yellow]")
        console.print("  curl -fsSL https://ollama.com/install.sh | sh")
        console.print("  ollama serve")
        return provider_id, ""


def configure_workspace() -> Path:
    """Configure workspace directory."""
    console.print("\n[bold]Configure workspace:[/bold]\n")
    
    default_workspace = Path.home() / ".wingman" / "workspace"
    
    console.print(f"Default workspace: [cyan]{default_workspace}[/cyan]")
    console.print("\n[yellow]The workspace is where Wingman stores:[/yellow]")
    console.print("  • Session data and transcripts")
    console.print("  • Memory and vector embeddings")
    console.print("  • Logs and audit trails")
    console.print("  • Generated files (if sandboxed)")
    
    use_default = Confirm.ask(
        "\nUse default workspace?",
        default=True
    )
    
    if use_default:
        workspace = default_workspace
    else:
        custom_path = Prompt.ask("Enter custom workspace path")
        workspace = Path(custom_path).expanduser()
    
    # Create workspace
    workspace.mkdir(parents=True, exist_ok=True)
    console.print(f"✓ Workspace created at: [green]{workspace}[/green]")
    
    # Security: Enable sandboxing
    sandboxed = Confirm.ask(
        "\n[bold]Enable workspace sandboxing?[/bold]\n"
        "[yellow](Recommended for security - restricts file/shell operations)[/yellow]",
        default=True
    )
    
    return workspace


def configure_channels() -> dict:
    """Configure optional messaging channels."""
    console.print("\n[bold]Configure messaging channels:[/bold]\n")
    
    channels_config = {}
    
    # Telegram
    if Confirm.ask("Enable Telegram bot?", default=False):
        console.print("\n[cyan]Get bot token from @BotFather on Telegram[/cyan]")
        token = Prompt.ask("Telegram bot token", password=True)
        channels_config["telegram"] = {"enabled": True, "token": token}
    
    # Discord
    if Confirm.ask("\nEnable Discord bot?", default=False):
        console.print("\n[cyan]Create app at: https://discord.com/developers/applications[/cyan]")
        token = Prompt.ask("Discord bot token", password=True)
        channels_config["discord"] = {"enabled": True, "token": token}
    
    # WhatsApp
    if Confirm.ask("\nEnable WhatsApp (via Twilio)?", default=False):
        console.print("\n[cyan]Get credentials at: https://www.twilio.com[/cyan]")
        sid = Prompt.ask("Twilio Account SID")
        auth_token = Prompt.ask("Twilio Auth Token", password=True)
        whatsapp_number = Prompt.ask("Twilio WhatsApp Number (e.g., whatsapp:+14155238886)")
        channels_config["whatsapp"] = {
            "enabled": True,
            "twilio_account_sid": sid,
            "twilio_auth_token": auth_token,
            "twilio_whatsapp_number": whatsapp_number,
        }
    
    # Slack
    if Confirm.ask("\nEnable Slack bot?", default=False):
        console.print("\n[cyan]Create app at: https://api.slack.com/apps[/cyan]")
        bot_token = Prompt.ask("Slack Bot Token (xoxb-...)", password=True)
        app_token = Prompt.ask("Slack App Token (xapp-...) for Socket Mode", password=True)
        channels_config["slack"] = {
            "enabled": True,
            "bot_token": bot_token,
            "app_token": app_token,
        }
    
    return channels_config


def save_configuration(
    provider: str,
    api_key: str,
    workspace: Path,
    sandboxed: bool,
    channels: dict,
):
    """Save configuration to files."""
    console.print("\n[bold]Saving configuration...[/bold]")
    
    # Create .env file
    env_path = Path(".env")
    env_lines = []
    
    # Provider API key
    if provider == "kimi":
        env_lines.append(f"KIMI_API_KEY={api_key}")
        env_lines.append(f"DEFAULT_MODEL=kimi/kimi-k2.5")
    elif provider == "gemini":
        env_lines.append(f"GEMINI_API_KEY={api_key}")
        env_lines.append(f"GOOGLE_API_KEY={api_key}")
        env_lines.append(f"DEFAULT_MODEL=gemini/gemini-2.5-flash")
    elif provider == "openai":
        env_lines.append(f"OPENAI_API_KEY={api_key}")
        env_lines.append(f"DEFAULT_MODEL=openai/gpt-4o")
    elif provider == "ollama":
        env_lines.append(f"OLLAMA_API_BASE=http://localhost:11434")
        env_lines.append(f"DEFAULT_MODEL=ollama/llama3:latest")
    
    # Workspace
    env_lines.append(f"\nWINGMAN_WORKSPACE={workspace}")
    env_lines.append(f"WINGMAN_WORKSPACE_SANDBOXED={'true' if sandboxed else 'false'}")
    
    # Gateway
    env_lines.append(f"\nGATEWAY_HOST=127.0.0.1")
    env_lines.append(f"GATEWAY_PORT=18789")
    
    # Channels
    if "telegram" in channels:
        env_lines.append(f"\nTELEGRAM_BOT_TOKEN={channels['telegram']['token']}")
    
    if "discord" in channels:
        env_lines.append(f"\nDISCORD_BOT_TOKEN={channels['discord']['token']}")
    
    if "whatsapp" in channels:
        cfg = channels["whatsapp"]
        env_lines.append(f"\nTWILIO_ACCOUNT_SID={cfg['twilio_account_sid']}")
        env_lines.append(f"TWILIO_AUTH_TOKEN={cfg['twilio_auth_token']}")
        env_lines.append(f"TWILIO_WHATSAPP_NUMBER={cfg['twilio_whatsapp_number']}")
    
    if "slack" in channels:
        cfg = channels["slack"]
        env_lines.append(f"\nSLACK_BOT_TOKEN={cfg['bot_token']}")
        env_lines.append(f"SLACK_APP_TOKEN={cfg['app_token']}")
    
    # Write .env
    with open(env_path, "w") as f:
        f.write("\n".join(env_lines))
    
    console.print(f"✓ Created {env_path}", style="green")
    
    # Create config directory
    config_dir = Path.home() / ".wingman"
    config_dir.mkdir(parents=True, exist_ok=True)
    console.print(f"✓ Created config directory: {config_dir}", style="green")


def print_next_steps(provider: str):
    """Print next steps."""
    next_steps = f"""
    [bold green]✓ Setup complete![/bold green]
    
    [bold]Next steps:[/bold]
    
    1. Start the WebChat UI:
       [cyan]python -m src.cli.app gateway[/cyan]
       Then open: [link]http://127.0.0.1:18789[/link]
    
    2. Or chat in terminal:
       [cyan]python -m src.cli.app chat[/cyan]
    
    3. View all commands:
       [cyan]python -m src.cli.app --help[/cyan]
    
    4. Install additional features:
       [cyan]pip install -e .[voice]     # Voice capabilities[/cyan]
       [cyan]pip install -e .[browser]   # Browser automation[/cyan]
       [cyan]pip install -e .[all]       # Everything[/cyan]
    
    5. Join the community:
       Discord: [link]https://discord.gg/wingman[/link]
       GitHub: [link]https://github.com/yourusername/wingman[/link]
    
    [bold yellow]Tip:[/bold yellow] All configuration is in ~/.wingman/config.json
    """
    
    console.print(Panel(next_steps, title="Success!", border_style="green"))


def run_setup_wizard():
    """Run the interactive setup wizard."""
    try:
        print_welcome()
        
        # Check environment
        env_status = check_environment()
        
        # If already configured, ask to reconfigure
        if env_status["config_exists"] or env_status["env_file_exists"]:
            reconfigure = Confirm.ask(
                "\n[yellow]Existing configuration found. Reconfigure?[/yellow]",
                default=False
            )
            if not reconfigure:
                console.print("\n[green]Keeping existing configuration.[/green]")
                return
        
        # Choose provider
        provider, api_key = choose_provider()
        
        # Configure workspace
        workspace = configure_workspace()
        sandboxed = Confirm.ask(
            "\nEnable workspace sandboxing?",
            default=True
        )
        
        # Configure channels
        channels = configure_channels()
        
        # Save configuration
        save_configuration(provider, api_key, workspace, sandboxed, channels)
        
        # Print next steps
        print_next_steps(provider)
    
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Setup cancelled.[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Setup failed: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    run_setup_wizard()
