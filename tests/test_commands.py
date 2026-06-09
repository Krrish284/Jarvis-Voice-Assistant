from __future__ import annotations

import voice_assistant.commands.handlers  # noqa: F401 - registers commands
from voice_assistant.commands.registry import get_command, get_all_commands, register


def test_register_and_get_command() -> None:
    @register("test_cmd", "A test command", [r"^test$", r"testing"])
    def _test_handler(text: str) -> str:
        return f"handled: {text}"

    cmd = get_command("test")
    assert cmd is not None
    assert cmd.name == "test_cmd"
    assert cmd.description == "A test command"

    cmd2 = get_command("testing this")
    assert cmd2 is not None
    assert cmd2.name == "test_cmd"

    result = cmd.handler("test")
    assert result == "handled: test"


def test_get_all_commands() -> None:
    cmds = get_all_commands()
    assert len(cmds) > 0
    names = [c.name for c in cmds]
    assert "time" in names
    assert "date" in names
    assert "joke" in names
    assert "help" in names
    assert "exit" in names


def test_time_command() -> None:
    cmd = get_command("what time is it")
    assert cmd is not None
    assert cmd.name == "time"
    result = cmd.handler("what time is it")
    assert "current time" in result.lower() or "time is" in result.lower()


def test_date_command() -> None:
    cmd = get_command("what's the date")
    assert cmd is not None
    assert cmd.name == "date"
    result = cmd.handler("what's the date")
    assert "today" in result.lower()
    assert "202" in result  # year prefix


def test_joke_command() -> None:
    cmd = get_command("tell me a joke")
    assert cmd is not None
    assert cmd.name == "joke"
    result = cmd.handler("tell me a joke")
    assert len(result) > 10


def test_help_command() -> None:
    cmd = get_command("help")
    assert cmd is not None
    assert cmd.name == "help"
    result = cmd.handler("help")
    assert "commands" in result.lower() or "help" in result.lower()


def test_exit_command() -> None:
    cmd = get_command("exit")
    assert cmd is not None
    assert cmd.name == "exit"
    result = cmd.handler("exit")
    assert result == "EXIT"


def test_no_match() -> None:
    cmd = get_command("supercalifragilisticexpialidocious")
    assert cmd is None


def test_calculate_command() -> None:
    cmd = get_command("what is 5 plus 3")
    assert cmd is not None
    assert cmd.name == "calculate"
    result = cmd.handler("what is 5 plus 3")
    assert "8" in result


def test_calculate_multiplication() -> None:
    cmd = get_command("calculate 6 times 7")
    assert cmd is not None
    result = cmd.handler("calculate 6 times 7")
    assert "42" in result


def test_timer_command() -> None:
    cmd = get_command("set a timer for 5 seconds")
    assert cmd is not None
    assert cmd.name == "timer"
    result = cmd.handler("set a timer for 5 seconds")
    assert "5" in result
    assert "second" in result.lower()


def test_open_command() -> None:
    cmd = get_command("open youtube")
    assert cmd is not None
    assert cmd.name == "open"


def test_search_command() -> None:
    cmd = get_command("search for Python")
    assert cmd is not None
    assert cmd.name == "search"


def test_wikipedia_command() -> None:
    cmd = get_command("wikipedia Python")
    assert cmd is not None
    assert cmd.name == "wikipedia"


def test_note_command() -> None:
    cmd = get_command("take a note buy milk")
    assert cmd is not None
    assert cmd.name == "note"
    result = cmd.handler("take a note buy milk")
    assert "saved" in result.lower() or "note" in result.lower()
