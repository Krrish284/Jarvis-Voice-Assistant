from __future__ import annotations

import logging

import speech_recognition as sr

logger = logging.getLogger(__name__)


class Listener:
    def __init__(
        self,
        energy_threshold: int = 300,
        phrase_time_limit: float = 5.0,
        language: str = "en-US",
        device_index: int | None = None,
    ) -> None:
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = energy_threshold
        self.recognizer.dynamic_energy_threshold = True
        self.phrase_time_limit = phrase_time_limit
        self.language = language
        self.device_index = device_index
        self.microphone: sr.Microphone | None = None

    def initialize(self) -> bool:
        try:
            self.microphone = sr.Microphone(device_index=self.device_index)
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1.0)
            logger.info("Microphone initialized successfully")
            return True
        except OSError:
            logger.error("No microphone found")
            return False
        except Exception:
            logger.exception("Failed to initialize microphone")
            return False

    def listen(self, timeout: float = 5.0) -> str | None:
        if not self.microphone:
            logger.warning("Microphone not initialized")
            return None
        try:
            with self.microphone as source:
                audio = self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=self.phrase_time_limit,
                )
            return self._recognize(audio)
        except sr.WaitTimeoutError:
            return None
        except Exception:
            logger.exception("Error during listening")
            return None

    def _recognize(self, audio: sr.AudioData) -> str | None:
        engines = [
            ("google", self._recognize_google),
            ("sphinx", self._recognize_sphinx),
        ]
        for name, method in engines:
            try:
                text = method(audio)
                if text:
                    logger.debug("Recognized via %s: %s", name, text)
                    return text
            except sr.UnknownValueError:
                continue
            except sr.RequestError as e:
                logger.warning("%s recognition error: %s", name, e)
                continue
        return None

    def _recognize_google(self, audio: sr.AudioData) -> str | None:
        return self.recognizer.recognize_google(audio, language=self.language)

    def _recognize_sphinx(self, audio: sr.AudioData) -> str | None:
        return self.recognizer.recognize_sphinx(audio, language=self.language)
