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

    attachable_material = materials.get("attachable_material", "entity_alphatest_one_sided")

    # Setup directories
    rp_models_dir = rp_root / "models" / "blocks" / namespace / model_path
    rp_models_dir.mkdir(parents=True, exist_ok=True)

    rp_attachables_dir = rp_root / "attachables" / namespace / model_path
    rp_attachables_dir.mkdir(parents=True, exist_ok=True)

    # Generate texture atlas from model textures
    textures = resolved_model["texture_paths"]
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
            generate_3d_render(resolved_model, textures, icon_target)
            if icon_target.exists():
                icon_texture_name = path_hash
                icon_generated = True
        except Exception as e:
            print(f"Warning: Failed to generate 3D render for {model_name}: {e}")

    if not icon_generated:
        icon_texture_path = textures.get("layer0")
        if not icon_texture_path and textures:
            icon_texture_path = list(textures.values())[0]
        
        if icon_texture_path:
            # Copy icon texture to the root textures folder
            shutil.copy2(icon_texture_path, icon_target)
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


def generate_3d_render(
    model: Mapping[str, Any],
    texture_paths: Mapping[str, Path],
    output_path: Path,
) -> None:
    """
    Generate a 3D render of the model using a simple ray-tracer with numpy.
    Matches the logic of the provided JS example (Orthographic, Display transforms).
    """
    if not np or not Image:
        print("Warning: numpy or PIL not installed, skipping 3D render.")
        return

    # 1. Load Textures
    textures = {}
    for key, path in texture_paths.items():
        if path.exists():
            try:
                img = Image.open(path).convert("RGBA")
                textures[key] = np.array(img)
                # Handle aliases like #0 -> 0
                textures[f"#{key}"] = textures[key]
            except Exception:
                pass
    
    if not textures:
        return

    # 2. Parse Elements & Build Scene
    elements = model.get("elements", [])
    if not elements:
        return

    scene_objects = []
    all_corners = []
    
    # Helper: Matrix factories
    def make_rotation_matrix(rx, ry, rz):
        # Euler XYZ in degrees
        rx, ry, rz = np.radians(rx), np.radians(ry), np.radians(rz)
        cx, sx = np.cos(rx), np.sin(rx)
        cy, sy = np.cos(ry), np.sin(ry)
        cz, sz = np.cos(rz), np.sin(rz)
        
        Rx = np.array([[1, 0, 0, 0], [0, cx, -sx, 0], [0, sx, cx, 0], [0, 0, 0, 1]])
        Ry = np.array([[cy, 0, sy, 0], [0, 1, 0, 0], [-sy, 0, cy, 0], [0, 0, 0, 1]])
        Rz = np.array([[cz, -sz, 0, 0], [sz, cz, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])
        return Rz @ Ry @ Rx

    def make_translation_matrix(tx, ty, tz):
        T = np.eye(4)
        T[:3, 3] = [tx, ty, tz]
        return T

    def make_scale_matrix(sx, sy, sz):
        S = np.eye(4)
        S[0,0], S[1,1], S[2,2] = sx, sy, sz
        return S

    # Global Display Transform (gui)
    display_root = model.get("display") or {}
    display = display_root.get("gui") or display_root.get("GUI") or {}

    d_rot = display.get("rotation", [0, 0, 0])
    d_pos = display.get("translation", [0, 0, 0])
    d_scale = display.get("scale", [1, 1, 1])
    
    M_display = make_translation_matrix(*d_pos) @ \
                make_rotation_matrix(*d_rot) @ \
                make_scale_matrix(*d_scale)

    for el in elements:
        f = np.array(el["from"])
        t = np.array(el["to"])
        center = (f + t) / 2
        dims = t - f
        
        # World center (centering 0..16 to -8..8)
        cx, cy, cz = center - 8
        
        # Pivot
        rot = el.get("rotation") or {}
        origin = np.array(rot.get("origin", [8, 8, 8]))
        axis = rot.get("axis", "y")
        angle = rot.get("angle", 0)
        
        px, py, pz = origin - 8
        
        # M = T(px,py,pz) * R * T(cx-px, cy-py, cz-pz)
        M_pivot_trans = make_translation_matrix(px, py, pz)
        
        if axis == "x": R = make_rotation_matrix(angle, 0, 0)
        elif axis == "y": R = make_rotation_matrix(0, angle, 0)
        else: R = make_rotation_matrix(0, 0, angle)
        
        M_offset = make_translation_matrix(cx-px, cy-py, cz-pz)
        M_local = M_pivot_trans @ R @ M_offset
        
        # Apply Global
        M_final = M_display @ M_local
        M_inv = np.linalg.inv(M_final)
        
        scene_objects.append({
            "M_inv": M_inv,
            "M_final": M_final,
            "dims": dims,
            "faces": el.get("faces") or {}
        })

        # Collect corners for auto-fit
        dx, dy, dz = dims / 2
        corners_local = np.array([
            [-dx, -dy, -dz], [dx, -dy, -dz], [dx, dy, -dz], [-dx, dy, -dz],
            [-dx, -dy, dz], [dx, -dy, dz], [dx, dy, dz], [-dx, dy, dz]
        ])
        corners_h = np.concatenate([corners_local, np.ones((8, 1))], axis=1)
        corners_world = (M_final @ corners_h.T).T[:, :3]
        all_corners.append(corners_world)

    # 3. Auto-fit Camera
    if all_corners:
        all_points = np.concatenate(all_corners, axis=0)
        min_pt = np.min(all_points, axis=0)
        max_pt = np.max(all_points, axis=0)
        
        # Bounding box in XY plane (Camera looks down Z)
        # Note: We will flip Y axis later, but for size calculation it doesn't matter
        width = max_pt[0] - min_pt[0]
        height = max_pt[1] - min_pt[1]
        
        center_x = (min_pt[0] + max_pt[0]) / 2
        center_y = (min_pt[1] + max_pt[1]) / 2
        
        # Add small margin (5%)
        frustum_size = max(width, height) * 1.05
        if frustum_size < 1.0: frustum_size = 16.0 # Fallback
    else:
        frustum_size = 16.0
        center_x, center_y = 0, 0

    RENDER_SIZE = 64
    
    # 4. Ray Tracing Setup
    # Grid
    xs = np.linspace(center_x - frustum_size/2, center_x + frustum_size/2, RENDER_SIZE)
    ys = np.linspace(center_y + frustum_size/2, center_y - frustum_size/2, RENDER_SIZE)
    
    xv, yv = np.meshgrid(xs, ys)
    
    # Ray Origins (World): [x, y, 48]
    ray_origins = np.stack([xv, yv, np.full_like(xv, 48)], axis=-1)
    ray_dir = np.array([0, 0, -1])
    
    # Buffers
    depth_buffer = np.full((RENDER_SIZE, RENDER_SIZE), np.inf)
    color_buffer = np.zeros((RENDER_SIZE, RENDER_SIZE, 4), dtype=np.uint8)
    
    light_dir = np.array([0.6, 1.0, 0.8])
    light_dir /= np.linalg.norm(light_dir)
    
    face_names = ["east", "west", "up", "down", "south", "north"]
    normals = [
        np.array([1,0,0]), np.array([-1,0,0]),
        np.array([0,1,0]), np.array([0,-1,0]),
        np.array([0,0,1]), np.array([0,0,-1])
    ]

    # 5. Render Loop
    for obj in scene_objects:
        dims = obj["dims"]
        half_dims = dims / 2
        M_inv = obj["M_inv"]
        M_final = obj["M_final"]
        
        # Transform Rays to Local
        ro_h = np.concatenate([ray_origins, np.ones((*ray_origins.shape[:2], 1))], axis=-1)
        ro_local = (M_inv @ ro_h.reshape(-1, 4).T).T.reshape(RENDER_SIZE, RENDER_SIZE, 4)[..., :3]
        
        rd_h = np.append(ray_dir, 0)
        rd_local = (M_inv @ rd_h)[:3]
        
        # Intersection
        with np.errstate(divide='ignore'):
            inv_rd = 1.0 / rd_local
        
        t1 = (-half_dims - ro_local) * inv_rd
        t2 = (half_dims - ro_local) * inv_rd
        
        tmin = np.minimum(t1, t2)
        tmax = np.maximum(t1, t2)
        
        t_enter = np.max(tmin, axis=-1)
        t_exit = np.min(tmax, axis=-1)
        
        hit_mask = (t_exit >= t_enter) & (t_exit > 0)
        
        if not np.any(hit_mask):
            continue
            
        # Hit Points (Local)
        t_hit = t_enter[hit_mask]
        p_hits_local = ro_local[hit_mask] + rd_local * t_hit[..., np.newaxis]
        
        # Depth Test (World Z)
        p_hits_h = np.concatenate([p_hits_local, np.ones((len(p_hits_local), 1))], axis=-1)
        p_hits_world = (M_final @ p_hits_h.T).T[..., :3]
        depths = 48 - p_hits_world[..., 2]
        
        # Update Mask
        current_depths = depth_buffer[hit_mask]
        update_mask = depths < current_depths
        
        if not np.any(update_mask):
            continue
            
        # Filter hits that passed depth test
        final_hits_local = p_hits_local[update_mask]
        final_depths = depths[update_mask]
        
        # Update Depth Buffer
        hit_indices = np.where(hit_mask)
        rows = hit_indices[0][update_mask]
        cols = hit_indices[1][update_mask]
        depth_buffer[rows, cols] = final_depths
        
        # Determine Face
        d_east = np.abs(final_hits_local[..., 0] - half_dims[0])
        d_west = np.abs(final_hits_local[..., 0] + half_dims[0])
        d_up = np.abs(final_hits_local[..., 1] - half_dims[1])
        d_down = np.abs(final_hits_local[..., 1] + half_dims[1])
        d_south = np.abs(final_hits_local[..., 2] - half_dims[2])
        d_north = np.abs(final_hits_local[..., 2] + half_dims[2])
        
        dists = np.stack([d_east, d_west, d_up, d_down, d_south, d_north], axis=-1)
        face_idx = np.argmin(dists, axis=-1)
        
        # Shading & Texturing
        for f_i, f_name in enumerate(face_names):
            f_mask = (face_idx == f_i)
            if not np.any(f_mask):
                continue
                
            face_data = obj["faces"].get(f_name)
            if not face_data:
                continue
                
            tex_key = face_data.get("texture", "")
            if tex_key.startswith("#"): tex_key = tex_key[1:]
            texture = textures.get(tex_key)
            if texture is None:
                continue
                
            # UV Mapping
            uvs = face_data.get("uv", [0, 0, 16, 16])
            pts = final_hits_local[f_mask]
            w, h, d = dims
            x, y, z = pts[:, 0], pts[:, 1], pts[:, 2]
            
            # Simple planar mapping
            if f_name == "north":   u, v = (half_dims[0] - x)/w, (half_dims[1] - y)/h
            elif f_name == "south": u, v = (x + half_dims[0])/w, (half_dims[1] - y)/h
            elif f_name == "east":  u, v = (half_dims[2] - z)/d, (half_dims[1] - y)/h
            elif f_name == "west":  u, v = (z + half_dims[2])/d, (half_dims[1] - y)/h
            elif f_name == "up":    u, v = (x + half_dims[0])/w, (half_dims[2] - z)/d
            elif f_name == "down":  u, v = (x + half_dims[0])/w, (z + half_dims[2])/d
            
            u_tex = uvs[0] + (uvs[2] - uvs[0]) * u
            v_tex = uvs[1] + (uvs[3] - uvs[1]) * v
            
            th, tw = texture.shape[:2]
            tx = np.clip((u_tex/16.0 * tw).astype(int), 0, tw-1)
            ty = np.clip((v_tex/16.0 * th).astype(int), 0, th-1)
            
            colors = texture[ty, tx]
            
            # Lighting
            M_rot = M_final[:3, :3]
            n_world = M_rot @ normals[f_i]
            n_world /= np.linalg.norm(n_world)
            diffuse = max(0.0, np.dot(n_world, light_dir))
            intensity = min(1.0, 0.4 + diffuse * 0.6)
            
            colors[:, :3] = (colors[:, :3] * intensity).astype(np.uint8)
            
            # Write
            f_rows = rows[f_mask]
            f_cols = cols[f_mask]
            
            # Alpha test
            alpha = colors[:, 3]
            visible = alpha > 10
            
            color_buffer[f_rows[visible], f_cols[visible]] = colors[visible]

    img = Image.fromarray(color_buffer, "RGBA")
    img.save(output_path)