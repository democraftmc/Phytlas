"""Language file generation handlers."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import List, Tuple


def write_language_files(texts_dir: Path, lang_entries: List[Tuple[str, str]]) -> None:
    """
    Write Bedrock language files for item names.

    Creates en_US.lang, en_GB.lang, and languages.json files.

    Args:
        texts_dir: Directory where language files should be written.
        lang_entries: List of (key, display_name) tuples for item translations.

    Returns:
        None. Creates language files in the texts directory.
    """
    texts_dir.mkdir(parents=True, exist_ok=True)
    
    lines = [f"item.geyser_custom:{key}.name={value}" for key, value in lang_entries]
    
    (texts_dir / "en_US.lang").write_text("\n".join(lines), encoding="utf-8")
    shutil.copy2(texts_dir / "en_US.lang", texts_dir / "en_GB.lang")
    
    (texts_dir / "languages.json").write_text(
        json.dumps(["en_US", "en_GB"], indent=2), 
        encoding="utf-8"
    )


def format_display_name(item_id: str, cmd: int) -> str:
    """
    Format a display name for an item with custom model data.

    Args:
        item_id: Full item identifier (e.g., "minecraft:diamond_sword").
        cmd: Custom model data value.

    Returns:
        Formatted display name (e.g., "Diamond Sword (CMD 123)").
    """
    base = item_id.split(":")[-1].replace("_", " ").title()
    return f"{base} (CMD {cmd})"
