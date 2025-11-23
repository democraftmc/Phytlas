from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import uuid
import zipfile
from pathlib import Path
from typing import Any, Mapping, Sequence

from models import convert_model, resolve_parental, write_geyser_mappings


_COLOR_THEMES: dict[str, str] = {
    "completion": "\033[32m[+]\033[0m ",
    "process": "\033[33m[•]\033[0m ",
    "critical": "\033[31m[X]\033[0m ",
    "error": "\033[31m[ERROR]\033[0m ",
    "info": "\033[36m",
    "plain": "",
}

_CONFIG_CACHE: dict[str, str] = {}

def status_message(level: str, message: str) -> None:
    """
    Render a normalized status line.

    Args:
    - level: Semantic label such as "completion" or "error".
    - message: Already formatted message body.

    Returns:
    - None. Emits directly to stdout/stderr.
    """
    normalized = level.lower().strip()
    prefix = _COLOR_THEMES.get(normalized, _COLOR_THEMES["plain"])
    suffix = "\033[0m" if normalized == "info" else ""
    stream = sys.stderr if normalized in {"error", "critical"} else sys.stdout
    text = message.rstrip("\n")
    stream.write(f"{prefix}{text}{suffix}\n")
    stream.flush()


def ensure_dependency(name: str, check_command: Sequence[str], expect_tokens: Sequence[str] | None = None) -> None:
    """
    Verify a CLI dependency is reachable.

    Args:
    - name: Friendly dependency name for error reporting.
    - check_command: Exact argv executed via subprocess.
    - expect_tokens: Optional substrings that must appear in stdout/stderr.

    Raises:
    - RuntimeError: if the command is missing or validation fails.
    """
    try:
        completed = subprocess.run(
            check_command,
            capture_output=True,
            text=True,
            check=True,
        )
    except FileNotFoundError as exc:  # pragma: no cover - defensive
        raise RuntimeError(f"Dependency {name} is not installed") from exc
    except subprocess.CalledProcessError as exc:  # pragma: no cover - defensive
        raise RuntimeError(f"Dependency {name} failed health check") from exc

    output = f"{completed.stdout}{completed.stderr}" if completed else ""
    if expect_tokens:
        if not any(token in output for token in expect_tokens):
            raise RuntimeError(
                f"Dependency {name} is present but did not report an expected version; saw: {output.strip() or '<empty>'}"
            )

    status_message("completion", f"Dependency {name} satisfied")


def prompt_config_value(key: str, prompt: str, default: str, description: str) -> str:
    """
    Ask the user for a config value only when it is unset.

    Args:
    - key: Identifier used by the calling workflow to store the answer.
    - prompt: Human-readable question displayed to the user.
    - default: Value adopted when the user presses enter.
    - description: Short explanation echoed back in summaries.

    Returns:
    - The resolved configuration string.
    """
    cached = _CONFIG_CACHE.get(key)
    if cached:
        return cached

    env_value = os.environ.get(key)
    if env_value:
        _CONFIG_CACHE[key] = env_value
        return env_value

    status_message("plain", f"{prompt} [{default}]\n")
    try:
        response = input(f"{description}: ")
    except EOFError:
        response = ""

    print()
    resolved = response.strip() or default
    _CONFIG_CACHE[key] = resolved
    return resolved


def throttle_jobs(max_parallel: int) -> None:
    """
    Block until the number of outstanding worker tasks drops below `max_parallel`.

    Args:
    - max_parallel: Upper bound on concurrent asynchronous jobs.

    Returns:
    - None. Should integrate with whatever concurrency primitive (e.g., asyncio.Semaphore)
      backs the Python port.
    """
    if max_parallel <= 0:
        return

    while max(threading.active_count() - 1, 0) >= max_parallel:
        time.sleep(0.05)


def hash_model_identifier(predicate_key: str, model_path: str) -> tuple[str, str]:
    """
    Compute short hashes that mimic the Bash `md5sum`-based `write_hash` helper.

    Args:
    - predicate_key: Canonical text representing the predicate tuple (item, CMD, damage, etc.).
    - model_path: Filesystem path used to produce the geometry hash.

    Returns:
    - Tuple `(entry_hash, path_hash)` containing the shortened hex digests.
    """
    entry_hash = hashlib.md5(predicate_key.encode("utf-8"), usedforsecurity=False).hexdigest()[:7]
    path_hash = hashlib.md5(model_path.encode("utf-8"), usedforsecurity=False).hexdigest()[:7]
    return entry_hash, path_hash


