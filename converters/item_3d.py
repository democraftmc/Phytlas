"""3D model item conversion from Java to Bedrock format.

This module handles items with actual 3D geometry (cubes/elements).
Changes here will NOT affect 2D sprite conversion.
"""

from __future__ import annotations

import json
import shutil
import math
from pathlib import Path
from typing import Any, Mapping
import subprocess

try:
    from PIL import Image
    import numpy as np
    
except ImportError:
    Image = None
    np = None

from services.texture_atlas import generate_atlas
from .geometry import build_geometry


def convert_3d_item(
    entry: Mapping[str, Any],
    resolved_model: Mapping[str, Any],
    rp_root: Path,
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

    attachable_material = materials.get("attachable_material", "entity_alphablend")

    # Setup directories
    rp_models_dir = rp_root / "models" / "blocks" / namespace / model_path
    rp_models_dir.mkdir(parents=True, exist_ok=True)

    rp_attachables_dir = rp_root / "attachables" / namespace / model_path
    rp_attachables_dir.mkdir(parents=True, exist_ok=True)

    # Generate texture atlas from model textures
    textures = resolved_model["texture_paths"]
    placeholder = list(textures.keys())[0]
    atlas_dir = textures_root / "models"
    atlas_key, frames, atlas_path, atlas_size = generate_atlas(
        textures, atlas_dir, path_hash
    )
    files_written["atlas"] = atlas_path

    # Handle Icon (2D sprite for inventory)
    icon_target = textures_root / "2d_renders" / f"{path_hash}.png"
    icon_generated = False

    if Image:
        try:
            print(namespace + ":" + model_name,)
            generate_cool_3d_render(namespace + ":" + model_name, str(icon_target))
            #generate_3d_render(resolved_model, textures, icon_target)
            if icon_target.exists():
                icon_texture_name = path_hash
                icon_generated = True
        except Exception as e:
            print(f"Warning: Failed to generate 3D render for {model_name}: {e}")

    if not icon_generated:
        if placeholder:
            # Copy icon texture to the root textures folder
            shutil.copy2(placeholder, icon_target)
            icon_texture_name = path_hash
        else:
            icon_texture_name = "camera"    

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

    attachable = create_3d_attachable_definition(
        identifier,
        attachable_material,
        f"models/{atlas_path.name}", 
        geometry_identifier,
    )
    short_name = model_name[:20] if len(model_name) > 20 else model_name
    attachable_file = rp_attachables_dir / f"{short_name}.{path_hash}.attachable.json"
    attachable_file.write_text(json.dumps(attachable, indent=2), encoding="utf-8")
    files_written["attachable"] = attachable_file
    animations_dir = rp_root / "animations" / namespace / model_path
    animations_dir.mkdir(parents=True, exist_ok=True)
    animations = generate_item_animations(geometry_id, resolved_model.get("display") or {})
    animation_file = animations_dir / f"animation.{model_name}.json"
    animation_file.write_text(json.dumps(animations, indent=2), encoding="utf-8")
    files_written["animation"] = animation_file
    return files_written

def generate_cool_3d_render(id, path):
    subprocess.run(["java", "-jar", "libs/BedrockAdderRenderer-1.3.6.jar", "render", "512", id, path], check=False)



def create_3d_item_definition(
    identifier: str,
    texture_key: str,
) -> dict[str, Any]:
    """
    Create Bedrock item definition JSON for a 3D model item.

    Args:
        identifier: Bedrock item identifier.
        texture_key: Texture key for the item icon.

    Returns:
        Item definition dictionary.
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
                    "texture": texture_key
                }
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
    geo_suffix = geometry_identifier.replace("geometry.geyser_custom.", "")
    return {
        "format_version": "1.10.0",
        "minecraft:attachable": {
            "description": {
                "identifier": identifier,
                "materials": {
                    "default": material,
                    "enchanted": "entity_alphatest_glint",
                },
                "textures": {
                    "default": f"textures/{atlas_filename}",
                    "enchanted": "textures/misc/enchanted_item_glint",
                },
                "geometry": {
                    "default": geometry_identifier
                },
                "scripts": {
                    "pre_animation": [
                        "v.main_hand = c.item_slot == 'main_hand';",
                        "v.off_hand = c.item_slot == 'off_hand';",
                        "v.head = c.item_slot == 'head';",
                    ],
                    "animate": [
                        {"thirdperson_main_hand": "v.main_hand && !c.is_first_person"},
                        {"thirdperson_off_hand": "v.off_hand && !c.is_first_person"},
                        {"thirdperson_head": "v.head && !c.is_first_person"},
                        {"firstperson_main_hand": "v.main_hand && c.is_first_person"},
                        {"firstperson_off_hand": "v.off_hand && c.is_first_person"},
                        {"firstperson_head": "c.is_first_person && v.head"},
                    ],
                },
                "animations": {
                    "thirdperson_main_hand": f"animation.geyser_custom.{geo_suffix}.thirdperson_main_hand",
                    "thirdperson_off_hand": f"animation.geyser_custom.{geo_suffix}.thirdperson_off_hand",
                    "thirdperson_head": f"animation.geyser_custom.{geo_suffix}.head",
                    "firstperson_main_hand": f"animation.geyser_custom.{geo_suffix}.firstperson_main_hand",
                    "firstperson_off_hand": f"animation.geyser_custom.{geo_suffix}.firstperson_off_hand",
                    "firstperson_head": "animation.geyser_custom.disable",
                },
                "render_controllers": ["controller.render.item_default"],
            },
        },
    }


def generate_item_animations(geometry_id: str, display: dict[str, Any]) -> dict[str, Any]:
    """
    Generate Bedrock animations based on Java display settings.
    Matches logic from converter.sh to ensure consistent positioning.
    
    Args:
        geometry_id: The geometry ID suffix.
        display: The 'display' section from the Java model.
        
    Returns:
        Animation definition dictionary.
    """
    anim_prefix = f"animation.geyser_custom.{geometry_id}"
    
    animations = {}

    # Helper to safely get values
    def get_val(data, key, default=None):
        return data.get(key, default)

    # 1. Third Person Main Hand (Right)
    # converter.sh: base rot=[90, 0, 0], pos=[0, 13, -3]
    # child pos=[-x, y, z], rot=[-x, -y, z]
    disp = display.get("thirdperson_righthand", {})
    j_rot = get_val(disp, "rotation", [0, 0, 0])
    j_pos = get_val(disp, "translation", [0, 0, 0])
    j_scale = get_val(disp, "scale", [1, 1, 1])

    animations[f"{anim_prefix}.thirdperson_main_hand"] = {
        "loop": True,
        "bones": {
            "geyser_custom": {
                "rotation": [90, 0, 0],
                "position": [0, 13, -3]
            },
            "geyser_custom_x": {
                "rotation": [-j_rot[0], 0, 0],
                "position": [-j_pos[0], j_pos[1], j_pos[2]],
                "scale": j_scale
            },
            "geyser_custom_y": {
                "rotation": [0, -j_rot[1], 0]
            },
            "geyser_custom_z": {
                "rotation": [0, 0, j_rot[2]]
            }
        }
    }

    # 2. Third Person Off Hand (Left)
    # converter.sh: base rot=[90, 0, 0], pos=[0, 13, -3]
    # child pos=[x, y, z], rot=[-x, -y, z]
    disp = display.get("thirdperson_lefthand", {})
    j_rot = get_val(disp, "rotation", [0, 0, 0])
    j_pos = get_val(disp, "translation", [0, 0, 0])
    j_scale = get_val(disp, "scale", [1, 1, 1])

    animations[f"{anim_prefix}.thirdperson_off_hand"] = {
        "loop": True,
        "bones": {
            "geyser_custom": {
                "rotation": [90, 0, 0],
                "position": [0, 13, -3]
            },
            "geyser_custom_x": {
                "rotation": [-j_rot[0], 0, 0],
                "position": [j_pos[0], j_pos[1], j_pos[2]],
                "scale": j_scale
            },
            "geyser_custom_y": {
                "rotation": [0, -j_rot[1], 0]
            },
            "geyser_custom_z": {
                "rotation": [0, 0, j_rot[2]]
            }
        }
    }

    # 3. Head
    # converter.sh: base pos=[0, 19.9, 0]
    # child pos=[-x*0.625, y*0.625, z*0.625], rot=[-x, -y, z]
    # child scale = scale * 0.625 (or 0.625 if no scale)
    disp = display.get("head", {})
    j_rot = get_val(disp, "rotation", [0, 0, 0])
    j_pos = get_val(disp, "translation", [0, 0, 0])
    raw_scale = get_val(disp, "scale", [1, 1, 1])

    # If scale was missing in Java, converter.sh uses 0.625. 
    # If present, it multiplies by 0.625.
    # We can simulate this by checking if "scale" key exists, but here we have defaults.
    # Let's assume if it's [1,1,1] it might be default, but Java JSON might omit it.
    # Ideally we check if key exists.
    if "scale" in disp:
        j_scale = [s * 0.625 for s in raw_scale]
    else:
        j_scale = [0.625, 0.625, 0.625]

    animations[f"{anim_prefix}.head"] = {
        "loop": True,
        "bones": {
            "geyser_custom": {
                "position": [0, 19.9, 0]
            },
            "geyser_custom_x": {
                "rotation": [-j_rot[0], 0, 0],
                "position": [-j_pos[0] * 0.625, j_pos[1] * 0.625, j_pos[2] * 0.625],
                "scale": j_scale
            },
            "geyser_custom_y": {
                "rotation": [0, -j_rot[1], 0]
            },
            "geyser_custom_z": {
                "rotation": [0, 0, j_rot[2]]
            }
        }
    }

    # 4. First Person Main Hand (Right)
    # converter.sh: base rot=[90, 60, -40], pos=[4, 10, 4], scale=1.5
    # child pos=[-x, y, -z], rot=[-x, -y, z] (default rot [0.1, 0.1, 0.1] if missing)
    disp = display.get("firstperson_righthand", {})
    # converter.sh default rotation is [0.1, 0.1, 0.1] if missing.
    if "rotation" in disp:
        j_rot = disp["rotation"]
        rot_x = [-j_rot[0], 0, 0]
    else:
        # converter.sh uses [0.1, 0.1, 0.1] if rotation is null.
        # But wait, it puts it in 'rotation' field of geyser_custom_x.
        # If rotation is null, it sets rotation to [0.1, 0.1, 0.1].
        # This seems to be a specific hack.
        rot_x = [0.1, 0.1, 0.1]
        j_rot = [0, 0, 0] # For y and z components if they are used?
        # converter.sh: geyser_custom_y rotation is null if rotation is null.
        # So only X gets the 0.1s? No, the array is [0.1, 0.1, 0.1].
    
    j_pos = get_val(disp, "translation", [0, 0, 0])
    j_scale = get_val(disp, "scale", [1, 1, 1])

    # Construct bones for FP Right
    bones_fp_right = {
        "geyser_custom": {
            "rotation": [90, 60, -40],
            "position": [4, 10, 4],
            "scale": 1.5
        },
        "geyser_custom_x": {
            "rotation": rot_x,
            "position": [-j_pos[0], j_pos[1], -j_pos[2]],
            "scale": j_scale
        }
    }
    if "rotation" in disp:
        bones_fp_right["geyser_custom_y"] = {"rotation": [0, -j_rot[1], 0]}
        bones_fp_right["geyser_custom_z"] = {"rotation": [0, 0, j_rot[2]]}

    animations[f"{anim_prefix}.firstperson_main_hand"] = {
        "loop": True,
        "bones": bones_fp_right
    }

    # 5. First Person Off Hand (Left)
    # converter.sh: base rot=[90, 60, -40], pos=[4, 10, 4], scale=1.5
    # child pos=[x, y, -z], rot=[-x, -y, z]
    disp = display.get("firstperson_lefthand", {})
    if "rotation" in disp:
        j_rot = disp["rotation"]
        rot_x = [-j_rot[0], 0, 0]
    else:
        rot_x = [0.1, 0.1, 0.1]
        j_rot = [0, 0, 0]

    j_pos = get_val(disp, "translation", [0, 0, 0])
    j_scale = get_val(disp, "scale", [1, 1, 1])

    bones_fp_left = {
        "geyser_custom": {
            "rotation": [90, 60, -40],
            "position": [4, 10, 4],
            "scale": 1.5
        },
        "geyser_custom_x": {
            "rotation": rot_x,
            "position": [j_pos[0], j_pos[1], -j_pos[2]],
            "scale": j_scale
        }
    }
    if "rotation" in disp:
        bones_fp_left["geyser_custom_y"] = {"rotation": [0, -j_rot[1], 0]}
        bones_fp_left["geyser_custom_z"] = {"rotation": [0, 0, j_rot[2]]}

    animations[f"{anim_prefix}.firstperson_off_hand"] = {
        "loop": True,
        "bones": bones_fp_left
    }

    return {
        "format_version": "1.8.0",
        "animations": animations
    }