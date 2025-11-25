"""Model conversion dispatcher for Java to Bedrock format.

This module provides a unified interface that dispatches to either:
- item_2d.py for 2D sprite/generated items
- item_3d.py for 3D model items

This separation ensures changes to 2D conversion don't affect 3D and vice versa.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from .item_2d import convert_2d_item
from .item_3d import convert_3d_item


def convert_model(
    entry: Mapping[str, Any],
    resolved_model: Mapping[str, Any],
    rp_root: Path,
    bp_root: Path,
    textures_root: Path,
    materials: Mapping[str, str],
) -> dict[str, Path]:
    """
    Convert a resolved Java model entry into Bedrock assets.

    This is a dispatcher that routes to either 2D or 3D conversion based on
    whether the model is "generated" (2D sprite) or has actual geometry (3D).

    Args:
        entry: Single config row containing fields like `path_hash`, `namespace`,
               `model_path`, `model_name`, `generated`, etc.
        resolved_model: Output of `resolve_parental` for the same entry.
        rp_root: Root directory for the Bedrock resource pack.
        bp_root: Root directory for the Bedrock behavior pack.
        textures_root: Destination directory for texture/atlas PNGs.
        materials: Dict with keys `attachable_material` and `block_material`.

    Returns:
        Mapping summarizing the files written.

    Raises:
        ValueError: If required entry metadata is missing or inconsistent.
    """
    required_keys = {"path_hash", "namespace", "model_path", "model_name", "generated"}
    missing = required_keys - set(entry)
    if missing:
        raise ValueError(f"Entry missing required keys: {', '.join(sorted(missing))}")

    is_2d = bool(entry["generated"])

    if is_2d:
        # Route to 2D sprite conversion (item_2d.py)
        return convert_2d_item(entry, resolved_model, rp_root, bp_root, textures_root, materials)
    else:
        # Route to 3D model conversion (item_3d.py)
        return convert_3d_item(entry, resolved_model, rp_root, bp_root, textures_root, materials)
