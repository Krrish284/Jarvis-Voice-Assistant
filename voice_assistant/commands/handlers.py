from __future__ import annotations

import datetime
import logging
import math
import re
import subprocess
import threading
import webbrowser
from urllib.parse import quote

import pyjokes
import requests
import wikipedia

from voice_assistant.commands.registry import register, get_all_commands

logger = logging.getLogger(__name__)

_weather_api_key: str | None = None

# --- Init ----------------------------------------------------------------

def init_handlers(weather_api_key: str | None = None) -> None:
    global _weather_api_key
    _weather_api_key = weather_api_key

# --- Helpers -------------------------------------------------------------

def _extract_query(text: str, prefixes: list[str]) -> str | None:
    for p in prefixes:
        match = re.search(p + r"\s+(.+?)$", text, re.IGNORECASE)
        if match:
            return match.group(1).strip().rstrip("?.!")
    return None

def _speak_async(text: str, callback: threading.Event | None = None) -> None:
    print(f"[Assistant] {text}")
    if callback:
        callback.set()

# --- Time & Date ---------------------------------------------------------

@register(
    name="time",
    description="Get the current time",
    patterns=[
        r"(what|what's|tell me)\s+(is\s+)?the\s+time",
        r"current\s+time",
        r"what\s+time\s+is\s+it",
        r"^time$",
    ],
)
def handle_time(text: str) -> str:
    now = datetime.datetime.now()
    return f"The current time is {now.strftime('%I:%M %p')}."


@register(
    name="date",
    description="Get today's date",
    patterns=[
        r"(what|what's|tell me)\s+(is\s+)?the\s+date",
        r"what\s+(day|date)\s+is\s+it",
        r"today(\'s|\s+is)?\s+(date|day)",
        r"current\s+date",
        r"^date$",
    ],
)
def handle_date(text: str) -> str:
    now = datetime.datetime.now()
    return f"Today is {now.strftime('%A, %B %d, %Y')}."


@register(
    name="day",
    description="Get the current day of the week",
    patterns=[
        r"what\s+day\s+is\s+it",
        r"what\s+day\s+of\s+the\s+week",
        r"^day$",
    ],
)
def handle_day(text: str) -> str:
    now = datetime.datetime.now()
    return f"Today is {now.strftime('%A')}."

# --- Weather -------------------------------------------------------------

@register(
    name="weather",
    description="Get weather for a city (requires WEATHER_API_KEY)",
    patterns=[
        r"(what(\'s| is)\s+)?the\s+weather(\s+(in|at|for)\s+\w+)?",
        r"(how(\'s| is)\s+)?the\s+weather(\s+(in|at|for)\s+\w+)?",
        r"weather\s+(in|at|for)\s+\w+",
        r"temperature(\s+(in|at|for)\s+\w+)?",
        r"^weather$",
    ],
)
def handle_weather(text: str) -> str:
    if not _weather_api_key:
        return (
            "Weather is not configured. "
            "Set your OpenWeatherMap API key in the WEATHER_API_KEY environment variable."
        )

    city = _extract_query(text, [r"(?:in|at|for)"])
    if not city:
        return "Which city would you like the weather for?"

    try:
        url = (
            f"https://api.openweathermap.org/data/2.5/weather"
            f"?q={quote(city)}&appid={_weather_api_key}&units=metric"
        )
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        temp = data["main"]["temp"]
        feels_like = data["main"]["feels_like"]
        description = data["weather"][0]["description"]
        humidity = data["main"]["humidity"]
        wind = data["wind"]["speed"]

        return (
            f"The weather in {city.title()} is {description} "
            f"with a temperature of {temp:.0f} degrees Celsius "
            f"(feels like {feels_like:.0f}). "
            f"Humidity is {humidity}% and wind speed is {wind:.1f} meters per second."
        )
    except requests.HTTPError as e:
        if resp.status_code == 404:
            return f"Sorry, I couldn't find a city named {city}."
        logger.error("Weather API HTTP error: %s", e)
        return f"Sorry, I couldn't get the weather for {city}."
    except requests.RequestException as e:
        logger.error("Weather API request error: %s", e)
        return f"Sorry, I couldn't get the weather for {city}."

