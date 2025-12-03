"""Texture resolution and utility functions."""

from __future__ import annotations

from pathlib import Path
from typing import Mapping


def resolve_texture_files(
    textures: Mapping[str, str], 
    assets_root: Path
) -> dict[str, Path]:
    """
    Resolve texture keys to actual file paths on disk.

    Args:
        textures: Mapping of texture keys to texture identifiers.
        assets_root: Root directory containing the assets folder.

    Returns:
        Dictionary mapping texture keys to their resolved file Paths.
    """
    resolved: dict[str, Path] = {}
    for key, value in textures.items():
        texture_id = resolve_texture_value(value, textures)
        namespace, rel = split_namespace(texture_id)
        path = assets_root / "assets" / namespace / "textures" / f"{rel}.png"
        resolved[key] = path
    return resolved


def resolve_texture_value(
    value: str, 
    textures: Mapping[str, str], 
    depth: int = 0
) -> str:
    """
    Recursively resolve texture reference indirection.

    Handles texture references that start with '#' which reference other texture keys.

    Args:
        value: Texture value or reference to resolve.
        textures: Full texture mapping for reference lookup.
        depth: Current recursion depth (prevents infinite loops).

    Returns:
        Fully resolved texture identifier.

    Raises:
        ValueError: If recursion depth exceeds limit or reference cannot be resolved.
    """
    if depth > 10:
        raise ValueError("Exceeded texture indirection depth")
    
    if value.startswith("#"):
        key = value[1:]
        target = textures.get(key)
        if target is None:
            raise ValueError(f"Texture reference {value} could not be resolved")
        return resolve_texture_value(target, textures, depth + 1)
    
    return value

