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
        payload["icon"] = entry["path_hash"]

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
    output_path.write_text(json.dumps(geyser_json), encoding="utf-8")


def write_geyser_item_mappings_v2(entries: Iterable[Mapping[str, Any]], output_path: Path) -> None:
    """
    Emit geyser_mappings.json compatible with Geyser's v2 custom item definitions (1.21.4).

    Args:
        entries: Iterable of config dictionaries containing at minimum 
                 `item`, `path_hash`, `namespace`, `model_path`, `model_name`, and `nbt`.
        output_path: Destination JSON file (typically `target/geyser_mappings.json`).
    """
    mappings: dict[str, list[dict[str, Any]]] = defaultdict(list)
    
    for entry in entries:
        item_id = entry.get("item")
        if item_id is None:
            continue
        
        java_id = item_id if ":" in item_id else f"minecraft:{item_id}"
        bedrock_name = java_id

        model_path = entry.get("model_path", "")
        model_name = entry.get("model_name", "")
        namespace = entry.get("namespace", "minecraft")
        
        model_full_path = f"{model_path}/{model_name}" if model_path else model_name
        model_id = f"{namespace}:{model_full_path}"

        path_hash = entry["path_hash"]
        override = entry.get("override", {})
        raw_target_model = entry.get("raw_target_model", {})
        base_model_data = entry.get("base_model_data", {})

        payload_def = {
            "type": "definition",
            "model": model_id,
            "bedrock_identifier": f"geyser_custom:{path_hash}",
            "bedrock_options": {
                "icon": path_hash,
                "allow_offhand": True
            }
        }
        
        # Merge any extra geyser v2 fields provided via custom overrides in the json
        # We check base_model_data, raw_target_model, and override in order of precedence:
        # override beats raw_target_model which beats base_model_data
        def apply_custom_keys(payload: dict):
            for source in (base_model_data, raw_target_model, override):
                for k, v in source.items():
                    if k in ("model", "predicate", "overrides", "parent", "textures", "elements", "display"): 
                        continue # Skip standard Java modeling keys or handled ones
                    if k == "bedrock_options" and isinstance(v, dict):
                        payload["bedrock_options"].update(v)
                    else:
                        payload[k] = v
            
                # If the user specifically set a geyser 'predicate', use it
                if "geyser_predicate" in source:
                    payload["predicate"] = source["geyser_predicate"]
                elif "predicate" in source:
                    # Avoid overwriting Java's predicate unless it's explicitly formatted for Geyser
                    if isinstance(source["predicate"], list) or "type" in source["predicate"]:
                        payload["predicate"] = source["predicate"]

        apply_custom_keys(payload_def)

        mappings[bedrock_name].append(payload_def)

        nbt = entry.get("nbt", {}) or {}
        if "CustomModelData" in nbt:
            payload_legacy = {
                "type": "legacy",
                "custom_model_data": nbt["CustomModelData"],
                "bedrock_identifier": f"geyser_custom:{path_hash}_legacy",
                "bedrock_options": {
                    "icon": path_hash,
                    "allow_offhand": True
                }
            }
            apply_custom_keys(payload_legacy)
                
            mappings[bedrock_name].append(payload_legacy)

    geyser_json = {
        "format_version": 2,
        "items": mappings,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(geyser_json, indent=4), encoding="utf-8")

