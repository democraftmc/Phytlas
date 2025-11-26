"""Texture atlas generation utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Mapping, Any


def generate_atlas(
    texture_files: Mapping[str, Path],
    output_dir: Path,
    atlas_name: str,
) -> tuple[str, dict[str, dict[str, float]], Path, tuple[int, int]]:
    """
    Generate a single PNG atlas for all textures required by one model.

    The atlas is built as a simple vertical strip (one texture per row). 
    This keeps the packing logic deterministic without requiring external CLI tools.

    Args:
        texture_files: Mapping from texture keys (model identifiers) to PNG file paths.
        output_dir: Directory inside the Bedrock resource pack where the atlas PNG 
                    should be written.
        atlas_name: Friendly name (typically the model hash) used for both the PNG 
                    file name and the resource identifier.

    Returns:
        Tuple of (atlas_key, frames, atlas_path, atlas_size):
        - atlas_key: String like `gmdl_atlas_<atlas_name>` used in Bedrock JSON.
        - frames: Mapping of texture key to frame metadata `{x, y, w, h}` in pixels.
        - atlas_path: Absolute Path to the generated PNG file.
        - atlas_size: (width, height) tuple in pixels.

    Raises:
        RuntimeError: If Pillow is not installed or if no textures were provided.
    """
    if not texture_files:
        raise RuntimeError("No textures supplied for atlas generation")

    try:
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError(
            "Pillow is required to generate atlases (pip install Pillow)"
        ) from exc

    output_dir.mkdir(parents=True, exist_ok=True)

    # Deduplicate textures that point to the same PNG file so a single
    # 16x16 source texture does not get stacked multiple times (which would
    # incorrectly produce 16x32, 16x48, ... atlases).
    unique_entries: list[dict[str, Any]] = []
    image_cache: dict[Path, dict[str, Any]] = {}

    for key, path in texture_files.items():
        canonical_path = Path(path).resolve()
        cached = image_cache.get(canonical_path)
        if cached is None:
            img = Image.open(canonical_path).convert("RGBA")
            cached = {"image": img, "keys": []}
            image_cache[canonical_path] = cached
            unique_entries.append(cached)
        cached["keys"].append(key)

    max_width = 0
    total_height = 0
    for entry in unique_entries:
        img = entry["image"]
        max_width = max(max_width, img.width)
        total_height += img.height

    atlas_image = Image.new("RGBA", (max_width, total_height), (0, 0, 0, 0))
    frames: dict[str, dict[str, float]] = {}
    cursor_y = 0

    for entry in unique_entries:
        img = entry["image"]
        atlas_image.paste(img, (0, cursor_y))
        frame = {"x": 0, "y": cursor_y, "w": img.width, "h": img.height}
        for key in entry["keys"]:
            frames[key] = frame.copy()
        cursor_y += img.height
        img.close()

    atlas_path = output_dir / f"{atlas_name}.png"
    atlas_image.save(atlas_path)

    atlas_key = f"gmdl_atlas_{atlas_name}"
    return atlas_key, frames, atlas_path, atlas_image.size
