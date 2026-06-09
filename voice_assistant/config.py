from __future__ import annotations

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    stt_engine: str = field(default_factory=lambda: os.getenv("STT_ENGINE", "google"))
    tts_engine: str = field(default_factory=lambda: os.getenv("TTS_ENGINE", "pyttsx3"))
    language: str = field(default_factory=lambda: os.getenv("LANGUAGE", "en-US"))
    wake_word: str = field(default_factory=lambda: os.getenv("WAKE_WORD", "assistant"))
    wake_word_enabled: bool = field(
        default_factory=lambda: os.getenv("WAKE_WORD_ENABLED", "false").lower()
        in ("true", "1", "yes")
    )
    energy_threshold: int = field(
        default_factory=lambda: int(os.getenv("ENERGY_THRESHOLD", "300"))
    )
    phrase_time_limit: float = field(
        default_factory=lambda: float(os.getenv("PHRASE_TIME_LIMIT", "5"))
    )
    mic_device_index: int | None = field(
        default_factory=lambda: (
            int(os.getenv("MIC_DEVICE_INDEX")) if os.getenv("MIC_DEVICE_INDEX") else None
        )
    )
    text_mode: bool = field(
        default_factory=lambda: os.getenv("TEXT_MODE", "false").lower()
        in ("true", "1", "yes")
    )
    weather_api_key: str | None = field(
        default_factory=lambda: os.getenv("WEATHER_API_KEY") or None
    )