# --- Web Search ----------------------------------------------------------

@register(
    name="search",
    description="Search the web using DuckDuckGo",
    patterns=[
        r"search\s+(for\s+)?(.+)",
        r"(search|look|find|google)\s+(up\s+)?(.+)",
        r"search\s+the\s+web\s+(for\s+)?(.+)",
    ],
)
def handle_search(text: str) -> str:
    query = _extract_query(text, [
        r"search\s+(?:for\s+)?",
        r"(?:search|look|find|google)\s+(?:up\s+)?",
        r"search\s+the\s+web\s+(?:for\s+)?",
    ])
    if not query:
        return "What would you like me to search for?"

    try:
        url = (
            f"https://api.duckduckgo.com/"
            f"?q={quote(query)}&format=json&no_html=1&skip_disambig=1"
        )
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        abstract = data.get("Abstract", "")
        answer = data.get("Answer", "")
        result = answer or abstract

        if result:
            return f"Here is what I found: {result[:500]}"
        else:
            webbrowser.open(f"https://duckduckgo.com/?q={quote(query)}")
            return f"I opened a web search for {query} in your browser."
    except requests.RequestException as e:
        logger.error("Search API error: %s", e)
        webbrowser.open(f"https://duckduckgo.com/?q={quote(query)}")
        return f"I opened a web search for {query} in your browser."

# --- Wikipedia -----------------------------------------------------------

@register(
    name="wikipedia",
    description="Look up a topic on Wikipedia",
    patterns=[
        r"wikipedia\s+(.+?)$",
        r"(look up|search|find|what(\'s| is))\s+(.+?)\s+on\s+wikipedia",
        r"tell\s+me\s+about\s+(.+?)\s+(from\s+)?wikipedia",
        r"wiki\s+(.+?)$",
    ],
)
def handle_wikipedia(text: str) -> str:
    query = _extract_query(text, [
        r"wikipedia\s+",
        r"(?:look up|search|find|what(?:\'s| is))\s+",
        r"tell\s+me\s+about\s+",
        r"wiki\s+",
    ])
    if not query:
        return "What would you like me to look up on Wikipedia?"

    try:
        summary = wikipedia.summary(query, sentences=3)
        return summary[:600]
    except wikipedia.exceptions.DisambiguationError as e:
        return f"There are multiple results for {query}. Please be more specific."
    except wikipedia.exceptions.PageError:
        return f"Sorry, I could not find a Wikipedia page for {query}."
    except requests.RequestException as e:
        logger.error("Wikipedia API error: %s", e)
        return f"Sorry, I couldn't reach Wikipedia for {query}."

# --- Calculator ----------------------------------------------------------

