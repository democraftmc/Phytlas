# Python Refactor Documentation

## Overview

This document describes the complete refactoring of the Python codebase to maximize modularity, improve clarity, and follow best practices.

## New Project Structure

```
project/
├── converter.py              # High-level orchestration (main entry point)
├── utils/                    # Utility modules
│   ├── __init__.py
│   ├── logging.py           # Status messages with color support
│   ├── config.py            # Configuration management
│   ├── hashing.py           # MD5 hashing for identifiers
│   └── file_ops.py          # File and directory operations
├── services/                 # Service modules for complex operations
│   ├── __init__.py
│   ├── dependency.py        # Dependency checking and job throttling
│   ├── pack_builder.py      # Bedrock pack manifest generation
│   ├── texture_atlas.py     # Texture atlas generation
│   └── texture_utils.py     # Texture resolution utilities
├── handlers/                 # Handler modules for pack operations
│   ├── __init__.py
│   ├── pack_handler.py      # Pack extraction and validation
│   ├── manifest.py          # Manifest and texture config files
│   └── language.py          # Language file generation
├── converters/               # Model conversion modules
│   ├── __init__.py
│   ├── parental.py          # Parent model resolution
│   ├── geometry.py          # Bedrock geometry building
│   └── model_converter.py   # Model conversion orchestration
└── models/                   # Data models and structures
    ├── __init__.py
    └── geyser.py            # Geyser mappings generation
```

## Module Descriptions

### converter.py (Main Entry Point)
**Purpose**: High-level orchestration of the conversion process.
**Responsibilities**:
- Coordinate the entire conversion workflow
- Call functions from other modules
- Handle the main conversion pipeline
- NO helper functions, NO internal logic
- Pure orchestration and pipeline management

**Key Functions**:
- `convert_resource_pack()` - Main conversion entry point
- `build_pack_metadata()` - Create pack metadata
- `copy_pack_icon()` - Copy pack icons
- `process_model_overrides()` - Process all model overrides
- `process_single_override()` - Process a single override

### utils/ - Utility Modules

#### utils/logging.py
**Purpose**: Logging and status message output.
**Public Functions**:
- `status_message(level, message)` - Display colored status messages

#### utils/config.py
**Purpose**: Configuration management and user prompts.
**Public Functions**:
- `prompt_config_value(key, prompt, default, description)` - Prompt for config
- `clear_config_cache()` - Clear configuration cache
- `get_cached_config(key)` - Get cached configuration

#### utils/hashing.py
**Purpose**: Generate MD5 hashes for model identifiers.
**Public Functions**:
- `hash_model_identifier(predicate_key, model_path)` - Generate hash tuple

#### utils/file_ops.py
**Purpose**: File and directory operations.
**Public Functions**:
- `zip_directory(source_dir, destination_zip)` - Create ZIP archive
- `slugify(value)` - Convert string to safe filename
- `ensure_directory(path)` - Ensure directory exists
- `copy_file_safe(source, destination)` - Safe file copy
- `consolidate_files(base_dir)` - Flatten directory structure

### services/ - Service Modules

#### services/dependency.py
**Purpose**: Dependency checking and job management.
**Public Functions**:
- `ensure_dependency(name, check_command, expect_tokens)` - Verify CLI dependency
- `throttle_jobs(max_parallel)` - Throttle parallel jobs

#### services/pack_builder.py
**Purpose**: Build Bedrock pack manifests.
**Public Functions**:
- `build_pack_manifests(meta, rp_dir, bp_dir)` - Generate manifest files

#### services/texture_atlas.py
**Purpose**: Generate texture atlases from individual textures.
**Public Functions**:
- `generate_atlas(texture_files, output_dir, atlas_name)` - Create texture atlas

#### services/texture_utils.py
**Purpose**: Texture resolution and utilities.
**Public Functions**:
- `resolve_texture_files(textures, assets_root)` - Resolve texture paths
- `resolve_texture_value(value, textures, depth)` - Resolve texture references
- `ensure_placeholder_texture(target)` - Create placeholder texture
- `split_namespace(resource, default_namespace)` - Split namespaced identifiers

### handlers/ - Handler Modules

#### handlers/pack_handler.py
**Purpose**: Handle pack extraction and validation.
**Public Functions**:
- `locate_pack_root(extracted_root)` - Find pack root directory
- `read_pack_description(mcmeta_path)` - Read pack description

