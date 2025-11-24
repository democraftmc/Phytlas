"""Dependency checking and job throttling utilities."""

from __future__ import annotations

import subprocess
import threading
import time
from typing import Optional, Sequence

from utils.logging import status_message


def ensure_dependency(
    name: str, 
    check_command: Sequence[str], 
    expect_tokens: Optional[Sequence[str]] = None
) -> None:
    """
    Verify a CLI dependency is reachable and working.

    Args:
        name: Friendly dependency name for error reporting.
        check_command: Exact argv executed via subprocess.
        expect_tokens: Optional substrings that must appear in stdout/stderr.

    Raises:
        RuntimeError: If the command is missing or validation fails.
    """
    try:
        completed = subprocess.run(
            check_command,
            capture_output=True,
            text=True,
            check=True,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(f"Dependency {name} is not installed") from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"Dependency {name} failed health check") from exc

    output = f"{completed.stdout}{completed.stderr}" if completed else ""
    if expect_tokens:
        if not any(token in output for token in expect_tokens):
            raise RuntimeError(
                f"Dependency {name} is present but did not report an expected version; "
                f"saw: {output.strip() or '<empty>'}"
            )

    status_message("completion", f"Dependency {name} satisfied")


def throttle_jobs(max_parallel: int) -> None:
    """
    Block until the number of outstanding worker tasks drops below max_parallel.

    This is a simple implementation that works with threading.

    Args:
        max_parallel: Upper bound on concurrent asynchronous jobs.

    Returns:
        None. Blocks until job count is within limit.
    """
    if max_parallel <= 0:
        return

    while max(threading.active_count() - 1, 0) >= max_parallel:
        time.sleep(0.05)
