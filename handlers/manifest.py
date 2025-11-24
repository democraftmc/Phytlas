"""Manifest and texture configuration file handlers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping


def write_disable_animation(animations_dir: Path) -> None:
    """
    Write the Geyser custom disable animation file.

    This animation is used to disable model rendering when needed.

    Args:
        animations_dir: Directory where the animation file should be written.

    Returns:
        None. Creates the animation file.
    """
    animations_dir.mkdir(parents=True, exist_ok=True)
    
    payload = {
        "format_version": "1.8.0",
        "animations": {
            "animation.geyser_custom.disable": {
                "loop": True,
                "override_previous_animation": True,
                "bones": {"geyser_custom": {"scale": 0}},
            }
        },
    }
    
    (animations_dir / "animation.geyser_custom.disable.json").write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )


def write_texture_manifest(
    path: Path, 
    atlas_name: str, 
    texture_data: Mapping[str, Any]
) -> None:
    """
    Write a Bedrock texture manifest file.

    Args:
        path: Destination path for the manifest file.
        atlas_name: Name of the texture atlas (e.g., "atlas.items").
        texture_data: Mapping of texture identifiers to their configuration.

    Returns:
        None. Writes the manifest file.
    """
    payload = {
        "resource_pack_name": "geyser_custom",
        "texture_name": atlas_name,
        "texture_data": texture_data,
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
