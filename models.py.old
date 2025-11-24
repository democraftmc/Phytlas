from __future__ import annotations

from collections import defaultdict
import json
import math
import os
from pathlib import Path
import shutil
from typing import Any, Iterable, Mapping, MutableMapping


def resolve_parental(
    model_path: Path,
    assets_root: Path | None = None,
) -> dict[str, Any]:
    """
    Resolve a Java model's inheritance chain until concrete geometry + textures exist.

    Args:
    - model_path: Absolute path to the JSON model definition inside the extracted Java pack.
    - assets_root: Optional override pointing to the root folder that contains the `assets/`
      directory. Defaults to `model_path.parents[3]`, which matches the Java pack layout
      (`<pack>/assets/<namespace>/models/...`).

    Returns:
    - Dict containing:
        * elements: list of resolved cubes (or None for generated/builtin models).
        * textures: merged texture dictionary with the lowest child overriding parents.
        * display: resolved display settings, if any.
        * generated: bool indicating whether the model ultimately comes from
          `builtin/generated` (meaning it should be treated as a 2D sprite).
        * parent_chain: list of model files that were inspected, deepest parent last.
        * texture_paths: mapping of texture keys to their on-disk PNG `Path` objects.

    Raises:
    - FileNotFoundError if a referenced parent cannot be located on disk.
    - ValueError if a parental loop is detected or if no geometry/textures could be
      resolved.
    """

    assets_root = assets_root or model_path.parents[3]
    current = Path(model_path)
    visited: set[Path] = set()
    parent_chain: list[str] = []
    resolved_elements: list[Any] | None = None
    resolved_display: dict[str, Any] | None = None
    resolved_textures: MutableMapping[str, str] = {}
    generated_model = False

    while True:
        if current in visited:
            raise ValueError(f"Circular parent reference detected for {model_path}")
        visited.add(current)
        parent_chain.append(str(current))
        model = json.loads(current.read_text(encoding="utf-8"))

        if resolved_elements is None and "elements" in model:
            resolved_elements = model["elements"]
        if "textures" in model:
            # Child definitions override parents, so we only fill missing keys.
            for key, value in model["textures"].items():
                resolved_textures.setdefault(key, value)
        if resolved_display is None and "display" in model:
            resolved_display = model["display"]

        parent = model.get("parent")
        if (resolved_elements is not None) or parent is None:
            generated_model = parent in {"builtin/generated", "minecraft:builtin/generated"}
            break

        parent_path = _parent_to_model_path(parent, assets_root)
        if not parent_path.exists():
            raise FileNotFoundError(f"Missing parent model {parent} for {model_path}")
        current = parent_path

    if resolved_elements is None and not generated_model:
        raise ValueError(f"Model {model_path} has no geometry even after resolving parents")

    texture_paths = _resolve_texture_files(resolved_textures, assets_root)

    return {
        "elements": resolved_elements,
        "textures": resolved_textures,
        "display": resolved_display,
        "generated": generated_model,
        "parent_chain": parent_chain,
        "texture_paths": texture_paths,
    }


def generate_atlas(
    texture_files: Mapping[str, Path],
    output_dir: Path,
    atlas_name: str,
) -> tuple[str, dict[str, dict[str, float]], Path, tuple[int, int]]:
    """
    Generate a single PNG atlas for all textures required by one model.

    The atlas is built as a simple vertical strip (one texture per row). This keeps the
    packing logic deterministic without requiring external CLI tools.

    Args:
    - texture_files: Mapping from texture keys (the identifiers referenced in the model)
      to on-disk PNG paths.
    - output_dir: Directory inside the Bedrock resource pack where the atlas PNG should
      be written.
    - atlas_name: Friendly name (typically the model hash) used for both the PNG file
      name and the resource identifier (`gmdl_atlas_<name>`).

    Returns:
    - Tuple of (atlas_key, frames, atlas_path, atlas_size):
        * atlas_key: string such as `gmdl_atlas_<atlas_name>` used in Bedrock JSON.
        * frames: mapping of texture key to frame metadata `{x, y, w, h}` in pixels.
        * atlas_path: absolute `Path` to the generated PNG file.
        * atlas_size: `(width, height)` in pixels.

    Raises:
    - RuntimeError if Pillow is not installed or if no textures were provided.
    """

    if not texture_files:
        raise RuntimeError("No textures supplied for atlas generation")

    try:
        from PIL import Image
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise RuntimeError("Pillow is required to generate atlases (pip install Pillow)") from exc

    output_dir.mkdir(parents=True, exist_ok=True)

    images: dict[str, Any] = {}
    max_width = 0
    total_height = 0
    for key, path in texture_files.items():
        img = Image.open(path).convert("RGBA")
        images[key] = img
        max_width = max(max_width, img.width)
        total_height += img.height

    atlas_image = Image.new("RGBA", (max_width, total_height), (0, 0, 0, 0))
    frames: dict[str, dict[str, float]] = {}
    cursor_y = 0
    for key, img in images.items():
        atlas_image.paste(img, (0, cursor_y))
        frames[key] = {"x": 0, "y": cursor_y, "w": img.width, "h": img.height}
        cursor_y += img.height

    atlas_path = output_dir / f"{atlas_name}.png"
    atlas_image.save(atlas_path)

    atlas_key = f"gmdl_atlas_{atlas_name}"
    return atlas_key, frames, atlas_path, atlas_image.size


