"""
Media Tools — Screen recording, Audio, Image processing, and Clipboard.
"""

from __future__ import annotations

import logging
import os
import subprocess
from datetime import datetime
from typing import Optional

from src.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)

# Track recording PID
_recording_pid = None


# ==================== SCREEN & VIDEO ====================

def start_screen_recording(output_path: Optional[str] = None) -> str:
    """
    Start screen recording using build-in screencapture.
    
    Args:
        output_path: Optional path to save recording (default: Desktop).
    """
    global _recording_pid
    
    if _recording_pid:
        return "Recording already in progress."

    try:
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.expanduser(f"~/Desktop/recording_{timestamp}.mov")
        
        # Use screencapture for video
        process = subprocess.Popen(
            ['screencapture', '-v', output_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        _recording_pid = process.pid
        return f"Recording started (PID {_recording_pid}). Saving to: {output_path}"
    except Exception as e:
        return f"Error starting recording: {e}"


def stop_screen_recording() -> str:
    """Stop the current screen recording."""
    global _recording_pid
    
    if not _recording_pid:
        return "No active recording found."

    try:
        subprocess.run(['kill', str(_recording_pid)], check=True)
        pid = _recording_pid
        _recording_pid = None
        return f"Recording stopped (PID {pid})."
    except Exception as e:
        return f"Error stopping recording: {e}"


# ==================== AUDIO ====================

def record_audio(duration: int = 10, output_path: Optional[str] = None) -> str:
    """
    Record audio using sox (requires 'rec' command).
    
    Args:
        duration: Duration in seconds (default 10).
        output_path: Optional output path (default: Desktop).
    """
    try:
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.expanduser(f"~/Desktop/audio_{timestamp}.wav")
        
        # Use rec from sox
        subprocess.run(['rec', output_path, 'trim', '0', str(duration)],
                      check=True, timeout=duration + 5)
        
        return f"Audio recorded ({duration}s): {output_path}"
    except FileNotFoundError:
        return "Error: 'sox' is not installed. Please run `brew install sox`."
    except Exception as e:
        return f"Error recording audio: {e}"


# ==================== CLIPBOARD ====================

def get_clipboard_content() -> str:
    """Get the current clipboard content (text)."""
    try:
        result = subprocess.run(['pbpaste'], capture_output=True, text=True)
        return result.stdout
    except Exception as e:
        return f"Error reading clipboard: {e}"


def set_clipboard_content(content: str) -> str:
    """Set the clipboard content."""
    try:
        subprocess.run(['pbcopy'], input=content.encode(), check=True)
        return "Clipboard updated."
    except Exception as e:
        return f"Error setting clipboard: {e}"


def save_clipboard_image(output_path: Optional[str] = None) -> str:
    """
    Save image from clipboard to file.

    Args:
        output_path: Optional output path (default: Desktop).
    """
    try:
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.expanduser(f"~/Desktop/clipboard_{timestamp}.png")
        
        script = f'''
        set theFile to POSIX file "{output_path}"
        try
            set theImage to (the clipboard as «class PNGf»)
            set fileRef to open for access theFile with write permission
            write theImage to fileRef
            close access fileRef
        on error
            return "NO_IMAGE"
        end try
        '''
        
        result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
        if "NO_IMAGE" in result.stdout:
             return "No image found in clipboard."

        return f"Clipboard image saved to: {output_path}"
    except Exception as e:
        return f"Error saving clipboard image: {e}"


# ==================== REGISTRATION ====================

def register_media_tools(registry: ToolRegistry):
    """Register media tools."""
    registry.register(
        name="start_screen_recording",
        description="Start recording the screen (video)",
        parameters={
            "type": "object",
            "properties": {
                "output_path": {
                    "type": "string",
                    "description": "Optional file path to save recording (default: Desktop)",
                },
            },
        },
        func=start_screen_recording,
    )
    registry.register(
        name="stop_screen_recording",
        description="Stop the current screen recording",
        parameters={
            "type": "object",
            "properties": {},
        },
        func=stop_screen_recording,
    )
    registry.register(
        name="record_audio",
        description="Record audio from microphone",
        parameters={
            "type": "object",
            "properties": {
                "duration": {
                    "type": "integer",
                    "description": "Duration in seconds (default: 10)",
                    "default": 10,
                },
                "output_path": {
                    "type": "string",
                    "description": "Optional file path to save recording",
                },
            },
        },
        func=record_audio,
    )
    registry.register(
        name="get_clipboard",
        description="Get text content from clipboard",
        parameters={
            "type": "object",
            "properties": {},
        },
        func=get_clipboard_content,
    )
    registry.register(
        name="set_clipboard",
        description="Set text content to clipboard",
        parameters={
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "Text content to copy to clipboard",
                },
            },
            "required": ["content"],
        },
        func=set_clipboard_content,
    )
    registry.register(
        name="save_clipboard_image",
        description="Save image from clipboard to file",
        parameters={
            "type": "object",
            "properties": {
                "output_path": {
                    "type": "string",
                    "description": "Optional file path to save image (default: Desktop)",
                },
            },
        },
        func=save_clipboard_image,
    )
