"""Hashing utilities for generating model identifiers."""

from __future__ import annotations

import hashlib


def hash_model_identifier(predicate_key: str, model_path: str) -> tuple[str, str]:
    """
    Compute short MD5 hashes for model identification.

    Creates shortened hex digests that mimic the Bash `md5sum`-based approach.

    Args:
        predicate_key: Canonical text representing the predicate tuple 
                       (item, CMD, damage, etc.).
        model_path: Filesystem path used to produce the geometry hash.

    Returns:
        Tuple `(entry_hash, path_hash)` containing the shortened hex digests (7 chars each).
    """
    entry_hash = hashlib.md5(
        predicate_key.encode("utf-8"), 
        usedforsecurity=False
    ).hexdigest()[:7]
    
    path_hash = hashlib.md5(
        model_path.encode("utf-8"), 
        usedforsecurity=False
    ).hexdigest()[:7]
    
    return entry_hash, path_hash