def convert_model(
    entry: Mapping[str, Any],
    resolved_model: Mapping[str, Any],
    rp_root: Path,
    bp_root: Path,
    textures_root: Path,
    materials: Mapping[str, str],
) -> dict[str, Path]:
    """
    Convert a resolved Java model entry into Bedrock geometry, behavior, and attachable
    assets.

    Args:
    - entry: Single config row (typically derived from `config.json`) containing fields
      like `path_hash`, `namespace`, `model_path`, `model_name`, `generated`, etc.
    - resolved_model: Output of `resolve_parental` for the same entry.
    - rp_root / bp_root: Root directories for the Bedrock resource and behavior packs.
    - textures_root: Destination directory for the generated atlas PNGs.
    - materials: Dict with keys `attachable_material` and `block_material` describing the
      Bedrock materials to use.

    Returns:
    - Mapping summarizing the files written.

    Raises:
    - ValueError if required entry metadata is missing or inconsistent.
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
        # 2D sprite path: copy the first available texture and hook it up as an item icon.
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

    textures = resolved_model["texture_paths"]
    atlas_key, frames, atlas_path, atlas_size = generate_atlas(textures, textures_dir, path_hash)
    files_written["atlas"] = atlas_path

    geometry_identifier = f"geometry.geyser_custom.{geometry_id}"
    geometry = _build_geometry(resolved_model["elements"], frames, atlas_size, geometry_identifier)
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


def consolidate_files(base_dir: Path) -> None:
    """
    Flatten nested directories under `base_dir`, ensuring each file ends up directly under
    `base_dir`. Collisions are resolved by appending incremental suffixes before moving.
    """

    base_dir = Path(base_dir)
    base_dir.mkdir(parents=True, exist_ok=True)

    for file_path in sorted(base_dir.rglob("*")):
        if not file_path.is_file() or file_path.parent == base_dir:
            continue
        target_name = file_path.name
        counter = 1
        while (base_dir / target_name).exists():
            stem, suffix = os.path.splitext(file_path.name)
            target_name = f"{stem}_{counter}{suffix}"
            counter += 1
        shutil.move(str(file_path), base_dir / target_name)

    # Remove now-empty directories, deepest first.
    for directory in sorted(base_dir.rglob("*"), reverse=True):
        if directory.is_dir():
            try:
                directory.rmdir()
            except OSError:
                continue


def write_geyser_mappings(entries: Iterable[Mapping[str, Any]], output_path: Path) -> None:
    """
    Emit `geyser_mappings.json` compatible with Geyser's custom item definitions.

    Args:
    - entries: Iterable of config dictionaries (matching the per-model structure) that
      contain at minimum `item`, `path_hash`, `generated`, `bedrock_icon`, and `nbt`.
    - output_path: Destination JSON file (typically `target/geyser_mappings.json`).
    """

    mappings: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for entry in entries:
        item_id = entry.get("item")
        if item_id is None:
            continue
        java_id = item_id if ":" in item_id else f"minecraft:{item_id}"
        bedrock_name = f"minecraft:{java_id.split(':')[-1]}"
        payload: dict[str, Any] = {
            "name": entry["path_hash"],
            "allow_offhand": True,
        }

        icon_info = entry.get("bedrock_icon", {})
        if entry.get("generated"):
            payload["icon"] = entry["path_hash"]
        else:
            payload["icon"] = icon_info.get("icon", "camera")
            if "frame" in icon_info:
                payload["frame"] = icon_info["frame"]

        nbt = entry.get("nbt", {}) or {}
        if "CustomModelData" in nbt:
            payload["custom_model_data"] = nbt["CustomModelData"]
        if "Damage" in nbt:
            payload["damage_predicate"] = nbt["Damage"]
        if "Unbreakable" in nbt:
            payload["unbreakable"] = nbt["Unbreakable"]

        mappings[bedrock_name].append(payload)

    geyser_json = {
        "format_version": "1",
        "items": mappings,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(geyser_json, indent=2), encoding="utf-8")


def _parent_to_model_path(parent: str, assets_root: Path) -> Path:
    namespace, path = _split_namespace(parent, default_namespace="minecraft")
    return assets_root / "assets" / namespace / "models" / f"{path}.json"


def _split_namespace(resource: str, default_namespace: str = "minecraft") -> tuple[str, str]:
    if ":" in resource:
        namespace, rest = resource.split(":", 1)
    else:
        namespace, rest = default_namespace, resource
    return namespace, rest.strip("/")


def _resolve_texture_files(textures: Mapping[str, str], assets_root: Path) -> dict[str, Path]:
    resolved: dict[str, Path] = {}
    for key, value in textures.items():
        texture_id = _resolve_texture_value(value, textures)
        namespace, rel = _split_namespace(texture_id)
        path = assets_root / "assets" / namespace / "textures" / f"{rel}.png"
        resolved[key] = path
    return resolved


def _resolve_texture_value(value: str, textures: Mapping[str, str], depth: int = 0) -> str:
    if depth > 10:
        raise ValueError("Exceeded texture indirection depth")
    if value.startswith("#"):
        key = value[1:]
        target = textures.get(key)
        if target is None:
            raise ValueError(f"Texture reference {value} could not be resolved")
        return _resolve_texture_value(target, textures, depth + 1)
    return value


def _round(value: float) -> float:
    return round(value + 0.0, 4)


def _build_geometry(
    elements: list[Mapping[str, Any]] | None,
    frames: Mapping[str, Mapping[str, float]],
    atlas_size: tuple[int, int],
    geometry_identifier: str,
) -> dict[str, Any]:
    if not elements:
        raise ValueError("Cannot build geometry without elements")

    cubes: list[dict[str, Any]] = []
    atlas_width, atlas_height = atlas_size

    for element in elements:
        from_vec = element.get("from", [0, 0, 0])
        to_vec = element.get("to", [0, 0, 0])
        cube: dict[str, Any] = {
            "origin": [_round(-to_vec[0] + 8), _round(from_vec[1]), _round(from_vec[2] - 8)],
            "size": [
                _round(to_vec[0] - from_vec[0]),
                _round(to_vec[1] - from_vec[1]),
                _round(to_vec[2] - from_vec[2]),
            ],
        }

        if rotation := element.get("rotation"):
            cube["pivot"] = [
                _round(-rotation.get("origin", [0, 0, 0])[0] + 8),
                _round(rotation.get("origin", [0, 0, 0])[1]),
                _round(rotation.get("origin", [0, 0, 0])[2] - 8),
            ]
            angle = rotation.get("angle", 0)
            axis = rotation.get("axis")
            if axis == "x":
                cube["rotation"] = [_round(-angle), 0, 0]
            elif axis == "y":
                cube["rotation"] = [0, _round(-angle), 0]
            elif axis == "z":
                cube["rotation"] = [0, 0, _round(angle)]

        faces_payload: dict[str, Any] = {}
        for face_name, face in (element.get("faces") or {}).items():
            texture_ref = face.get("texture")
            if not texture_ref:
                continue
            texture_key = texture_ref[1:] if texture_ref.startswith("#") else texture_ref
            frame = frames.get(texture_key)
            if not frame:
                continue
            uv = face.get("uv")
            if uv:
                scale_x = frame["w"] / 16
                scale_y = frame["h"] / 16
                u0 = frame["x"] + uv[0] * scale_x
                v0 = frame["y"] + uv[1] * scale_y
                u1 = frame["x"] + uv[2] * scale_x
                v1 = frame["y"] + uv[3] * scale_y
            else:
                u0, v0 = frame["x"], frame["y"]
                u1, v1 = frame["x"] + frame["w"], frame["y"] + frame["h"]

            faces_payload[face_name] = {
                "uv": [_round(u0), _round(v0)],
                "uv_size": [_round(u1 - u0), _round(v1 - v0)],
            }

        if faces_payload:
            cube["uv"] = faces_payload
        cubes.append(cube)

    geometry = {
        "format_version": "1.16.0",
        "minecraft:geometry": [
            {
                "description": {
                    "identifier": geometry_identifier,
                    "texture_width": max(1, atlas_width),
                    "texture_height": max(1, atlas_height),
                    "visible_bounds_width": 4,
                    "visible_bounds_height": 4.5,
                    "visible_bounds_offset": [0, 0.75, 0],
                },
                "bones": [
                    {
                        "name": "geyser_custom",
                        "binding": "q.item_slot_to_bone_name(c.item_slot)",
                        "pivot": [0, 8, 0],
                        "cubes": cubes,
                    }
                ],
            }
        ],
    }

    return geometry

def add_to_terrain_mappings():
    pass

