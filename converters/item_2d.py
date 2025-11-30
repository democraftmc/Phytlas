"""2D sprite/generated item conversion from Java to Bedrock format.

This module handles items that are flat 2D sprites (generated from builtin/generated parent).
Changes here will NOT affect 3D model conversion.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any, Mapping


def convert_2d_item(
    entry: Mapping[str, Any],
    resolved_model: Mapping[str, Any],
    textures_root: Path,
) -> dict[str, Path]:
    """
    Convert a 2D sprite/generated Java item into Bedrock assets.

    This handles items with parent "builtin/generated" that are flat textures
    without 3D geometry.

    Args:
        entry: Single config row containing fields like `path_hash`, `namespace`,
               `model_path`, `model_name`, etc.
        resolved_model: Output of `resolve_parental` for the same entry.
        rp_root: Root directory for the Bedrock resource pack.
        bp_root: Root directory for the Bedrock behavior pack.
        textures_root: Destination directory for texture PNGs.
        materials: Dict with keys `attachable_material` and `block_material`.

    Returns:
        Mapping summarizing the files written.

    Raises:
        ValueError: If required entry metadata is missing or no textures available.
    """
    files_written: dict[str, Path] = {}
    
    path_hash = entry["path_hash"]

    # Copy the first available texture to textures/2d_items/{path_hash}.png
    texture_paths = list(resolved_model["texture_paths"].values())
    if not texture_paths:
        raise ValueError(f"2D item {path_hash} has no textures to copy")
    texture_target = textures_root / "2d_items" / f"{path_hash}.png"
    texture_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(texture_paths[0], texture_target)
    files_written["texture"] = texture_target

    return files_written