"""
Wake Word Detection for Wingman AI.

Uses Porcupine for local wake word detection with custom wake words.
Inspired by OpenClaw's voice activation system.
"""

from __future__ import annotations

import asyncio
import logging
import struct
from pathlib import Path
from typing import Callable

logger = logging.getLogger(__name__)

try:
    import pvporcupine
    import pyaudio
    WAKE_WORD_AVAILABLE = True
except ImportError:
    WAKE_WORD_AVAILABLE = False
    logger.warning("Wake word detection unavailable: install pvporcupine and pyaudio")


class WakeWordDetector:
    """
    Detect wake words using Porcupine wake word engine.
    
    Supports custom wake words and local processing (no cloud required).
    """
    
    def __init__(
        self,
        access_key: str,
        keywords: list[str] | None = None,
        sensitivities: list[float] | None = None,
    ):
        """
        Initialize wake word detector.
        
        Args:
            access_key: Picovoice access key (get from console.picovoice.ai)
            keywords: List of built-in keywords (e.g., ['porcupine', 'jarvis'])
                     Default: ['porcupine'] (can be changed to 'wingman' with custom model)
            sensitivities: Detection sensitivity (0.0-1.0) for each keyword
                          Higher = more sensitive but more false positives
                          Default: [0.5] for each keyword
        """
        if not WAKE_WORD_AVAILABLE:
            raise RuntimeError("Wake word detection requires: pip install pvporcupine pyaudio")
        
        self.access_key = access_key
        self.keywords = keywords or ["porcupine"]
        self.sensitivities = sensitivities or [0.5] * len(self.keywords)
        
        self.porcupine = None
        self.audio_stream = None
        self.pa = None
        self._running = False
        self._task = None
    
    def start(self, callback: Callable[[str], None]) -> None:
        """
        Start wake word detection.
        
        Args:
            callback: Function to call when wake word detected (receives keyword)
        """
        if self._running:
            logger.warning("Wake word detector already running")
            return
        
        try:
            # Initialize Porcupine
            self.porcupine = pvporcupine.create(
                access_key=self.access_key,
                keywords=self.keywords,
                sensitivities=self.sensitivities,
            )
            
            # Initialize PyAudio
            self.pa = pyaudio.PyAudio()
            self.audio_stream = self.pa.open(
                rate=self.porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=self.porcupine.frame_length,
            )
            
            self._running = True
            self._task = asyncio.create_task(self._detect_loop(callback))
            logger.info(f"Wake word detector started with keywords: {self.keywords}")
        
        except Exception as e:
            logger.error(f"Failed to start wake word detector: {e}")
            self.stop()
            raise
    
    async def _detect_loop(self, callback: Callable[[str], None]) -> None:
        """Background loop for wake word detection."""
        try:
            while self._running:
                # Read audio frame (blocking, so run in executor)
                pcm = await asyncio.get_event_loop().run_in_executor(
                    None,
                    self.audio_stream.read,
                    self.porcupine.frame_length,
                )
                
                # Convert bytes to int16 array
                pcm = struct.unpack_from("h" * self.porcupine.frame_length, pcm)
                
                # Process frame
                keyword_index = self.porcupine.process(pcm)
                
                if keyword_index >= 0:
                    detected_keyword = self.keywords[keyword_index]
                    logger.info(f"Wake word detected: {detected_keyword}")
                    
                    # Call callback in executor to avoid blocking
                    await asyncio.get_event_loop().run_in_executor(
                        None,
                        callback,
                        detected_keyword,
                    )
        
        except Exception as e:
            logger.error(f"Wake word detection error: {e}")
        
        finally:
            logger.info("Wake word detection loop stopped")
    
    def stop(self) -> None:
        """Stop wake word detection and clean up resources."""
        self._running = False
        
        if self._task:
            self._task.cancel()
            self._task = None
        
        if self.audio_stream:
            self.audio_stream.stop_stream()
            self.audio_stream.close()
            self.audio_stream = None
        
        if self.porcupine:
            self.porcupine.delete()
            self.porcupine = None
        
        if self.pa:
            self.pa.terminate()
            self.pa = None
        
        logger.info("Wake word detector stopped")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


# Example usage
if __name__ == "__main__":
    import os
    
    async def main():
        access_key = os.getenv("PICOVOICE_ACCESS_KEY")
        if not access_key:
            print("Set PICOVOICE_ACCESS_KEY environment variable")
            return
        
        def on_wake_word(keyword: str):
            print(f"🎤 Wake word detected: {keyword}")
        
        detector = WakeWordDetector(
            access_key=access_key,
            keywords=["porcupine", "jarvis"],
            sensitivities=[0.5, 0.5],
        )
        
        try:
            detector.start(on_wake_word)
            print("Listening for wake words... (Press Ctrl+C to stop)")
            await asyncio.Event().wait()  # Wait forever
        except KeyboardInterrupt:
            print("\nStopping...")
        finally:
            detector.stop()
    
    asyncio.run(main())
