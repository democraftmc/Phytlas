"""Model conversion from Java to Bedrock format."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Mapping

from services.texture_atlas import generate_atlas
from .geometry import build_geometry


def convert_model(
    entry: Mapping[str, Any],
    resolved_model: Mapping[str, Any],
    rp_root: Path,
    bp_root: Path,
    textures_root: Path,
    materials: Mapping[str, str],
) -> dict[str, Path]:
    """
    Convert a resolved Java model entry into Bedrock geometry, behavior, and attachable assets.

    Args:
        entry: Single config row containing fields like `path_hash`, `namespace`, 
               `model_path`, `model_name`, `generated`, etc.
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
    required_keys = {"path_hash", "namespace", "model_path", "model_name", "generated"}
    missing = required_keys - set(entry)
    if missing:
        raise ValueError(f"Entry missing required keys: {', '.join(sorted(missing))}")

    files_written: dict[str, Path] = {}
    namespace = entry["namespace"]
    model_path = entry["model_path"].strip("/")
    model_name = entry["model_name"]
    path_hash = entry["path_hash"]
    generated = bool(entry["generated"])
    geometry_id = entry.get("geometry", path_hash)
    identifier = f"geyser_custom:{path_hash}"

    rp_models_dir = rp_root / "models" / "blocks" / namespace / model_path
    rp_models_dir.mkdir(parents=True, exist_ok=True)

    bp_blocks_dir = bp_root / "blocks" / namespace / model_path
    bp_items_dir = bp_root / "items" / namespace / model_path
    bp_blocks_dir.mkdir(parents=True, exist_ok=True)
    bp_items_dir.mkdir(parents=True, exist_ok=True)

    rp_attachables_dir = rp_root / "attachables" / namespace / model_path
    rp_attachables_dir.mkdir(parents=True, exist_ok=True)

    textures_dir = textures_root

    attachable_material = materials.get("attachable_material", "entity_alphatest_one_sided")
    block_material = materials.get("block_material", "alpha_test")

    if generated:
        # 2D sprite path: copy the first available texture
        texture_paths = list(resolved_model["texture_paths"].values())
        if not texture_paths:
            raise ValueError(f"Generated model {path_hash} has no textures to copy")
        
        texture_target = textures_dir / f"{path_hash}.png"
        texture_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(texture_paths[0], texture_target)

        item_def = {
            "format_version": "1.16.100",
            "minecraft:item": {
                "description": {
                    "identifier": identifier,
                    "category": "items",
                },
                "components": {
                    "minecraft:icon": {
                        "texture": path_hash,
                    }
                },
            },
        }
        item_file = bp_items_dir / f"{model_name}.{path_hash}.json"
        item_file.write_text(json.dumps(item_def, indent=2), encoding="utf-8")
        files_written["item"] = item_file

        attachable = {
            "format_version": "1.10.0",
            "minecraft:attachable": {
                "description": {
                    "identifier": identifier,
                    "materials": {"default": attachable_material},
                    "textures": {"default": f"textures/{texture_target.name}"},
                    "geometry": {},
                    "scripts": {},
                }
            },
        }
        attachable_file = rp_attachables_dir / f"{model_name}.{path_hash}.attachable.json"
        attachable_file.write_text(json.dumps(attachable, indent=2), encoding="utf-8")
        files_written["attachable"] = attachable_file
        return files_written

    # 3D model path: generate atlas and geometry
    textures = resolved_model["texture_paths"]
    atlas_key, frames, atlas_path, atlas_size = generate_atlas(textures, textures_dir, path_hash)
    files_written["atlas"] = atlas_path

    geometry_identifier = f"geometry.geyser_custom.{geometry_id}"
    geometry = build_geometry(resolved_model["elements"], frames, atlas_size, geometry_identifier)
    geometry_file = rp_models_dir / f"{model_name}.json"
    geometry_file.write_text(json.dumps(geometry, indent=2), encoding="utf-8")
    files_written["geometry"] = geometry_file

    block_def = {
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
    block_file = bp_blocks_dir / f"{model_name}.json"
    block_file.write_text(json.dumps(block_def, indent=2), encoding="utf-8")
    files_written["block"] = block_file

    attachable = {
        "format_version": "1.10.0",
        "minecraft:attachable": {
            "description": {
                "identifier": identifier,
                "materials": {"default": attachable_material},
                "textures": {"default": f"textures/{atlas_path.name}"},
                "geometry": {"default": geometry_identifier},
                "scripts": {"animate": []},
                "render_controllers": ["controller.render.item_default"],
            },
        },
    }
    attachable_file = rp_attachables_dir / f"{model_name}.{path_hash}.attachable.json"
    attachable_file.write_text(json.dumps(attachable, indent=2), encoding="utf-8")
    files_written["attachable"] = attachable_file

    return files_written
