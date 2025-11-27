"""2D sprite/generated item conversion from Java to Bedrock format.

This module handles items that are flat 2D sprites (generated from builtin/generated parent).
Changes here will NOT affect 3D model conversion.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Mapping


def convert_2d_item(
    entry: Mapping[str, Any],
    resolved_model: Mapping[str, Any],
    rp_root: Path,
    bp_root: Path,
    textures_root: Path,
    materials: Mapping[str, str],
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
    
    namespace = entry["namespace"]
    model_path = entry["model_path"].strip("/")
    model_name = entry["model_name"]
    path_hash = entry["path_hash"]
    identifier = f"geyser_custom:{path_hash}"
    
    attachable_material = materials.get("attachable_material", "entity_alphatest_one_sided")

    # Setup directories
    bp_items_dir = bp_root / "items" / namespace / model_path
    bp_items_dir.mkdir(parents=True, exist_ok=True)

    rp_attachables_dir = rp_root / "attachables" / namespace / model_path
    rp_attachables_dir.mkdir(parents=True, exist_ok=True)

    # Copy the first available texture
    texture_paths = list(resolved_model["texture_paths"].values())
    if not texture_paths:
        raise ValueError(f"2D item {path_hash} has no textures to copy")
    
    texture_target = textures_root / f"{path_hash}.png"
    texture_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(texture_paths[0], texture_target)

    # Write item definition
    item_def = create_2d_item_definition(identifier, path_hash)
    item_file = bp_items_dir / f"{model_name}.{path_hash}.json"
    item_file.write_text(json.dumps(item_def, indent=2), encoding="utf-8")
    files_written["item"] = item_file

    # Write attachable definition
    attachable = create_2d_attachable_definition(
        identifier, 
        attachable_material, 
        texture_target.name
    )
    # Shorten filename to avoid path length issues on some platforms
    short_name = model_name[:20] if len(model_name) > 20 else model_name
    attachable_file = rp_attachables_dir / f"{short_name}.{path_hash}.attachable.json"
    attachable_file.write_text(json.dumps(attachable, indent=2), encoding="utf-8")
    files_written["attachable"] = attachable_file

    return files_written


def create_2d_item_definition(identifier: str, texture_key: str) -> dict[str, Any]:
    """
    Create Bedrock item definition JSON for a 2D sprite item.

    Args:
        identifier: Bedrock item identifier (e.g., "geyser_custom:gmdl_abc1234").
        texture_key: Texture key for the item icon.

    Returns:
        Item definition dictionary ready for JSON serialization.
    """
    return {
        "format_version": "1.16.100",
        "minecraft:item": {
            "description": {
                "identifier": identifier,
                "category": "items",
            },
            "components": {
                "minecraft:icon": {
                    "texture": texture_key,
                }
            },
        },
    }


def create_2d_attachable_definition(
    identifier: str,
    material: str,
    texture_filename: str,
) -> dict[str, Any]:
    """
    Create Bedrock attachable definition JSON for a 2D sprite item.

    Args:
        identifier: Bedrock item identifier.
        material: Bedrock material name for rendering.
        texture_filename: Filename of the texture in textures/ folder.

    Returns:
        Attachable definition dictionary ready for JSON serialization.
    """
    return {
        "format_version": "1.10.0",
        "minecraft:attachable": {
            "description": {
                "identifier": identifier,
                "materials": {"default": material},
                "textures": {"default": f"textures/{texture_filename}"},
                "geometry": {},
                "scripts": {},
            }
        },
    }
