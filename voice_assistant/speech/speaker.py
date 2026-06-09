from __future__ import annotations

import logging

import pyttsx3

logger = logging.getLogger(__name__)


class Speaker:
    def __init__(self, rate: int = 180, volume: float = 0.9) -> None:
        self.engine: pyttsx3.Engine | None = None
        self.rate = rate
        self.volume = volume

    def initialize(self) -> bool:
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty("rate", self.rate)
            self.engine.setProperty("volume", self.volume)

            voices = self.engine.getProperty("voices")
            for voice in voices:
                if "female" in voice.name.lower():
                    self.engine.setProperty("voice", voice.id)
                    break

            logger.info("TTS engine initialized successfully")
            return True
        except Exception:
            logger.exception("Failed to initialize TTS engine")
            return False

    def speak(self, text: str) -> None:
        if not self.engine:
            logger.warning("TTS engine not initialized")
            return
        try:
            logger.info("Speaking: %s", text)
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception:
            logger.exception("Error during speech synthesis")

    def cleanup(self) -> None:
        if self.engine:
            try:
                self.engine.stop()
            except Exception:
                pass
