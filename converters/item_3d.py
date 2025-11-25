"""3D model item conversion from Java to Bedrock format.

This module handles items with actual 3D geometry (cubes/elements).
Changes here will NOT affect 2D sprite conversion.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from services.texture_atlas import generate_atlas
from .geometry import build_geometry


def convert_3d_item(
    entry: Mapping[str, Any],
    resolved_model: Mapping[str, Any],
    rp_root: Path,
    bp_root: Path,
    textures_root: Path,
    materials: Mapping[str, str],
) -> dict[str, Path]:
    """
    Convert a 3D Java model item into Bedrock geometry, behavior, and attachable assets.

    This handles items with actual geometry (cubes/elements) that need atlas generation
    and geometry conversion.

    Args:
        entry: Single config row containing fields like `path_hash`, `namespace`,
               `model_path`, `model_name`, `geometry`, etc.
        resolved_model: Output of `resolve_parental` for the same entry.
        rp_root: Root directory for the Bedrock resource pack.
        bp_root: Root directory for the Bedrock behavior pack.
        textures_root: Destination directory for generated atlas PNGs.
        materials: Dict with keys `attachable_material` and `block_material`.

    Returns:
        Mapping summarizing the files written.

    Raises:
        ValueError: If required entry metadata is missing or inconsistent.
    """
    files_written: dict[str, Path] = {}

    namespace = entry["namespace"]
    model_path = entry["model_path"].strip("/")
    model_name = entry["model_name"]
    path_hash = entry["path_hash"]
    geometry_id = entry.get("geometry", path_hash)
    identifier = f"geyser_custom:{path_hash}"

    attachable_material = materials.get("attachable_material", "entity_alphatest_one_sided")
    block_material = materials.get("block_material", "alpha_test")

    # Setup directories
    rp_models_dir = rp_root / "models" / "blocks" / namespace / model_path
    rp_models_dir.mkdir(parents=True, exist_ok=True)

    bp_blocks_dir = bp_root / "blocks" / namespace / model_path
    bp_blocks_dir.mkdir(parents=True, exist_ok=True)

    rp_attachables_dir = rp_root / "attachables" / namespace / model_path
    rp_attachables_dir.mkdir(parents=True, exist_ok=True)

    # Generate texture atlas from model textures
    textures = resolved_model["texture_paths"]
    atlas_key, frames, atlas_path, atlas_size = generate_atlas(
        textures, textures_root, path_hash
    )
    files_written["atlas"] = atlas_path

    # Build Bedrock geometry from Java elements
    geometry_identifier = f"geometry.geyser_custom.{geometry_id}"
    geometry = build_geometry(
        resolved_model["elements"], 
        frames, 
        atlas_size, 
        geometry_identifier
    )
    geometry_file = rp_models_dir / f"{model_name}.json"
    geometry_file.write_text(json.dumps(geometry, indent=2), encoding="utf-8")
    files_written["geometry"] = geometry_file

    # Write block definition
    block_def = create_3d_block_definition(identifier, atlas_key, geometry_identifier, block_material)
    block_file = bp_blocks_dir / f"{model_name}.json"
    block_file.write_text(json.dumps(block_def, indent=2), encoding="utf-8")
    files_written["block"] = block_file

    # Write attachable definition
    attachable = create_3d_attachable_definition(
        identifier,
        attachable_material,
        atlas_path.name,
        geometry_identifier,
    )
    attachable_file = rp_attachables_dir / f"{model_name}.{path_hash}.attachable.json"
    attachable_file.write_text(json.dumps(attachable, indent=2), encoding="utf-8")
    files_written["attachable"] = attachable_file

    return files_written


def create_3d_block_definition(
    identifier: str,
    atlas_key: str,
    geometry_identifier: str,
    block_material: str,
) -> dict[str, Any]:
    """
    Create Bedrock block definition JSON for a 3D model.

    Args:
        identifier: Bedrock block identifier (e.g., "geyser_custom:gmdl_abc1234").
        atlas_key: Texture atlas key for material instances.
        geometry_identifier: Geometry identifier string.
        block_material: Bedrock material/render method.

    Returns:
        Block definition dictionary ready for JSON serialization.
    """
    return {
        "format_version": "1.16.100",
        "minecraft:block": {
            "description": {
                "identifier": identifier,
            },
            "components": {
                "minecraft:material_instances": {
                    "*": {
                        "texture": atlas_key,
                        "render_method": block_material,
                        "face_dimming": False,
                        "ambient_occlusion": False,
                    }
                },
                "minecraft:geometry": geometry_identifier,
            },
        },
    }


def create_3d_attachable_definition(
    identifier: str,
    material: str,
    atlas_filename: str,
    geometry_identifier: str,
) -> dict[str, Any]:
    """
    Create Bedrock attachable definition JSON for a 3D model item.

    Args:
        identifier: Bedrock item identifier.
        material: Bedrock material name for rendering.
        atlas_filename: Filename of the atlas texture in textures/ folder.
        geometry_identifier: Geometry identifier string.

    Returns:
        Attachable definition dictionary ready for JSON serialization.
    """
    return {
        "format_version": "1.10.0",
        "minecraft:attachable": {
            "description": {
                "identifier": identifier,
                "materials": {"default": material},
                "textures": {"default": f"textures/{atlas_filename}"},
                "geometry": {"default": geometry_identifier},
                "scripts": {"animate": []},
                "render_controllers": ["controller.render.item_default"],
            },
        },
    }
