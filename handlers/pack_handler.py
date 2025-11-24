"""Pack extraction and validation handlers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional


def locate_pack_root(extracted_root: Path) -> Optional[Path]:
    """
    Find the root directory of a Minecraft resource pack.

    Looks for pack.mcmeta to identify the pack root.

    Args:
        extracted_root: Root directory where the pack was extracted.

    Returns:
        Path to the pack root, or None if not found.
    """
    if (extracted_root / "pack.mcmeta").exists():
        return extracted_root
    
    candidates = list(extracted_root.glob("**/pack.mcmeta"))
    return candidates[0].parent if candidates else None


def read_pack_description(mcmeta_path: Path) -> str:
    """
    Read the pack description from pack.mcmeta file.

    Args:
        mcmeta_path: Path to the pack.mcmeta file.

    Returns:
        Pack description string, or a default if not found.
    """
    try:
        data = json.loads(mcmeta_path.read_text(encoding="utf-8"))
        return data.get("pack", {}).get("description", "Converted Resource Pack")
    except Exception:
        return "Converted Resource Pack"
