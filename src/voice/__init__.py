"""
Voice subsystem for Wingman AI.

Provides wake word detection, speech-to-text, and text-to-speech capabilities.
"""

from __future__ import annotations

from .wake_word import WakeWordDetector
from .stt import SpeechToText, STTProvider
from .tts import TextToSpeech, TTSProvider, TTSVoice

__all__ = [
    "WakeWordDetector",
    "SpeechToText",
    "STTProvider",
    "TextToSpeech",
    "TTSProvider",
    "TTSVoice",
]
