"""
Speech-to-Text (STT) for Wingman AI.

Supports multiple providers: OpenAI Whisper, Google Speech-to-Text, local Whisper.
"""

from __future__ import annotations

import asyncio
import io
import logging
import tempfile
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.config.settings import Settings

logger = logging.getLogger(__name__)


class STTProvider(str, Enum):
    """Available STT providers."""
    OPENAI_WHISPER = "openai_whisper"
    GOOGLE_STT = "google_stt"
    LOCAL_WHISPER = "local_whisper"


class SpeechToText:
    """
    Convert speech audio to text using various providers.
    
    Supports streaming and batch transcription.
    """
    
    def __init__(
        self,
        provider: STTProvider = STTProvider.OPENAI_WHISPER,
        settings: Settings | None = None,
    ):
        """
        Initialize speech-to-text engine.
        
        Args:
            provider: STT provider to use
            settings: Wingman settings for API keys
        """
        self.provider = provider
        self.settings = settings
        self._client = None
    
    async def transcribe_file(self, audio_path: Path | str) -> str:
        """
        Transcribe audio file to text.
        
        Args:
            audio_path: Path to audio file (wav, mp3, m4a, etc.)
        
        Returns:
            Transcribed text
        """
        audio_path = Path(audio_path)
        
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        if self.provider == STTProvider.OPENAI_WHISPER:
            return await self._transcribe_openai_whisper(audio_path)
        
        elif self.provider == STTProvider.GOOGLE_STT:
            return await self._transcribe_google_stt(audio_path)
        
        elif self.provider == STTProvider.LOCAL_WHISPER:
            return await self._transcribe_local_whisper(audio_path)
        
        else:
            raise ValueError(f"Unsupported STT provider: {self.provider}")
    
    async def transcribe_bytes(self, audio_bytes: bytes, format: str = "wav") -> str:
        """
        Transcribe audio bytes to text.
        
        Args:
            audio_bytes: Raw audio data
            format: Audio format (wav, mp3, m4a, etc.)
        
        Returns:
            Transcribed text
        """
        # Write to temporary file
        with tempfile.NamedTemporaryFile(suffix=f".{format}", delete=False) as f:
            f.write(audio_bytes)
            temp_path = Path(f.name)
        
        try:
            return await self.transcribe_file(temp_path)
        finally:
            temp_path.unlink(missing_ok=True)
    
    async def _transcribe_openai_whisper(self, audio_path: Path) -> str:
        """Transcribe using OpenAI Whisper API."""
        try:
            from openai import AsyncOpenAI
        except ImportError:
            raise RuntimeError("OpenAI Whisper requires: pip install openai")
        
        if not self.settings:
            raise ValueError("Settings required for OpenAI Whisper")
        
        api_key = self.settings.providers.openai.api_key
        if not api_key:
            raise ValueError("OPENAI_API_KEY not configured")
        
        client = AsyncOpenAI(api_key=api_key)
        
        with open(audio_path, "rb") as audio_file:
            transcript = await client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text",
            )
        
        logger.info(f"Transcribed {audio_path.name} using OpenAI Whisper")
        return transcript
    
    async def _transcribe_google_stt(self, audio_path: Path) -> str:
        """Transcribe using Google Cloud Speech-to-Text."""
        try:
            from google.cloud import speech
        except ImportError:
            raise RuntimeError("Google STT requires: pip install google-cloud-speech")
        
        client = speech.SpeechClient()
        
        with open(audio_path, "rb") as audio_file:
            content = audio_file.read()
        
        audio = speech.RecognitionAudio(content=content)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            language_code="en-US",
            enable_automatic_punctuation=True,
        )
        
        # Run in executor to avoid blocking
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: client.recognize(config=config, audio=audio),
        )
        
        # Combine all transcripts
        transcript = " ".join(
            result.alternatives[0].transcript
            for result in response.results
        )
        
        logger.info(f"Transcribed {audio_path.name} using Google STT")
        return transcript
    
    async def _transcribe_local_whisper(self, audio_path: Path) -> str:
        """Transcribe using local Whisper model."""
        try:
            import whisper
        except ImportError:
            raise RuntimeError("Local Whisper requires: pip install openai-whisper")
        
        # Load model (cached after first load)
        if not self._client:
            logger.info("Loading local Whisper model (base)...")
            self._client = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: whisper.load_model("base"),
            )
        
        # Transcribe in executor
        result = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self._client.transcribe(str(audio_path)),
        )
        
        transcript = result["text"].strip()
        logger.info(f"Transcribed {audio_path.name} using local Whisper")
        return transcript


# Example usage
if __name__ == "__main__":
    import sys
    
    async def main():
        if len(sys.argv) < 2:
            print("Usage: python -m src.voice.stt <audio_file>")
            return
        
        audio_file = sys.argv[1]
        
        # Try OpenAI Whisper first, fall back to local
        stt = SpeechToText(provider=STTProvider.LOCAL_WHISPER)
        
        print(f"Transcribing {audio_file}...")
        text = await stt.transcribe_file(audio_file)
        print(f"\nTranscription:\n{text}")
    
    asyncio.run(main())
