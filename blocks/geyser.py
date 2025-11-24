"""Geyser mappings generation."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping



def write_geyser_block_mappings(entries: dict[str, list[str]], output_path: Path) -> None:
    """
    Emit geyser_mappings.json compatible with Geyser's custom item definitions.

    Args:
        entries: Iterable of config dictionaries containing at minimum 
                 `item`, `path_hash`, `generated`, `bedrock_icon`, and `nbt`.
        output_path: Destination JSON file (typically `target/geyser_mappings.json`).

    Returns:
        None. Writes the mappings file to disk.
    """
    mappings: dict[str, dict[str, Any]] = defaultdict(dict)
    for block_type in entries:
        variants: dict[str, Any] = {}
        for block_variant_index in range(len(entries[block_type])):
            variants[entries[block_type][block_variant_index]] = {
                "name": f"block_{block_variant_index}",
                "geometry": "cube_all",
                "material_instances": {
                    "*": {
                        "texture": f"block_{block_variant_index}",
                        "render_method": "alpha_test"
                    }
                }
            }
            
        block_json = {
            "name": block_type,
            "included_in_creative_inventory": False,
            "only_override_states": True,
            "place_air": True,
            "state_overrides": variants
        }

        mappings["minecraft:" +block_type] = block_json

    geyser_json = {
        "format_version": 1,
        "blocks": mappings
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(geyser_json, indent=2), encoding="utf-8")
