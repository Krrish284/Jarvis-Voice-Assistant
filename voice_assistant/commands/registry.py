from __future__ import annotations

import re
from collections.abc import Callable
from typing import NamedTuple


class Command(NamedTuple):
    name: str
    description: str
    handler: Callable[..., str]
    patterns: list[re.Pattern[str]]

    def matches(self, text: str) -> bool:
        return any(p.search(text) for p in self.patterns)


_registry: dict[str, Command] = {}


def register(
    name: str,
    description: str,
    patterns: list[str],
) -> Callable[[Callable[..., str]], Callable[..., str]]:
    def decorator(func: Callable[..., str]) -> Callable[..., str]:
        compiled = [re.compile(p, re.IGNORECASE) for p in patterns]
        _registry[name] = Command(name, description, func, compiled)
        return func
    return decorator


def get_command(text: str) -> Command | None:
    for cmd in _registry.values():
        if cmd.matches(text):
            return cmd
    return None


def get_all_commands() -> list[Command]:
    return list(_registry.values())
