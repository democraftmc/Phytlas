"""Parent model resolution for Java Edition models."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, MutableMapping, Optional, Set

from services.texture_utils import resolve_texture_files, split_namespace


def resolve_parental(
    model_path: Path,
    assets_root: Optional[Path] = None,
) -> dict[str, Any]:
    """
    Resolve a Java model's inheritance chain until concrete geometry and textures exist.

    Walks up the parent chain, merging textures, elements, and display settings.

    Args:
        model_path: Absolute path to the JSON model definition inside the extracted Java pack.
        assets_root: Optional override pointing to the root folder that contains the `assets/`
                     directory. Defaults to `model_path.parents[3]`, which matches the Java 
                     pack layout (`<pack>/assets/<namespace>/models/...`).

    Returns:
        Dictionary containing:
        - elements: List of resolved cubes (or None for generated/builtin models).
        - textures: Merged texture dictionary with child overriding parents.
        - display: Resolved display settings, if any.
        - generated: Bool indicating whether model comes from `builtin/generated`.
        - parent_chain: List of model files that were inspected, deepest parent last.
        - texture_paths: Mapping of texture keys to their on-disk PNG Path objects.

    Raises:
        FileNotFoundError: If a referenced parent cannot be located on disk.
        ValueError: If a parental loop is detected or no geometry/textures could be resolved.
    """
    assets_root = assets_root or model_path.parents[3]
    current = Path(model_path)
    visited: Set[Path] = set()
    parent_chain: list[str] = []
    resolved_elements: Optional[list[Any]] = None
    resolved_display: Optional[dict[str, Any]] = None
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
            # Child definitions override parents, so only fill missing keys
            for key, value in model["textures"].items():
                resolved_textures.setdefault(key, value)
        
        if resolved_display is None and "display" in model:
            resolved_display = model["display"]

        parent = model.get("parent")
        if (resolved_elements is not None) or parent is None:
            generated_model = parent in {"builtin/generated", "minecraft:builtin/generated"}
            break

        parent_path = parent_to_model_path(parent, assets_root)
        if not parent_path.exists():
            raise FileNotFoundError(f"Missing parent model {parent} for {model_path}")
        
        current = parent_path

    if resolved_elements is None and not generated_model:
        raise ValueError(f"Model {model_path} has no geometry even after resolving parents")

    texture_paths = resolve_texture_files(resolved_textures, assets_root)

    return {
        "elements": resolved_elements,
        "textures": resolved_textures,
        "display": resolved_display,
        "generated": generated_model,
        "parent_chain": parent_chain,
        "texture_paths": texture_paths,
    }


def parent_to_model_path(parent: str, assets_root: Path) -> Path:
    """
    Convert a parent model reference to a filesystem path.

    Args:
        parent: Parent model identifier (e.g., "minecraft:item/handheld").
        assets_root: Root directory containing the assets folder.

    Returns:
        Path to the parent model JSON file.
    """
    namespace, path = split_namespace(parent, default_namespace="minecraft")
    return assets_root / "assets" / namespace / "models" / f"{path}.json"
