"""
High-level resource pack converter orchestration.

This module provides the main entry point for converting Java Edition resource packs
to Bedrock Edition format with Geyser custom model support.
"""

from __future__ import annotations

from collections import defaultdict
import json
import shutil
import uuid
import zipfile
from pathlib import Path
from typing import Any, Optional

from converters import resolve_parental, build_geometry, convert_2d_item, convert_3d_item
from handlers import (
    format_display_name,
    locate_pack_root,
    read_pack_description,
    write_disable_animation,
    write_language_files,
    write_texture_manifest,
)
from models import write_geyser_item_mappings
from blocks import write_geyser_block_mappings
from services import build_pack_manifests, ensure_placeholder_texture
from services.texture_atlas import generate_atlas
from services.texture_utils import split_namespace
from utils import hash_model_identifier, slugify, status_message, zip_directory


def convert_resource_pack(
    input_zip: str | Path,
    output_root: Optional[Path] = None,
    *,
    attachable_material: str = "entity_alphatest_one_sided",
    block_material: str = "alpha_test",
) -> tuple[Path, Path]:
    """
    Convert a Java resource pack zip into Bedrock-ready resource/behavior packs plus Geyser mappings.

    This is the main orchestration function that coordinates the entire conversion process:
    1. Extract and validate the input pack
    2. Build pack manifests
    3. Process model overrides
    4. Convert models to Bedrock format
    5. Generate texture atlases
    6. Create Geyser mappings
    7. Package output

    Args:
        input_zip: Path to the Java Edition resource pack ZIP file.
        output_root: Optional output directory. Defaults to ./target/.
        attachable_material: Bedrock material for attachables.
        block_material: Bedrock material for blocks.

    Returns:
        Tuple of (resource_pack_path, behavior_pack_path) pointing to the generated .mcpack files.

    Raises:
        FileNotFoundError: If input pack or required assets are missing.
        RuntimeError: If conversion fails due to missing dependencies or invalid data.
    """
    # Validate input
    input_zip = Path(input_zip).expanduser().resolve()
    if not input_zip.is_file():
        raise FileNotFoundError(f"Input pack {input_zip} was not found")

    # Setup output structure
    output_root = Path(output_root or (Path.cwd() / "target"))
    shutil.rmtree(output_root, ignore_errors=True)
    rp_root = output_root / "rp"
    bp_root = output_root / "bp"
    for root in (rp_root, bp_root):
        root.mkdir(parents=True, exist_ok=True)

    textures_root = rp_root / "textures"
    custom_blocks_location = "custom_blocks"
    blocks_root   = textures_root / custom_blocks_location
    textures_root.mkdir(parents=True, exist_ok=True)
    blocks_root.mkdir(parents=True, exist_ok=True)

    materials = {
        "attachable_material": attachable_material,
        "block_material": block_material,
    }

    # Extract and process pack
    status_message("process", f"Extracting {input_zip.name}")
    # Extract into ./pack so humans can inspect the extracted files
    extract_root = Path.cwd() / "pack"
    shutil.rmtree(extract_root, ignore_errors=True)
    extract_root.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(input_zip, "r") as archive:
        archive.extractall(extract_root)

    pack_root = locate_pack_root(extract_root)
    if pack_root is None:
        raise RuntimeError("Unable to locate pack.mcmeta in the provided archive")

    item_dir = pack_root / "assets" / "minecraft" / "models" / "item"
    block_dir = pack_root / "assets" / "minecraft" / "blockstates"
    if not item_dir.exists():
        raise RuntimeError("No assets/minecraft/models/item directory found in pack")

    pack_description = read_pack_description(pack_root / "pack.mcmeta")

    # Build pack metadata and manifests
    meta = build_pack_metadata(pack_description)
    build_pack_manifests(meta, rp_root, bp_root)

    # Copy pack icon if present
    copy_pack_icon(pack_root, rp_root, bp_root)

    # Setup animations and placeholder texture
    write_disable_animation(rp_root / "animations")
    ensure_placeholder_texture(textures_root / "custom_blocks" / "placeholder.png")

    # Process model overrides
    converted_item_entries, item_texture_data, terrain_texture_data, lang_entries = process_model_overrides(
        item_dir, pack_root, rp_root, bp_root, textures_root, materials
    )

    converted_block_entries, terrain_texture_data  = process_block_overrides(
        block_dir, pack_root, rp_root, bp_root, blocks_root, custom_blocks_location, terrain_texture_data
    )


    if not converted_item_entries:
        raise RuntimeError("No convertible custom_model_data overrides were found")

    # Write texture manifests
    write_texture_manifest(
        rp_root / "textures" / "item_texture.json",
        "atlas.items",
        item_texture_data,
    )
    write_texture_manifest(
        rp_root / "textures" / "terrain_texture.json",
        "atlas.terrain",
        terrain_texture_data,
    )

    # Write language files
    write_language_files(rp_root / "texts", lang_entries)

    # Write Geyser mappings
    mappings_path = output_root / "item_geyser_mappings.json"
    write_geyser_item_mappings(converted_item_entries, mappings_path)
    mappings_path = output_root / "block_geyser_mappings.json"
    write_geyser_block_mappings(converted_block_entries, mappings_path)

    # Package outputs
    resource_zip = output_root / f"{slugify(pack_description)}_resources.mcpack"
    behavior_zip = output_root / f"{slugify(pack_description)}_behaviors.mcpack"
    zip_directory(rp_root, resource_zip)
    zip_directory(bp_root, behavior_zip)

    status_message("completion", f"Conversion complete -> {resource_zip.name}, {behavior_zip.name}")
    return resource_zip, behavior_zip


