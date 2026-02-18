"""
Desktop Tools — Window management (snap, move, resize).
"""

from __future__ import annotations

import logging
import subprocess
from typing import Optional

from src.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


def get_screen_dimensions(display: int = 0) -> tuple[int, int, int, int]:
    """
    Get screen dimensions for specified display.
    Returns: (x_offset, y_offset, width, height)
    """
    try:
        script = '''
        tell application "Finder"
            set desktopBounds to bounds of window of desktop
            return desktopBounds
        end tell
        '''
        result = subprocess.run(['osascript', '-e', script], 
                              capture_output=True, text=True, timeout=3)
        
        bounds = result.stdout.strip().split(', ')
        if len(bounds) >= 4:
            x1, y1, x2, y2 = map(int, bounds)
            
            if display == 0:
                return (0, 25, x2, y2 - 25)
            else:
                width = x2
                return (width * display, 25, width, y2 - 25)
        
        return (0, 25, 1920, 1055)  # Fallback
            
    except Exception:
        return (0, 25, 1920, 1055)


def snap_window(app_name: str, position: str, display: int = 0) -> str:
    """
    Snap a window to a specific position.
    
    Args:
        app_name: Application name.
        position: 'left', 'right', 'top', 'bottom', 'full'.
        display: Display index (0=main).
    """
    try:
        x_offset, y_offset, screen_width, screen_height = get_screen_dimensions(display)
        
        if position == 'left':
            x, y = x_offset, y_offset
            w, h = int(screen_width * 0.5), screen_height
        elif position == 'right':
            x, y = x_offset + int(screen_width * 0.5), y_offset
            w, h = int(screen_width * 0.5), screen_height
        elif position == 'top':
            x, y = x_offset, y_offset
            w, h = screen_width, int(screen_height * 0.5)
        elif position == 'bottom':
            x, y = x_offset, y_offset + int(screen_height * 0.5)
            w, h = screen_width, int(screen_height * 0.5)
        elif position == 'full':
            x, y = x_offset, y_offset
            w, h = screen_width, screen_height
        else:
            return f"Unknown position: {position}"
            
        script = f'''
        tell application "System Events"
            tell process "{app_name}"
                set frontmost to true
                tell window 1
                    set position to {{{x}, {y}}}
                    set size to {{{w}, {h}}}
                end tell
            end tell
        end tell
        '''
        subprocess.run(['osascript', '-e', script], check=True, timeout=3)
        return f"{app_name} snapped to {position} on display {display}"
    except Exception as e:
        return f"Error snapping window: {e}"


def list_open_windows() -> str:
    """List all open windows visible to System Events."""
    try:
        script = '''
        tell application "System Events"
            set windowList to {}
            repeat with proc in (every process whose background only is false)
                set procName to name of proc
                repeat with win in (every window of proc)
                    set end of windowList to procName & " - " & name of win
                end repeat
            end repeat
            return windowList
        end tell
        '''
        result = subprocess.run(['osascript', '-e', script], 
                              capture_output=True, text=True, check=True, timeout=5)
        windows = [w.strip() for w in result.stdout.split(',') if w.strip()]
        return f"Open windows ({len(windows)}):\n" + "\n".join(f"- {w}" for w in windows)
    except Exception as e:
        return f"Error listing windows: {e}"


def register_desktop_tools(registry: ToolRegistry):
    """Register desktop tools."""
    registry.register(
        name="snap_window",
        description="Snap an application window to a position (left, right, top, bottom, full)",
        parameters={
            "type": "object",
            "properties": {
                "app_name": {
                    "type": "string",
                    "description": "Application name to snap",
                },
                "position": {
                    "type": "string",
                    "description": "Position: 'left', 'right', 'top', 'bottom', or 'full'",
                    "enum": ["left", "right", "top", "bottom", "full"],
                },
                "display": {
                    "type": "integer",
                    "description": "Display index (0=main, default: 0)",
                    "default": 0,
                },
            },
            "required": ["app_name", "position"],
        },
        func=snap_window,
    )
    registry.register(
        name="list_open_windows",
        description="List all open windows on macOS",
        parameters={
            "type": "object",
            "properties": {},
        },
        func=list_open_windows,
    )
