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
