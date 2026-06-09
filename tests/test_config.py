from __future__ import annotations

import os
from unittest.mock import patch

from voice_assistant.config import Settings


def test_default_settings() -> None:
    settings = Settings()
    assert settings.stt_engine == "google"
    assert settings.tts_engine == "pyttsx3"
    assert settings.language == "en-US"
    assert settings.wake_word == "assistant"
    assert settings.wake_word_enabled is False
    assert settings.energy_threshold == 300
    assert settings.phrase_time_limit == 5.0
    assert settings.mic_device_index is None
    assert settings.text_mode is False
    assert settings.weather_api_key is None


def test_custom_environment() -> None:
    with patch.dict(
        os.environ,
        {
            "STT_ENGINE": "sphinx",
            "WAKE_WORD_ENABLED": "true",
            "WAKE_WORD": "computer",
            "ENERGY_THRESHOLD": "500",
            "TEXT_MODE": "true",
            "WEATHER_API_KEY": "test_key_123",
            "MIC_DEVICE_INDEX": "1",
            "LANGUAGE": "es-ES",
        },
        clear=True,
    ):
        settings = Settings()
        assert settings.stt_engine == "sphinx"
        assert settings.wake_word_enabled is True
        assert settings.wake_word == "computer"
        assert settings.energy_threshold == 500
        assert settings.text_mode is True
        assert settings.weather_api_key == "test_key_123"
        assert settings.mic_device_index == 1
        assert settings.language == "es-ES"


def test_boolean_parsing() -> None:
    true_values = ["true", "1", "yes"]
    for val in true_values:
        with patch.dict(os.environ, {"TEXT_MODE": val}, clear=True):
            assert Settings().text_mode is True

    false_values = ["false", "0", "no", "", "something"]
    for val in false_values:
        with patch.dict(os.environ, {"TEXT_MODE": val}, clear=True):
            assert Settings().text_mode is False