#### handlers/manifest.py
**Purpose**: Write manifest and configuration files.
**Public Functions**:
- `write_disable_animation(animations_dir)` - Write disable animation
- `write_texture_manifest(path, atlas_name, texture_data)` - Write texture manifest

#### handlers/language.py
**Purpose**: Generate language files.
**Public Functions**:
- `write_language_files(texts_dir, lang_entries)` - Write language files
- `format_display_name(item_id, cmd)` - Format item display names

### converters/ - Converter Modules

#### converters/parental.py
**Purpose**: Resolve Java model parent inheritance chains.
**Public Functions**:
- `resolve_parental(model_path, assets_root)` - Resolve model hierarchy
- `parent_to_model_path(parent, assets_root)` - Convert parent to path

#### converters/geometry.py
**Purpose**: Build Bedrock geometry from Java models.
**Public Functions**:
- `build_geometry(elements, frames, atlas_size, geometry_identifier)` - Build geometry
- `round_value(value)` - Round float to 4 decimals

#### converters/model_converter.py
**Purpose**: Convert Java models to Bedrock format.
**Public Functions**:
- `convert_model(entry, resolved_model, rp_root, bp_root, textures_root, materials)` - Convert model

### models/ - Data Models

#### models/geyser.py
**Purpose**: Generate Geyser custom item mappings.
**Public Functions**:
- `write_geyser_mappings(entries, output_path)` - Write Geyser mappings

## Key Changes from Original Code

### 1. All Private Functions Made Public
All functions that previously started with `_` have been renamed to be public:
- `_split_namespace()` → `split_namespace()`
- `_locate_pack_root()` → `locate_pack_root()`
- `_read_pack_description()` → `read_pack_description()`
- `_write_disable_animation()` → `write_disable_animation()`
- `_ensure_placeholder_texture()` → `ensure_placeholder_texture()`
- `_write_texture_manifest()` → `write_texture_manifest()`
- `_write_language_files()` → `write_language_files()`
- `_format_display_name()` → `format_display_name()`
- `_zip_directory()` → `zip_directory()`
- `_slugify()` → `slugify()`
- `_parent_to_model_path()` → `parent_to_model_path()`
- `_resolve_texture_files()` → `resolve_texture_files()`
- `_resolve_texture_value()` → `resolve_texture_value()`
- `_round()` → `round_value()`
- `_build_geometry()` → `build_geometry()`

### 2. Type Hints Everywhere
- All function parameters have type hints
- All return types are specified
- Using `from __future__ import annotations` for forward references
- Optional types properly annotated with `Optional[...]` or `... | None`

### 3. Comprehensive Docstrings
- Every public function has a docstring
- Docstrings follow Google style format
- Include Args, Returns, and Raises sections
- Clear, concise descriptions

### 4. Improved Organization
- Related functions grouped into logical modules
- Clear separation of concerns
- No circular imports
- Clean import paths through `__init__.py` files

### 5. Better Naming
- Consistent naming conventions throughout
- Clear, descriptive function names
- Meaningful variable names
- No cryptic abbreviations

### 6. PEP8 Compliance
- Proper line lengths
- Consistent spacing
- Standard import ordering
- Clear code structure

## Usage Example

```python
from converter import convert_resource_pack

# Convert a Java resource pack to Bedrock format
resource_pack, behavior_pack = convert_resource_pack(
    input_zip="MyPack.zip",
    output_root="output",
    attachable_material="entity_alphatest_one_sided",
    block_material="alpha_test",
)

print(f"Resource pack: {resource_pack}")
print(f"Behavior pack: {behavior_pack}")
```

## Benefits of the New Structure

1. **Scalability**: Easy to add new features by creating new modules
2. **Maintainability**: Clear organization makes code easy to understand
3. **Testability**: Modular functions are easier to test in isolation
4. **Reusability**: Utility functions can be used across different parts of the project
5. **Clarity**: High-level orchestration in converter.py shows the workflow clearly
6. **Type Safety**: Type hints help catch errors early
7. **Documentation**: Comprehensive docstrings serve as inline documentation

## Migration Notes

- Old files preserved as `app.py.old` and `models.py.old`
- All functionality from original code is preserved
- No breaking changes to the conversion logic
- Import paths have changed - update any external code accordingly