@register(
    name="calculate",
    description="Evaluate a mathematical expression",
    patterns=[
        r"(what(\'s| is)\s+)(.+)",
        r"calculate\s+(.+)",
        r"compute\s+(.+)",
        r"what\s+is\s+the\s+(sum|product|result|value)\s+of\s+(.+)",
    ],
)
def handle_calculate(text: str) -> str:
    expression = text.lower()

    for prefix in [
        r"^what(\'s| is)\s+the\s+(?:sum|product|result|value)\s+of\s+",
        r"^what(\'s| is)\s+",
        r"^calculate\s+",
        r"^compute\s+",
    ]:
        expression = re.sub(prefix, "", expression, count=1)

    expression = expression.strip().rstrip("?.!")

    replacements = {
        r"\bplus\b": "+",
        r"\bminus\b": "-",
        r"\b(times|x)\b": "*",
        r"\bmultiplied\s+by\b": "*",
        r"\bdivided\s+by\b": "/",
        r"\bover\b": "/",
        r"\bpower\s+of\b": "**",
        r"\braised\s+to\b": "**",
        r"\bmod\b": "%",
        r"\bpi\b": str(math.pi),
    }
    for pattern, replacement in replacements.items():
        expression = re.sub(pattern, replacement, expression, flags=re.IGNORECASE)

    expression = re.sub(r"[^0-9+\-*/.()% \d]", "", expression)
    expression = expression.strip()

    if not expression:
        return "What would you like me to calculate?"

    allowed_globals = {
        "__builtins__": {},
        "abs": abs,
        "round": round,
        "min": min,
        "max": max,
        "pow": pow,
    }
    allowed_globals.update(
        {k: v for k, v in math.__dict__.items() if not k.startswith("_")}
    )

    try:
        result = eval(expression, allowed_globals)
        if isinstance(result, float):
            result = round(result, 4)
        return f"The result is {result}."
    except ZeroDivisionError:
        return "Cannot divide by zero."
    except Exception:
        return "Sorry, I couldn't calculate that expression."

# --- Jokes ---------------------------------------------------------------

@register(
    name="joke",
    description="Tell a random joke",
    patterns=[
        r"(tell|say|give)\s+(me\s+)?(a\s+)?joke",
        r"make\s+me\s+laugh",
        r"tell\s+(me\s+)?something\s+funny",
        r"^joke$",
    ],
)
def handle_joke(text: str) -> str:
    try:
        return pyjokes.get_joke()
    except Exception:
        return (
            "Why did the programmer quit his job? "
            "Because he didn't get arrays!"
        )

# --- Open Website/App ----------------------------------------------------

@register(
    name="open",
    description="Open a website or application",
    patterns=[
        r"(open|launch|start)\s+(.+)",
        r"go\s+to\s+(.+)",
        r"navigate\s+to\s+(.+)",
    ],
)
def handle_open(text: str) -> str:
    target = _extract_query(text, [
        r"(?:open|launch|start)\s+",
        r"go\s+to\s+",
        r"navigate\s+to\s+",
    ])
    if not target:
        return "What would you like me to open?"

    target = target.strip().lower()

    website_map = {
        "youtube": "https://youtube.com",
        "google": "https://google.com",
        "github": "https://github.com",
        "gmail": "https://mail.google.com",
        "stack overflow": "https://stackoverflow.com",
        "reddit": "https://reddit.com",
        "twitter": "https://twitter.com",
        "x": "https://x.com",
        "linkedin": "https://linkedin.com",
        "facebook": "https://facebook.com",
        "amazon": "https://amazon.com",
    }

    url = website_map.get(target)
    if not url:
        if "." in target or "/" in target:
            if not target.startswith(("http://", "https://")):
                url = "https://" + target
            else:
                url = target
        else:
            url = f"https://duckduckgo.com/?q={quote(target)}"

    try:
        webbrowser.open(url)
        return f"Opening {target}."
    except Exception:
        return f"Sorry, I couldn't open {target}."

# --- Timer ---------------------------------------------------------------

_timers: list[threading.Timer] = []


@register(
    name="timer",
    description="Set a timer for a given duration",
    patterns=[
        r"(set|start)\s+(a\s+)?timer\s+(for\s+)?(\d+\s*(second|minute|hour)s?)",
        r"timer\s+(\d+\s*(second|minute|hour)s?)",
        r"(\d+)\s*(second|minute|hour)s?\s+(timer|from now)",
    ],
)
def handle_timer(text: str) -> str:
    match = re.search(
        r"(\d+)\s*(second|minute|hour)s?", text, re.IGNORECASE
    )
    if not match:
        return "Please specify the duration. For example: set a timer for 5 minutes."

    amount = int(match.group(1))
    unit = match.group(2).lower()

    unit_map = {"second": 1, "minute": 60, "hour": 3600}
    seconds = amount * unit_map.get(unit, 1)

    timer = threading.Timer(seconds, _timer_expired, args=[amount, unit])
    timer.daemon = True
    timer.start()
    _timers.append(timer)

    return f"Timer set for {amount} {unit if amount == 1 else unit + 's'}."


