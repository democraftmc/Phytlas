"""Logging utilities for status messages with color support."""

from __future__ import annotations

import sys
from typing import Literal

# Color theme definitions for different message types
COLOR_THEMES: dict[str, str] = {
    "completion": "\033[32m[+]\033[0m ",
    "process": "\033[33m[•]\033[0m ",
    "critical": "\033[31m[X]\033[0m ",
    "error": "\033[31m[ERROR]\033[0m ",
    "info": "\033[36m",
    "plain": "",
}

MessageLevel = Literal["completion", "process", "critical", "error", "info", "plain"]


def status_message(level: MessageLevel, message: str) -> None:
    """
    Render a normalized status line with color coding.

    Args:
        level: Semantic label such as "completion", "process", "critical", 
               "error", "info", or "plain".
        message: Message body to display.

    Returns:
        None. Emits directly to stdout/stderr.
    """
    normalized = level.lower().strip()
    prefix = COLOR_THEMES.get(normalized, COLOR_THEMES["plain"])
    suffix = "\033[0m" if normalized == "info" else ""
    stream = sys.stderr if normalized in {"error", "critical"} else sys.stdout
    text = message.rstrip("\n")
    stream.write(f"{prefix}{text}{suffix}\n")
    stream.flush()
