from __future__ import annotations

import logging
import subprocess
import sys

from voice_assistant.commands.handlers import handle_confirmation
from voice_assistant.commands.registry import get_command
from voice_assistant.commands import handlers as cmd_handlers
from voice_assistant.config import Settings
from voice_assistant.speech.listener import Listener
from voice_assistant.speech.speaker import Speaker
from voice_assistant.utils.helpers import text_input

logger = logging.getLogger(__name__)

_SHUTDOWN_COMMANDS = ("shutdown", "restart")

_PENDING_CONFIRMATION: dict[str, str] = {}


class AssistantEngine:
    def __init__(self, config: Settings) -> None:
        self.config = config
        self.listener: Listener | None = None
        self.speaker: Speaker | None = None
        self.running = True

        cmd_handlers.init_handlers(weather_api_key=config.weather_api_key)

        if not config.text_mode:
            self._init_audio()

    def _init_audio(self) -> None:
        self.listener = Listener(
            energy_threshold=self.config.energy_threshold,
            phrase_time_limit=self.config.phrase_time_limit,
            language=self.config.language,
            device_index=self.config.mic_device_index,
        )
        self.speaker = Speaker()

        if not self.listener.initialize():
            logger.warning("Microphone initialization failed, falling back to text mode")
            self.listener = None

        if not self.speaker.initialize():
            logger.warning("TTS initialization failed, falling back to text mode")
            self.speaker = None

    def _speak(self, text: str) -> None:
        if self.speaker:
            self.speaker.speak(text)
        else:
            print(f"[Assistant] {text}")

    def _listen(self) -> str | None:
        if self.listener:
            return self.listener.listen(timeout=1.0)
        return None

    def _process_text(self, text: str) -> str | None:
        text = text.strip()
        if not text:
            return None

        logger.info("Processing: %s", text)

        if _PENDING_CONFIRMATION:
            result = handle_confirmation(text)
            if result == "Cancelled.":
                _PENDING_CONFIRMATION.clear()
                return result

            if result is None:
                action = _PENDING_CONFIRMATION.pop("action", "")
                return self._execute_system_action(action)

            _PENDING_CONFIRMATION.clear()
            return result

        command = get_command(text)
        if command:
            try:
                response = command.handler(text)
                if response == "EXIT":
                    self.running = False
                    return "Goodbye!"
                if command.name in _SHUTDOWN_COMMANDS:
                    _PENDING_CONFIRMATION["action"] = command.name
                return response
            except Exception:
                logger.exception("Error executing command '%s'", command.name)
                return "Sorry, something went wrong while processing that command."

        return (
            "I didn't understand that. "
            "Say 'help' to see what I can do, or try rephrasing your request."
        )

    def _execute_system_action(self, action: str) -> str:
        system = sys.platform
        try:
            if action == "shutdown":
                if system == "win32":
                    subprocess.run(["shutdown", "/s", "/t", "5"], check=True)
                elif system == "darwin":
                    subprocess.run(["sudo", "shutdown", "-h", "+1"], check=True)
                else:
                    subprocess.run(["sudo", "shutdown", "+1"], check=True)
                return "Shutting down the computer in 5 seconds."
            elif action == "restart":
                if system == "win32":
                    subprocess.run(["shutdown", "/r", "/t", "5"], check=True)
                elif system == "darwin":
                    subprocess.run(["sudo", "shutdown", "-r", "+1"], check=True)
                else:
                    subprocess.run(["sudo", "reboot"], check=True)
                return "Restarting the computer in 5 seconds."
        except subprocess.CalledProcessError as e:
            logger.error("System action '%s' failed: %s", action, e)
            return f"Sorry, I couldn't {action} the computer."
        except FileNotFoundError as e:
            logger.error("System action '%s' command not found: %s", action, e)
            return f"Sorry, the {action} command is not available on this system."
        return f"Unknown action: {action}"

    def run(self) -> None:
        greetings = [
            "Hello, I am your voice assistant. How can I help you?",
            "Hi there! I'm ready to assist you. What can I do?",
            "Greetings! I'm your voice assistant. Say help to see my capabilities.",
        ]
        import random
        self._speak(random.choice(greetings))

        while self.running:
            try:
                text: str | None = None

                if self.config.wake_word_enabled and self.listener:
                    self._speak("Listening for wake word...")
                    text = self._listen()
                    if text and self.config.wake_word.lower() in text.lower():
                        self._speak("Yes?")
                        text = self._listen()
                    else:
                        continue
                else:
                    if self.listener:
                        print("\n(Press Enter to speak, or type 'exit' to quit)")
                        user_input = text_input()
                        if not user_input:
                            text = self._listen()
                        else:
                            text = user_input if user_input.strip() else None
                    else:
                        try:
                            user_input = input("You: ").strip()
                        except (EOFError, KeyboardInterrupt):
                            break
                        text = user_input if user_input else None

                if text:
                    response = self._process_text(text)
                    if response:
                        self._speak(response)

            except KeyboardInterrupt:
                break
            except Exception:
                logger.exception("Unexpected error in main loop")
                self._speak("Sorry, I encountered an error. Please try again.")

        self._speak("Goodbye!")

    def cleanup(self) -> None:
        if self.speaker:
            self.speaker.cleanup()