def ensure_placeholder_texture(target: Path) -> None:
    """
    Create the built-in 16x16 texture (taken from the provided image) if it doesn't exist.
    No external image file is required: pixels are embedded directly.
    """
    if target.exists():
        return

    target.parent.mkdir(parents=True, exist_ok=True)

    try:
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError("Pillow is required to write placeholder textures") from exc

    # === Embedded RGBA pixels extracted from DMEOCRAFT's Pixel Art Background ===
    pixels = [
        (182,157,101,255),(182,157,101,255),(205,184,125,255),(195,172,114,255),(205,184,125,255),(186,168,116,255),(186,168,116,255),(186,168,116,255),(159,107,88,255),(127,86,70,255),(159,107,88,255),(161,113,94,255),(161,113,94,255),(167,117,97,255),(167,117,97,255),(167,117,97,255),
        (182,157,101,255),(182,157,101,255),(195,172,114,255),(182,157,101,255),(186,168,116,255),(205,184,125,255),(186,168,116,255),(159,107,88,255),(127,86,70,255),(93,62,47,255),(127,86,70,255),(159,107,88,255),(161,113,94,255),(167,117,97,255),(161,113,94,255),(161,113,94,255),
        (205,184,125,255),(195,172,114,255),(205,184,125,255),(205,184,125,255),(195,172,114,255),(186,168,116,255),(159,107,88,255),(127,86,70,255),(93,62,47,255),(127,86,70,255),(159,107,88,255),(161,113,94,255),(159,107,88,255),(159,107,88,255),(159,107,88,255),(161,113,94,255),
        (205,184,125,255),(205,184,125,255),(195,172,114,255),(186,168,116,255),(195,172,114,255),(159,107,88,255),(127,86,70,255),(93,62,47,255),(127,86,70,255),(159,107,88,255),(186,168,116,255),(205,184,125,255),(205,184,125,255),(195,172,114,255),(159,107,88,255),(127,86,70,255),
        (195,172,114,255),(186,168,116,255),(186,168,116,255),(195,172,114,255),(159,107,88,255),(127,86,70,255),(93,62,47,255),(127,86,70,255),(159,107,88,255),(195,172,114,255),(205,184,125,255),(195,172,114,255),(186,168,116,255),(159,107,88,255),(127,86,70,255),(93,62,47,255),
        (186,168,116,255),(186,168,116,255),(159,107,88,255),(127,86,70,255),(127,86,70,255),(93,62,47,255),(127,86,70,255),(159,107,88,255),(195,172,114,255),(205,184,125,255),(195,172,114,255),(186,168,116,255),(159,107,88,255),(127,86,70,255),(93,62,47,255),(127,86,70,255),
        (186,168,116,255),(159,107,88,255),(127,86,70,255),(93,62,47,255),(127,86,70,255),(159,107,88,255),(182,157,101,255),(195,172,114,255),(205,184,125,255),(195,172,114,255),(186,168,116,255),(159,107,88,255),(127,86,70,255),(93,62,47,255),(127,86,70,255),(159,107,88,255),
        (159,107,88,255),(127,86,70,255),(93,62,47,255),(127,86,70,255),(159,107,88,255),(182,157,101,255),(195,172,114,255),(205,184,125,255),(195,172,114,255),(186,168,116,255),(159,107,88,255),(127,86,70,255),(93,62,47,255),(127,86,70,255),(159,107,88,255),(182,157,101,255),
        (159,107,88,255),(93,62,47,255),(127,86,70,255),(159,107,88,255),(182,157,101,255),(195,172,114,255),(205,184,125,255),(195,172,114,255),(186,168,116,255),(159,107,88,255),(127,86,70,255),(93,62,47,255),(127,86,70,255),(159,107,88,255),(182,157,101,255),(186,168,116,255),
        (127,86,70,255),(127,86,70,255),(159,107,88,255),(182,157,101,255),(195,172,114,255),(205,184,125,255),(195,172,114,255),(195,172,114,255),(159,107,88,255),(127,86,70,255),(93,62,47,255),(127,86,70,255),(159,107,88,255),(182,157,101,255),(186,168,116,255),(195,172,114,255),
        (127,86,70,255),(159,107,88,255),(186,168,116,255),(195,172,114,255),(205,184,125,255),(205,184,125,255),(186,168,116,255),(159,107,88,255),(127,86,70,255),(93,62,47,255),(127,86,70,255),(159,107,88,255),(182,157,101,255),(186,168,116,255),(195,172,114,255),(205,184,125,255),
        (159,107,88,255),(186,168,116,255),(195,172,114,255),(205,184,125,255),(205,184,125,255),(195,172,114,255),(159,107,88,255),(127,86,70,255),(93,62,47,255),(127,86,70,255),(159,107,88,255),(182,157,101,255),(186,168,116,255),(195,172,114,255),(205,184,125,255),(205,184,125,255),
        (186,168,116,255),(195,172,114,255),(205,184,125,255),(205,184,125,255),(195,172,114,255),(159,107,88,255),(127,86,70,255),(93,62,47,255),(127,86,70,255),(159,107,88,255),(182,157,101,255),(195,172,114,255),(205,184,125,255),(205,184,125,255),(205,184,125,255),(195,172,114,255),
        (195,172,114,255),(205,184,125,255),(205,184,125,255),(195,172,114,255),(159,107,88,255),(127,86,70,255),(93,62,47,255),(127,86,70,255),(159,107,88,255),(182,157,101,255),(195,172,114,255),(205,184,125,255),(205,184,125,255),(205,184,125,255),(195,172,114,255),(195,172,114,255),
        (205,184,125,255),(205,184,125,255),(195,172,114,255),(159,107,88,255),(127,86,70,255),(93,62,47,255),(127,86,70,255),(159,107,88,255),(182,157,101,255),(195,172,114,255),(205,184,125,255),(205,184,125,255),(205,184,125,255),(195,172,114,255),(195,172,114,255),(195,172,114,255)
    ]

    img = Image.new("RGBA", (16, 16))
    img.putdata(pixels)
    img.save(target)



def split_namespace(resource: str, default_namespace: str = "minecraft") -> tuple[str, str]:
    """
    Split a namespaced resource identifier into namespace and path.

    Args:
        resource: Resource identifier, optionally with namespace prefix (e.g., "minecraft:item").
        default_namespace: Namespace to use if none is specified.

    Returns:
        Tuple of (namespace, path).
    """
    if ":" in resource:
        namespace, rest = resource.split(":", 1)
    else:
        namespace, rest = default_namespace, resource
    return namespace, rest.strip("/")
