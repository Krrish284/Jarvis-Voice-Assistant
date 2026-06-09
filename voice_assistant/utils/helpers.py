from __future__ import annotations

import sys


def text_input(prompt: str = "", timeout: float | None = None) -> str:
    """Read a line of text input. Cross-platform compatible."""
    try:
        if sys.platform == "win32":
            import msvcrt
            import time

            if prompt:
                print(prompt, end="", flush=True)

            start = time.time()
            chars = []
            while True:
                if timeout is not None and (time.time() - start) > timeout:
                    return ""
                if msvcrt.kbhit():
                    ch = msvcrt.getwch()
                    if ch == "\r":
                        print()
                        return "".join(chars)
                    elif ch == "\b":
                        if chars:
                            chars.pop()
                            print("\b \b", end="", flush=True)
                    elif ch == "\x03":
                        raise KeyboardInterrupt
                    else:
                        chars.append(ch)
                        print(ch, end="", flush=True)
        else:
            import select

            if timeout:
                ready, _, _ = select.select([sys.stdin], [], [], timeout)
                if not ready:
                    return ""
            return input(prompt)
    except (EOFError, KeyboardInterrupt):
        raise
    except Exception:
        return input(prompt) if not timeout else ""
