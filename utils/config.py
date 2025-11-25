"""Configuration management utilities."""

from __future__ import annotations

import os

from .logging import status_message

# Global configuration cache
_CONFIG_CACHE: dict[str, str] = {}


def prompt_config_value(key: str, prompt: str, default: str, description: str) -> str:
    """
    Ask the user for a configuration value only when it is unset.

    Checks cache first, then environment variables, then prompts user.

    Args:
        key: Identifier used to store and retrieve the configuration value.
        prompt: Human-readable question displayed to the user.
        default: Value adopted when the user presses enter without input.
        description: Short explanation echoed back in summaries.

    Returns:
        The resolved configuration string.
    """
    # Check cache first
    cached = _CONFIG_CACHE.get(key)
    if cached:
        return cached

    # Check environment variables
    env_value = os.environ.get(key)
    if env_value:
        _CONFIG_CACHE[key] = env_value
        return env_value

    # Prompt user
    status_message("plain", f"{prompt} [{default}]\n")
    try:
        response = input(f"{description}: ")
    except EOFError:
        response = ""

    print()
    resolved = response.strip() or default
    _CONFIG_CACHE[key] = resolved
    return resolved


def clear_config_cache() -> None:
    """Clear the configuration cache."""
    _CONFIG_CACHE.clear()


def get_cached_config(key: str) -> str | None:
    """
    Get a cached configuration value without prompting.

    Args:
        key: Configuration key to retrieve.

    Returns:
        The cached value or None if not found.
    """
    return _CONFIG_CACHE.get(key)
