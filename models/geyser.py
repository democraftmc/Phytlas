"""Geyser mappings generation."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping


def write_geyser_item_mappings(entries: Iterable[Mapping[str, Any]], output_path: Path) -> None:
    """
    Emit geyser_mappings.json compatible with Geyser's custom item definitions.

    Args:
        entries: Iterable of config dictionaries containing at minimum 
                 `item`, `path_hash`, `generated`, `bedrock_icon`, and `nbt`.
        output_path: Destination JSON file (typically `target/geyser_mappings.json`).

    Returns:
        None. Writes the mappings file to disk.
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

