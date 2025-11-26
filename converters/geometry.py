"""Geometry building for Bedrock Edition models."""

from __future__ import annotations

from typing import Any, Mapping


def round_value(value: float) -> float:
    """
    Round a float value to 4 decimal places.

    Args:
        value: Value to round.

    Returns:
        Rounded value.
    """
    return round(value + 0.0, 4)


def build_geometry(
    elements: list[Mapping[str, Any]] | None,
    frames: Mapping[str, Mapping[str, float]],
    atlas_size: tuple[int, int],
    geometry_identifier: str,
) -> dict[str, Any]:
    """
    Build Bedrock geometry JSON from Java model elements.

    Converts Java Edition model cubes to Bedrock Edition format with proper
    UV mapping and transformations.

    Args:
        elements: List of Java model cube definitions.
        frames: Mapping of texture keys to frame data (x, y, w, h) in the atlas.
        atlas_size: Tuple of (width, height) of the texture atlas.
        geometry_identifier: Bedrock geometry identifier string.

    Returns:
        Complete Bedrock geometry JSON structure.

    Raises:
        ValueError: If no elements are provided.
    """
    if not elements:
        raise ValueError("Cannot build geometry without elements")

    cubes: list[dict[str, Any]] = []
    atlas_width, atlas_height = atlas_size

    for element in elements:
        from_vec = element.get("from", [0, 0, 0])
        to_vec = element.get("to", [0, 0, 0])
        
        cube: dict[str, Any] = {
            "origin": [
                round_value(-to_vec[0] + 8), 
                round_value(from_vec[1]), 
                round_value(from_vec[2] - 8)
            ],
            "size": [
                round_value(to_vec[0] - from_vec[0]),
                round_value(to_vec[1] - from_vec[1]),
                round_value(to_vec[2] - from_vec[2]),
            ],
        }

        # Handle rotation if present
        if rotation := element.get("rotation"):
            cube["pivot"] = [
                round_value(-rotation.get("origin", [0, 0, 0])[0] + 8),
                round_value(rotation.get("origin", [0, 0, 0])[1]),
                round_value(rotation.get("origin", [0, 0, 0])[2] - 8),
            ]
            angle = rotation.get("angle", 0)
            axis = rotation.get("axis")
            
            if axis == "x":
                cube["rotation"] = [round_value(-angle), 0, 0]
            elif axis == "y":
                cube["rotation"] = [0, round_value(-angle), 0]
            elif axis == "z":
                cube["rotation"] = [0, 0, round_value(angle)]

        # Process faces
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
                "uv": [round_value(u0), round_value(v0)],
                "uv_size": [round_value(u1 - u0), round_value(v1 - v0)],
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