def build_pack_metadata(pack_description: str) -> dict[str, Any]:
    """
    Build pack metadata with UUIDs and version information.

    Args:
        pack_description: Pack description string from pack.mcmeta.

    Returns:
        Dictionary containing pack metadata.
    """
    return {
        "name": pack_description,
        "description": "Adds 3D items for use with a Geyser proxy",
        "resource_header_uuid": uuid.uuid4(),
        "resource_module_uuid": uuid.uuid4(),
        "behavior_header_uuid": uuid.uuid4(),
        "behavior_module_uuid": uuid.uuid4(),
        "version": [1, 0, 0],
    }


def copy_pack_icon(pack_root: Path, rp_root: Path, bp_root: Path) -> None:
    """
    Copy pack.png icon to both resource and behavior packs if present.

    Args:
        pack_root: Root directory of the extracted Java pack.
        rp_root: Resource pack root directory.
        bp_root: Behavior pack root directory.
    """
    if (pack_root / "pack.png").exists():
        shutil.copy2(pack_root / "pack.png", rp_root / "pack_icon.png")
        shutil.copy2(pack_root / "pack.png", bp_root / "pack_icon.png")

def process_block_overrides(
    block_dir: Path,
    pack_root: Path,
    rp_root: Path,
    bp_root: Path,
    blocks_root: Path,
    custom_blocks_location: str,
    terrain_texture_data: dict[str, dict[str, str]],
) -> tuple[dict[str, list[dict[str, str]]], dict[str, dict[str, str]]]:
    """
    Process all model override files and convert them to Bedrock format.

    Args:
        block_dir: Directory containing Java block model variations
        pack_root: Root directory of the extracted Java pack.
        rp_root: Resource pack root directory.
        bp_root: Behavior pack root directory.
        textures_root: Directory for texture output.
        materials: Material configuration dictionary.

    Returns:
        Tuple of (converted_entries, item_texture_data, terrain_texture_data, lang_entries).
    """
    converted_entries: dict[str, list[dict[str, str]]] = defaultdict(list)
    status_message("process", "Walking block override files")
    counter = 0

    # Create a shared cube geometry + atlas for fallbacks (Option A)
    try:
        placeholder_tex = rp_root / "textures" / "custom_blocks" / "placeholder.png"
        # ensure blocks_root exists for atlas output
        blocks_root.mkdir(parents=True, exist_ok=True)
        cube_atlas_key, cube_frames, cube_atlas_path, cube_atlas_size = generate_atlas(
            {"all": placeholder_tex}, blocks_root, "cube"
        )
        cube_geometry_id = "cube"
        cube_geometry_identifier = f"geometry.geyser_custom.{cube_geometry_id}"
        cube_elements = [
            {
                "name": "cube",
                "from": [0, 0, 0],
                "to": [16, 16, 16],
                "faces": {
                    face: {"texture": "#all"}
                    for face in ("north", "south", "east", "west", "up", "down")
                },
                "item_display_transforms": {
                    "thirdperson_righthand": {"scale": [0.5, 0.5, 0.5]},
                    "thirdperson_lefthand": {"scale": [0.5, 0.5, 0.5]},
                    "firstperson_righthand": {"scale": [0.5, 0.5, 0.5]},
                    "firstperson_lefthand": {"scale": [0.5, 0.5, 0.5]}
                }
            }
        ]
        rp_cube_models_dir = rp_root / "models" / "blocks" / "geyser_custom"
        rp_cube_models_dir.mkdir(parents=True, exist_ok=True)
        cube_geometry = build_geometry(cube_elements, cube_frames, cube_atlas_size, cube_geometry_identifier)
        (rp_cube_models_dir / "cube.json").write_text(json.dumps(cube_geometry, indent=2), encoding="utf-8")
        # Register cube atlas in terrain texture manifest data
        terrain_texture_data[cube_atlas_key] = {"textures": f"textures/{custom_blocks_location}/{cube_atlas_path.name}"}
    except Exception as exc:
        status_message("info", f"Failed to create shared cube geometry/atlas: {exc}")
    for block_file in sorted(block_dir.rglob("*.json")):
        try:
            block_data = json.loads(block_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            status_message("error", f"[C266] Skipping invalid JSON {block_file}: {exc}")
            continue

        for variant, model_ref in block_data.get("variants", {}).items():
            target_model = model_ref.get("model") if isinstance(model_ref, dict) else None
            if not target_model:
                continue

            # Locate the referenced model JSON in the extracted pack
            namespace, relative_model = split_namespace(target_model, default_namespace="minecraft")
            model_glob = f"assets/{namespace}/models/{relative_model}.json"
            model_json = None
            for p in pack_root.rglob(model_glob):
                model_json = p
                break
            if model_json is None:
                for p in pack_root.rglob(f"{relative_model}.json"):
                    model_json = p
                    break
            if model_json is None:
                status_message("error", f"[C286] (you can ignore me) Block model JSON not found for {target_model}. Target: {model_ref}")
                continue

            try:
                resolved = resolve_parental(model_json, assets_root=pack_root)
            except Exception as exc:
                status_message("error", f"[C292] Failed to resolve {model_json}: {exc}")
                continue

            # If the model is generated (sprite) or has no elements, fallback to a cube
            elements = resolved.get("elements")
            if resolved.get("generated") or not elements:
                elements = [
                    {
                        "name": "cube",
                        "from": [0, 0, 0],
                        "to": [16, 16, 16],
                        "faces": {
                            face: {"texture": "#all"}
                            for face in ("north", "south", "east", "west", "up", "down")
                        },
                        "item_display_transforms": {
                            "thirdperson_righthand": {"scale": [0.5, 0.5, 0.5]},
                            "thirdperson_lefthand": {"scale": [0.5, 0.5, 0.5]},
                            "firstperson_righthand": {"scale": [0.5, 0.5, 0.5]},
                            "firstperson_lefthand": {"scale": [0.5, 0.5, 0.5]}
                        }
                    }
                ]

            # Build unique ids/hashes for atlas and geometry
            predicate_key = f"{block_file.stem}_{variant}_{counter}"
            entry_hash, geo_hash = hash_model_identifier(predicate_key, str(model_json))
            path_hash = f"gmdl_{entry_hash}"
            geometry_id = f"geo_{geo_hash}"
            geometry_identifier = f"geometry.geyser_custom.{geometry_id}"

            # Generate an atlas for this block's textures
            try:
                atlas_key, frames, atlas_path, atlas_size = generate_atlas(resolved["texture_paths"], blocks_root, path_hash)
            except Exception as exc:
                status_message("error", f"[C327] Atlas generation failed for {target_model}: {exc}")
                continue

            # Build Bedrock geometry and write it into the resource pack
            try:
                geometry = build_geometry(elements, frames, atlas_size, geometry_identifier)
            except Exception as exc:
                status_message("error", f"[C334] Geometry build failed for {target_model}: {exc}")
                continue

            model_parts = relative_model.split("/")
            model_name = model_parts[-1]
            model_path = "/".join(model_parts[:-1])
            rp_models_dir = rp_root / "models" / "blocks" / namespace / model_path
            rp_models_dir.mkdir(parents=True, exist_ok=True)
            geometry_file = rp_models_dir / f"{model_name}.{geometry_id}.json"
            try:
                geometry_file.write_text(json.dumps(geometry, indent=2), encoding="utf-8")
            except Exception as exc:
                status_message("error", f"[C346] Failed to write geometry {geometry_file}: {exc}")
                continue

            # Register texture in terrain texture manifest (paths relative to rp textures dir)
            terrain_texture_data[atlas_key] = {"textures": f"textures/{custom_blocks_location}/{atlas_path.name}"}

            # Append converted variant entry
            converted_entries[block_file.stem].append({
                "variant": variant,
                "geometry": geometry_identifier,
                "texture": atlas_key,
            })

            counter += 1

    return converted_entries, terrain_texture_data

def process_model_overrides(
    item_dir: Path,
    pack_root: Path,
    rp_root: Path,
    bp_root: Path,
    textures_root: Path,
    materials: dict[str, str],
) -> tuple[list[dict[str, Any]], dict[str, dict[str, str]], dict[str, dict[str, str]], list[tuple[str, str]]]:
    """
    Process all model override files and convert them to Bedrock format.

    Args:
        item_dir: Directory containing Java item model JSON files.
        pack_root: Root directory of the extracted Java pack.
        rp_root: Resource pack root directory.
        bp_root: Behavior pack root directory.
        textures_root: Directory for texture output.
        materials: Material configuration dictionary.

    Returns:
        Tuple of (converted_entries, item_texture_data, terrain_texture_data, lang_entries).
    """
    converted_entries: list[dict[str, Any]] = []
    item_texture_data: dict[str, dict[str, str]] = {}
    terrain_texture_data: dict[str, dict[str, str]] = {}
    lang_entries: list[tuple[str, str]] = []

    status_message("process", "Walking item override files")
    
    for model_file in sorted(item_dir.rglob("*.json")):
        item_id = f"minecraft:{model_file.stem}"
        
        try:
            model_data = json.loads(model_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            status_message("error", f"[C398] Skipping invalid JSON {model_file}: {exc}")
            continue

        for index, override in enumerate(model_data.get("overrides") or []):
            predicate = override.get("predicate") or {}
            cmd = predicate.get("custom_model_data")
            if cmd is None:
                continue
            
            target_model = override.get("model")
            if not target_model:
                continue

            # Process single override
            entry = process_single_item_override(
                item_id, cmd, index, target_model, pack_root, 
                rp_root, bp_root, textures_root, materials
            )
            
            if entry is None:
                continue

            converted_entries.append(entry)
            
            display_name = format_display_name(item_id, int(cmd))
            lang_entries.append((entry["path_hash"], display_name))

            # Add texture data
            if entry["generated"]:
                item_texture_data[entry["path_hash"]] = {
                    "textures": f"textures/2d_items/{entry['path_hash']}"
                }
            else:
                # For 3D items, the icon is at textures/{path_hash}.png
                # The key is {path_hash}
                item_texture_data[entry["path_hash"]] = {
                    "textures": f"textures/{entry['path_hash']}"
                }
                
                # We also register the atlas in terrain_texture.json for completeness/debugging,
                # although the attachable points to the file directly.
                # The atlas is now in textures/models/{path_hash}.png
                atlas_key = f"gmdl_atlas_{entry['path_hash']}"
                terrain_texture_data[atlas_key] = {
                    "textures": f"textures/models/{entry['path_hash']}"
                }

    return converted_entries, item_texture_data, terrain_texture_data, lang_entries


def process_single_item_override(
    item_id: str,
    cmd: int,
    index: int,
    target_model: str,
    pack_root: Path,
    rp_root: Path,
    bp_root: Path,
    textures_root: Path,
    materials: dict[str, str],
) -> Optional[dict[str, Any]]:
    """
    Process a single model override entry.

    Args:
        item_id: Full item identifier.
        cmd: Custom model data value.
        index: Override index in the array.
        target_model: Target model path reference.
        pack_root: Root directory of the extracted Java pack.
        rp_root: Resource pack root directory.
        bp_root: Behavior pack root directory.
        textures_root: Directory for texture output.
        materials: Material configuration dictionary.

    Returns:
        Entry dictionary if successful, None if processing failed.
    """
    namespace, relative_model = split_namespace(target_model, default_namespace="minecraft")
    target_json = pack_root / "assets" / namespace / "models" / f"{relative_model}.json"
    
    if not target_json.exists():
        status_message("error", f"[C480] Missing referenced model {target_model}")
        return None

    try:
        resolved = resolve_parental(target_json, assets_root=pack_root)
    except Exception as exc:
        status_message("error", f"[C486] Failed to resolve {target_json}: {exc}")
        return None

    predicate_key = f"{item_id}_cmd{cmd}_idx{index}"
    entry_hash, geo_hash = hash_model_identifier(predicate_key, str(target_json))
    path_hash = f"gmdl_{entry_hash}"
    geometry_id = f"geo_{geo_hash}"
    model_parts = relative_model.split("/")
    model_name = model_parts[-1]
    model_path = "/".join(model_parts[:-1])

    entry = {
        "item": item_id,
        "path_hash": path_hash,
        "namespace": namespace,
        "model_path": model_path,
        "model_name": model_name,
        "generated": resolved["generated"],
        "geometry": geometry_id,
        "bedrock_icon": {"icon": "camera", "frame": 0},
        "nbt": {"CustomModelData": int(cmd)},
    }

    try:
        required_keys = {"path_hash", "namespace", "model_path", "model_name", "generated"}
        missing = required_keys - set(entry)
        if missing:
            raise ValueError(f"Entry missing required keys: {', '.join(sorted(missing))}")

        is_2d = bool(entry["generated"])

        if is_2d:
            # Route to 2D sprite conversion (item_2d.py)
            convert_2d_item(entry, resolved, rp_root, bp_root, textures_root, materials)
        else:
            # Route to 3D model conversion (item_3d.py)
            convert_3d_item(entry, resolved, rp_root, bp_root, textures_root, materials)
    except Exception as exc:
        status_message("error", f"[C524] Conversion failed for {target_model}: {exc}")
        return None

    return entry


import argparse
import sys


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert Java Edition resource pack to Bedrock Edition."
    )
    parser.add_argument("input_pack", help="Path to the input resource pack (zip or directory)")
    parser.add_argument("-o", "--output", help="Output directory", default="target")
    parser.add_argument("--attachable-material", default="entity_alphatest_one_sided", help="Material for attachables")
    parser.add_argument("--block-material", default="alpha_test", help="Material for blocks")

    args = parser.parse_args()

    try:
        convert_resource_pack(
            args.input_pack,
            Path(args.output),
            attachable_material=args.attachable_material,
            block_material=args.block_material,
        )
    except Exception as e:
        status_message("error", "[Main Core]" + str(e))
        sys.exit(1)