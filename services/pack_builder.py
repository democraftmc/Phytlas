"""Pack manifest building utilities."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from utils.logging import status_message


def build_pack_manifests(meta: Mapping[str, Any], rp_dir: Path) -> None:
    """
    Emit Bedrock resource/behavior pack manifest JSON scaffolding.

    Args:
        meta: Minimal metadata containing name, description, UUIDs, and versions.
              Required keys: resource_header_uuid, resource_module_uuid,
              behavior_header_uuid, behavior_module_uuid.
        rp_dir: Destination directory for the resource-pack manifest.
        bp_dir: Destination directory for the behavior-pack manifest.

    Returns:
        None. Writes manifest.json files to both directories.

    Raises:
        ValueError: If required metadata keys are missing.
    """
    required_keys = {
        "resource_header_uuid",
        "resource_module_uuid",
        "behavior_header_uuid",
        "behavior_module_uuid",
    }
    missing = [key for key in required_keys if key not in meta]
    if missing:
        raise ValueError(f"Missing manifest metadata keys: {', '.join(missing)}")

    rp_dir = Path(rp_dir)
    rp_dir.mkdir(parents=True, exist_ok=True)

    version = list(meta.get("version", [1, 0, 0]))
    min_engine_version = list(meta.get("min_engine_version", [1, 18, 3]))
    description = meta.get("description", "Adds 3D items for use with a Geyser proxy")
    pack_name = meta.get("name", meta.get("pack_desc", description))

    rp_manifest = {
        "format_version": 2,
        "header": {
            "description": description,
            "name": pack_name,
            "uuid": str(meta["resource_header_uuid"]).lower(),
            "version": version,
            "min_engine_version": min_engine_version,
        },
        "modules": [
            {
                "description": description,
                "type": "resources",
                "uuid": str(meta["resource_module_uuid"]).lower(),
                "version": version,
            }
        ],
    }

    (rp_dir / "manifest.json").write_text(json.dumps(rp_manifest, indent=2))

    status_message("completion", "Generated Bedrock manifest scaffolding")