def _timer_expired(amount: int, unit: str) -> None:
    unit_label = unit if amount == 1 else unit + "s"
    message = f"Timer finished! {amount} {unit_label} have passed."
    _speak_async(message)

# --- Notes ---------------------------------------------------------------

@register(
    name="note",
    description="Save a note to notes.txt",
    patterns=[
        r"(take|make|write)\s+(a\s+)?note(\s+to\s+|\s*:?\s*)",
        r"note\s+(this\s+)?down\s+",
        r"remember\s+(that\s+)?",
    ],
)
def handle_note(text: str) -> str:
    content = _extract_query(text, [
        r"(?:take|make|write)\s+(?:a\s+)?note(?:\s+to\s+|\s*:?\s*)",
        r"note\s+(?:this\s+)?down\s+",
        r"remember\s+(?:that\s+)?",
    ])
    if not content:
        return "What would you like me to note down?"

    try:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        with open("notes.txt", "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {content}\n")
        return f"Note saved: {content}"
    except OSError as e:
        logger.error("Failed to write note: %s", e)
        return "Sorry, I couldn't save the note."

# --- System Commands -----------------------------------------------------

@register(
    name="shutdown",
    description="Shut down the computer (asks for confirmation)",
    patterns=[
        r"(shut\s*down|power\s*off|turn\s*off)\s+(the\s+)?(computer|pc|system|machine)",
        r"shutdown\s+(\w+)",
    ],
)
def handle_shutdown(text: str) -> str:
    return (
        "Are you sure you want to shut down the computer? "
        "Say yes to confirm or no to cancel."
    )


@register(
    name="restart",
    description="Restart the computer (asks for confirmation)",
    patterns=[
        r"(restart|reboot|reset)\s+(the\s+)?(computer|pc|system|machine)",
        r"restart\s+(\w+)",
    ],
)
def handle_restart(text: str) -> str:
    return (
        "Are you sure you want to restart the computer? "
        "Say yes to confirm or no to cancel."
    )

# --- Confirmation handler -------------------------------------------------

def handle_confirmation(text: str) -> str | None:
    text_lower = text.lower().strip()
    if text_lower in ("yes", "yeah", "yep", "sure", "go ahead", "confirm"):
        return None  # caller handles this
    if text_lower in ("no", "nope", "cancel", "never mind", "don't", "stop"):
        return "Cancelled."
    return None

# --- Help -----------------------------------------------------------------

@register(
    name="help",
    description="List all available commands",
    patterns=[
        r"(what\s+)?(can\s+you\s+do|commands|help|capabilities)",
        r"list\s+(all\s+)?commands",
        r"how\s+(can\s+)?(you\s+)?help",
        r"what\s+are\s+your\s+(commands|features|capabilities)",
        r"^help$",
    ],
)
def handle_help(text: str) -> str:
    commands = get_all_commands()
    lines = [f"I can help you with {len(commands)} things:"]
    for cmd in sorted(commands, key=lambda c: c.name):
        lines.append(f"  - {cmd.name}: {cmd.description}")
    return "\n".join(lines)


# --- Exit -----------------------------------------------------------------

@register(
    name="exit",
    description="Exit the voice assistant",
    patterns=[
        r"^(exit|quit|bye|goodbye|stop|shut\s*up)$",
        r"(exit|quit)\s+(the\s+)?(app|assistant|program)",
        r"that(\'s| is)\s+all",
        r"goodbye",
        r"see\s+you\s+(later|soon)",
    ],
)
def handle_exit(text: str) -> str:
    return "EXIT"