def build_pack_manifests(meta: Mapping[str, Any], rp_dir: Path, bp_dir: Path) -> None:
    """
    Emit Bedrock resource/behavior pack manifest JSON scaffolding.

    Args:
    - meta: Minimal metadata (name, description, UUIDs, versions).
    - rp_dir: Destination directory for the resource-pack manifest.
    - bp_dir: Destination directory for the behavior-pack manifest.

    Returns:
    - None. Writes files or raises if directories are inaccessible.
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
    bp_dir = Path(bp_dir)
    rp_dir.mkdir(parents=True, exist_ok=True)
    bp_dir.mkdir(parents=True, exist_ok=True)

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

    bp_manifest = {
        "format_version": 2,
        "header": {
            "description": description,
            "name": pack_name,
            "uuid": str(meta["behavior_header_uuid"]).lower(),
            "version": version,
            "min_engine_version": min_engine_version,
        },
        "modules": [
            {
                "description": description,
                "type": "data",
                "uuid": str(meta["behavior_module_uuid"]).lower(),
                "version": version,
            }
        ],
        "dependencies": [
            {
                "uuid": str(meta["resource_header_uuid"]).lower(),
                "version": version,
            }
        ],
    }

    (rp_dir / "manifest.json").write_text(json.dumps(rp_manifest, indent=2))
    (bp_dir / "manifest.json").write_text(json.dumps(bp_manifest, indent=2))

    status_message("completion", "Generated Bedrock manifest scaffolding")


def convert_resource_pack(
    input_zip: str | Path,
    output_root: Path | None = None,
    *,
    attachable_material: str = "entity_alphatest_one_sided",
    block_material: str = "alpha_test",
) -> tuple[Path, Path]:
    """
    Convert a Java resource pack zip into Bedrock-ready resource/behavior packs plus
    Geyser mappings.

    Returns the paths to the generated resource and behavior mcpack archives.
    """

    input_zip = Path(input_zip).expanduser().resolve()
    if not input_zip.is_file():
        raise FileNotFoundError(f"Input pack {input_zip} was not found")

    output_root = Path(output_root or (Path.cwd() / "target"))
    shutil.rmtree(output_root, ignore_errors=True)
    rp_root = output_root / "rp"
    bp_root = output_root / "bp"
    for root in (rp_root, bp_root):
        root.mkdir(parents=True, exist_ok=True)

    textures_root = rp_root / "textures"
    textures_root.mkdir(parents=True, exist_ok=True)

    materials = {
        "attachable_material": attachable_material,
        "block_material": block_material,
    }

    status_message("process", f"Extracting {input_zip.name}")
    with tempfile.TemporaryDirectory(prefix="pack_extract_") as temp_dir:
        extract_root = Path(temp_dir)
        with zipfile.ZipFile(input_zip, "r") as archive:
            archive.extractall(extract_root)

        pack_root = _locate_pack_root(extract_root)
        if pack_root is None:
            raise RuntimeError("Unable to locate pack.mcmeta in the provided archive")

        item_dir = pack_root / "assets" / "minecraft" / "models" / "item"
        if not item_dir.exists():
            raise RuntimeError("No assets/minecraft/models/item directory found in pack")

        pack_description = _read_pack_description(pack_root / "pack.mcmeta")

        meta = {
            "name": pack_description,
            "description": "Adds 3D items for use with a Geyser proxy",
            "resource_header_uuid": uuid.uuid4(),
            "resource_module_uuid": uuid.uuid4(),
            "behavior_header_uuid": uuid.uuid4(),
            "behavior_module_uuid": uuid.uuid4(),
            "version": [1, 0, 0],
        }
        build_pack_manifests(meta, rp_root, bp_root)

        if (pack_root / "pack.png").exists():
            shutil.copy2(pack_root / "pack.png", rp_root / "pack_icon.png")
            shutil.copy2(pack_root / "pack.png", bp_root / "pack_icon.png")

        _write_disable_animation(rp_root / "animations")
        _ensure_placeholder_texture(textures_root / "0.png")

        converted_entries: list[dict[str, Any]] = []
        item_texture_data: dict[str, dict[str, str]] = {}
        terrain_texture_data: dict[str, dict[str, str]] = {}
        lang_entries: list[tuple[str, str]] = []

        status_message("process", "Walking item override files")
        for model_file in sorted(item_dir.rglob("*.json")):
            item_id = f"minecraft:{model_file.stem}"
            try:
                model_data = json.loads(model_file.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                status_message("error", f"Skipping invalid JSON {model_file}: {exc}")
                continue

            for index, override in enumerate(model_data.get("overrides") or []):
                predicate = override.get("predicate") or {}
                cmd = predicate.get("custom_model_data")
                if cmd is None:
                    continue
                target_model = override.get("model")
                if not target_model:
                    continue

                namespace, relative_model = _split_namespace(target_model, default="minecraft")
                target_json = pack_root / "assets" / namespace / "models" / f"{relative_model}.json"
                if not target_json.exists():
                    status_message("error", f"Missing referenced model {target_model}")
                    continue

                try:
                    resolved = resolve_parental(target_json, assets_root=pack_root)
                except Exception as exc:  # pragma: no cover - defensive
                    status_message("error", f"Failed to resolve {target_json}: {exc}")
                    continue

                predicate_key = f"{item_id}_cmd{cmd}_idx{index}"
                entry_hash, geo_hash = hash_model_identifier(predicate_key, str(target_json))
                path_hash = f"gmdl_{entry_hash}"
                geometry_id = f"geo_{geo_hash}"
                model_parts = relative_model.split("/")
                model_name = model_parts[-1]
                model_path = "/".join(model_parts[:-1])

                entry = {
                    "item": item_id,
                    "path_hash": path_hash,
                    "namespace": namespace,
                    "model_path": model_path,
                    "model_name": model_name,
                    "generated": resolved["generated"],
                    "geometry": geometry_id,
                    "bedrock_icon": {"icon": "camera", "frame": 0},
                    "nbt": {"CustomModelData": int(cmd)},
                }

                try:
                    convert_model(entry, resolved, rp_root, bp_root, textures_root, materials)
                except Exception as exc:  # pragma: no cover - defensive
                    status_message("error", f"Conversion failed for {target_model}: {exc}")
                    continue

                converted_entries.append(entry)
                display_name = _format_display_name(item_id, int(cmd))
                lang_entries.append((path_hash, display_name))

                if entry["generated"]:
                    item_texture_data[path_hash] = {"textures": f"textures/{path_hash}"}
                else:
                    atlas_key = f"gmdl_atlas_{path_hash}"
                    terrain_texture_data[atlas_key] = {"textures": f"textures/{path_hash}"}

        if not converted_entries:
            raise RuntimeError("No convertible custom_model_data overrides were found")

    _write_texture_manifest(
        rp_root / "textures" / "item_texture.json",
        "atlas.items",
        item_texture_data,
    )
    _write_texture_manifest(
        rp_root / "textures" / "terrain_texture.json",
        "atlas.terrain",
        terrain_texture_data,
    )

    _write_language_files(rp_root / "texts", lang_entries)

    mappings_path = output_root / "geyser_mappings.json"
    write_geyser_mappings(converted_entries, mappings_path)

    resource_zip = output_root / f"{_slugify(pack_description)}_resources.mcpack"
    behavior_zip = output_root / f"{_slugify(pack_description)}_behaviors.mcpack"
    _zip_directory(rp_root, resource_zip)
    _zip_directory(bp_root, behavior_zip)

    status_message("completion", f"Conversion complete -> {resource_zip.name}, {behavior_zip.name}")
    return resource_zip, behavior_zip


def _split_namespace(resource: str, default: str = "minecraft") -> tuple[str, str]:
    if ":" in resource:
        namespace, path = resource.split(":", 1)
    else:
        namespace, path = default, resource
    return namespace, path.strip("/")


def _locate_pack_root(extracted_root: Path) -> Path | None:
    if (extracted_root / "pack.mcmeta").exists():
        return extracted_root
    candidates = list(extracted_root.glob("**/pack.mcmeta"))
    return candidates[0].parent if candidates else None


def _read_pack_description(mcmeta_path: Path) -> str:
    try:
        data = json.loads(mcmeta_path.read_text(encoding="utf-8"))
        return data.get("pack", {}).get("description", "Converted Resource Pack")
    except Exception:  # pragma: no cover - fallback
        return "Converted Resource Pack"


def _write_disable_animation(animations_dir: Path) -> None:
    animations_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "format_version": "1.8.0",
        "animations": {
            "animation.geyser_custom.disable": {
                "loop": True,
                "override_previous_animation": True,
                "bones": {"geyser_custom": {"scale": 0}},
            }
        },
    }
    (animations_dir / "animation.geyser_custom.disable.json").write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )


def _ensure_placeholder_texture(target: Path) -> None:
    if target.exists():
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        from PIL import Image
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise RuntimeError("Pillow is required to write placeholder textures") from exc
    Image.new("RGBA", (16, 16), (255, 255, 255, 255)).save(target)


def _write_texture_manifest(path: Path, atlas_name: str, texture_data: Mapping[str, Any]) -> None:
    payload = {
        "resource_pack_name": "geyser_custom",
        "texture_name": atlas_name,
        "texture_data": texture_data,
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_language_files(texts_dir: Path, lang_entries: list[tuple[str, str]]) -> None:
    texts_dir.mkdir(parents=True, exist_ok=True)
    lines = [f"item.geyser_custom:{key}.name={value}" for key, value in lang_entries]
    (texts_dir / "en_US.lang").write_text("\n".join(lines), encoding="utf-8")
    shutil.copy2(texts_dir / "en_US.lang", texts_dir / "en_GB.lang")
    (texts_dir / "languages.json").write_text(json.dumps(["en_US", "en_GB"], indent=2), encoding="utf-8")


def _format_display_name(item_id: str, cmd: int) -> str:
    base = item_id.split(":")[-1].replace("_", " ").title()
    return f"{base} (CMD {cmd})"


def _zip_directory(source_dir: Path, destination_zip: Path) -> None:
    with zipfile.ZipFile(destination_zip, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for file_path in sorted(source_dir.rglob("*")):
            if file_path.is_file():
                archive.write(file_path, file_path.relative_to(source_dir))


def _slugify(value: str) -> str:
    sanitized = re.sub(r"[^A-Za-z0-9_-]+", "_", value.strip())
    return sanitized or "converted_pack"