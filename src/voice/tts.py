"""
Text-to-Speech (TTS) for Wingman AI.

Supports multiple providers: OpenAI TTS, Google TTS, ElevenLabs, local TTS.
"""

from __future__ import annotations

import asyncio
import logging
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.config.settings import Settings

logger = logging.getLogger(__name__)


class TTSProvider(str, Enum):
    """Available TTS providers."""
    OPENAI_TTS = "openai_tts"
    GOOGLE_TTS = "google_tts"
    ELEVENLABS = "elevenlabs"
    LOCAL_TTS = "local_tts"


class TTSVoice(str, Enum):
    """Available voices for OpenAI TTS."""
    ALLOY = "alloy"
    ECHO = "echo"
    FABLE = "fable"
    ONYX = "onyx"
    NOVA = "nova"
    SHIMMER = "shimmer"


class TextToSpeech:
    """
    Convert text to speech audio using various providers.
    
    Supports streaming and file output.
    """
    
    def __init__(
        self,
        provider: TTSProvider = TTSProvider.OPENAI_TTS,
        settings: Settings | None = None,
        voice: str = "alloy",
    ):
        """
        Initialize text-to-speech engine.
        
        Args:
            provider: TTS provider to use
            settings: Wingman settings for API keys
            voice: Voice name (provider-specific)
        """
        self.provider = provider
        self.settings = settings
        self.voice = voice
        self._client = None
    
    async def synthesize(
        self,
        text: str,
        output_path: Path | str | None = None,
    ) -> bytes:
        """
        Convert text to speech audio.
        
        Args:
            text: Text to synthesize
            output_path: Optional path to save audio file
        
        Returns:
            Audio bytes (MP3 format)
        """
        if self.provider == TTSProvider.OPENAI_TTS:
            audio_bytes = await self._synthesize_openai_tts(text)
        
        elif self.provider == TTSProvider.GOOGLE_TTS:
            audio_bytes = await self._synthesize_google_tts(text)
        
        elif self.provider == TTSProvider.ELEVENLABS:
            audio_bytes = await self._synthesize_elevenlabs(text)
        
        elif self.provider == TTSProvider.LOCAL_TTS:
            audio_bytes = await self._synthesize_local_tts(text)
        
        else:
            raise ValueError(f"Unsupported TTS provider: {self.provider}")
        
        # Save to file if requested
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(audio_bytes)
            logger.info(f"Saved audio to {output_path}")
        
        return audio_bytes
    
    async def _synthesize_openai_tts(self, text: str) -> bytes:
        """Synthesize using OpenAI TTS API."""
        try:
            from openai import AsyncOpenAI
        except ImportError:
            raise RuntimeError("OpenAI TTS requires: pip install openai")
        
        if not self.settings:
            raise ValueError("Settings required for OpenAI TTS")
        
        api_key = self.settings.providers.openai.api_key
        if not api_key:
            raise ValueError("OPENAI_API_KEY not configured")
        
        client = AsyncOpenAI(api_key=api_key)
        
        response = await client.audio.speech.create(
            model="tts-1",
            voice=self.voice,
            input=text,
        )
        
        audio_bytes = response.content
        logger.info(f"Synthesized {len(text)} chars using OpenAI TTS ({self.voice})")
        return audio_bytes
    
    async def _synthesize_google_tts(self, text: str) -> bytes:
        """Synthesize using Google Cloud Text-to-Speech."""
        try:
            from google.cloud import texttospeech
        except ImportError:
            raise RuntimeError("Google TTS requires: pip install google-cloud-texttospeech")
        
        client = texttospeech.TextToSpeechClient()
        
        synthesis_input = texttospeech.SynthesisInput(text=text)
        
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name=self.voice if self.voice != "alloy" else "en-US-Neural2-A",
        )
        
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )
        
        # Run in executor to avoid blocking
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config,
            ),
        )
        
        logger.info(f"Synthesized {len(text)} chars using Google TTS")
        return response.audio_content
    
    async def _synthesize_elevenlabs(self, text: str) -> bytes:
        """Synthesize using ElevenLabs API."""
        try:
            from elevenlabs import AsyncElevenLabs
        except ImportError:
            raise RuntimeError("ElevenLabs requires: pip install elevenlabs")
        
        if not self.settings:
            raise ValueError("Settings required for ElevenLabs")
        
        # Assume API key in environment or settings
        import os
        api_key = os.getenv("ELEVENLABS_API_KEY", "")
        if not api_key:
            raise ValueError("ELEVENLABS_API_KEY not configured")
        
        client = AsyncElevenLabs(api_key=api_key)
        
        # Generate audio
        audio_generator = await client.generate(
            text=text,
            voice=self.voice if self.voice != "alloy" else "Rachel",
            model="eleven_monolingual_v1",
        )
        
        # Collect audio bytes
        audio_bytes = b"".join([chunk async for chunk in audio_generator])
        
        logger.info(f"Synthesized {len(text)} chars using ElevenLabs")
        return audio_bytes
    
    async def _synthesize_local_tts(self, text: str) -> bytes:
        """Synthesize using local TTS (pyttsx3 or Coqui TTS)."""
        try:
            import pyttsx3
            import io
        except ImportError:
            raise RuntimeError("Local TTS requires: pip install pyttsx3")
        
        # Initialize engine (cached)
        if not self._client:
            self._client = pyttsx3.init()
            self._client.setProperty("rate", 150)  # Speaking rate
        
        # Save to temporary file (pyttsx3 doesn't support in-memory)
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            temp_path = Path(f.name)
        
        try:
            # Generate speech in executor
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self._client.save_to_file(text, str(temp_path)),
            )
            await asyncio.get_event_loop().run_in_executor(
                None,
                self._client.runAndWait,
            )
            
            # Read audio bytes
            with open(temp_path, "rb") as f:
                audio_bytes = f.read()
            
            logger.info(f"Synthesized {len(text)} chars using local TTS")
            return audio_bytes
        
        finally:
            temp_path.unlink(missing_ok=True)


# Example usage
if __name__ == "__main__":
    import sys
    
    async def main():
        if len(sys.argv) < 2:
            print("Usage: python -m src.voice.tts '<text>' [output.mp3]")
            return
        
        text = sys.argv[1]
        output = sys.argv[2] if len(sys.argv) > 2 else "output.mp3"
        
        # Use local TTS (no API key required)
        tts = TextToSpeech(provider=TTSProvider.LOCAL_TTS)
        
        print(f"Synthesizing: {text}")
        await tts.synthesize(text, output_path=output)
        print(f"Saved to {output}")
    
    asyncio.run(main())
