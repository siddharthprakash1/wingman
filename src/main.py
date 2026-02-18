"""
Wingman - Personal AI Assistant (OpenClaw-style)

Main entry point for the application.
"""

import logging
from pathlib import Path

from rich.logging import RichHandler
import typer

# Configure logging before imports
logging.basicConfig(
    level="INFO",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)],
)

logger = logging.getLogger("wingman")

# Import the CLI app
from src.cli.commands import app

# Keep the game command for backwards compatibility
@app.command()
def game():
    """Start the Snake game (demo app)."""
    try:
        from src.apps.snake_game.main import game_loop
        game_loop()
    except ImportError:
        typer.echo("pygame not installed. Run: pip install pygame")
    except Exception as e:
        typer.echo(f"Error running game: {e}")


if __name__ == "__main__":
    app()
