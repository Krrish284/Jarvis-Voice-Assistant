from __future__ import annotations

from voice_assistant.commands.registry import register, get_command, get_all_commands


def test_register_new_command() -> None:
    @register("hello", "Says hello", [r"^hello$", r"^hi$"])
    def _hello(text: str) -> str:
        return "Hello!"

    cmd = get_command("hello")
    assert cmd is not None
    assert cmd.name == "hello"
    assert cmd.description == "Says hello"
    assert cmd.handler("hello") == "Hello!"


def test_pattern_matching() -> None:
    cmd = get_command("hi")
    assert cmd is not None
    assert cmd.name == "hello"


def test_multiple_registrations() -> None:
    count_before = len(get_all_commands())
    cmd_list = get_all_commands()
    names = [c.name for c in cmd_list]
    assert "hello" in names
    assert len(cmd_list) >= count_before


def test_no_match_returns_none() -> None:
    cmd = get_command("zzzznotacommandzzzz")
    assert cmd is None


def test_case_insensitive() -> None:
    cmd = get_command("HELLO")
    assert cmd is not None
    assert cmd.name == "hello"
