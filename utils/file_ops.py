"""File and directory operation utilities."""

from __future__ import annotations

import re
import shutil
import zipfile
from pathlib import Path
from typing import Optional

_ZIP_EPOCH = (1980, 1, 1, 0, 0, 0)


def zip_directory(source_dir: Path, destination_zip: Path) -> None:
    """
    Create a ZIP archive from a directory.

    Args:
        source_dir: Directory to archive.
        destination_zip: Path where the ZIP file should be created.

    Returns:
        None. Creates the ZIP file at the specified destination.
    """
    with zipfile.ZipFile(destination_zip, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for file_path in sorted(source_dir.rglob("*")):
            if not file_path.is_file():
                continue

            arcname = file_path.relative_to(source_dir).as_posix()
            try:
                zinfo = zipfile.ZipInfo.from_file(file_path, arcname)
            except ValueError as exc:  # legacy timestamps trigger this
                if "timestamps before 1980" not in str(exc):
                    raise
                stat_res = file_path.stat()
                zinfo = zipfile.ZipInfo(arcname, _ZIP_EPOCH)
                zinfo.external_attr = (stat_res.st_mode & 0xFFFF) << 16
                zinfo.file_size = stat_res.st_size
            else:
                if zinfo.date_time < _ZIP_EPOCH:
                    zinfo.date_time = _ZIP_EPOCH

            with file_path.open("rb") as src:
                archive.writestr(zinfo, src.read())


def slugify(value: str) -> str:
    """
    Convert a string to a safe filename slug.

    Replaces non-alphanumeric characters (except dashes and underscores) with underscores.

    Args:
        value: String to slugify.

    Returns:
        Sanitized string suitable for use in filenames.
    """
    sanitized = re.sub(r"[^A-Za-z0-9_-]+", "_", value.strip())
    return sanitized or "converted_pack"


def ensure_directory(path: Path) -> Path:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        path: Directory path to ensure exists.

    Returns:
        The same path as a Path object.
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def copy_file_safe(source: Path, destination: Path) -> None:
    """
    Safely copy a file, creating parent directories if needed.

    Args:
        source: Source file path.
        destination: Destination file path.

    Returns:
        None. Copies the file to the destination.
    """
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def consolidate_files(base_dir: Path) -> None:
    """
    Flatten nested directories, moving all files directly under base_dir.

    Collisions are resolved by appending incremental suffixes.

    Args:
        base_dir: Base directory to consolidate files into.

    Returns:
        None. Modifies the directory structure in place.
    """
    base_dir = Path(base_dir)
    base_dir.mkdir(parents=True, exist_ok=True)

    for file_path in sorted(base_dir.rglob("*")):
        if not file_path.is_file() or file_path.parent == base_dir:
            continue
        
        target_name = file_path.name
        counter = 1
        while (base_dir / target_name).exists():
            stem = file_path.stem
            suffix = file_path.suffix
            target_name = f"{stem}_{counter}{suffix}"
            counter += 1
        
        shutil.move(str(file_path), base_dir / target_name)

    # Remove now-empty directories, deepest first
    for directory in sorted(base_dir.rglob("*"), reverse=True):
        if directory.is_dir():
            try:
                directory.rmdir()
            except OSError:
                continue
