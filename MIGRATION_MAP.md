# Migration Map: Old → New Structure

This document shows exactly where each function from the original code was moved in the refactored structure.

## From `app.py` → New Modules

### Moved to `utils/logging.py`
- `_COLOR_THEMES` → `COLOR_THEMES` (made public, module-level constant)
- `status_message()` → `status_message()` (unchanged, now public)

### Moved to `utils/config.py`
- `_CONFIG_CACHE` → `_CONFIG_CACHE` (internal to module)
- `prompt_config_value()` → `prompt_config_value()` (unchanged)
- Added: `clear_config_cache()` (new utility function)
- Added: `get_cached_config()` (new utility function)

### Moved to `utils/hashing.py`
- `hash_model_identifier()` → `hash_model_identifier()` (unchanged)

### Moved to `utils/file_ops.py`
- `_zip_directory()` → `zip_directory()` (made public)
- `_slugify()` → `slugify()` (made public)
- Added: `ensure_directory()` (new utility function)
- Added: `copy_file_safe()` (new utility function)
- Added: `consolidate_files()` (moved from models.py)

### Moved to `services/dependency.py`
- `ensure_dependency()` → `ensure_dependency()` (unchanged)
- `throttle_jobs()` → `throttle_jobs()` (unchanged)

### Moved to `services/pack_builder.py`
- `build_pack_manifests()` → `build_pack_manifests()` (unchanged)

### Moved to `handlers/pack_handler.py`
- `_locate_pack_root()` → `locate_pack_root()` (made public)
- `_read_pack_description()` → `read_pack_description()` (made public)

### Moved to `handlers/manifest.py`
- `_write_disable_animation()` → `write_disable_animation()` (made public)
- `_write_texture_manifest()` → `write_texture_manifest()` (made public)

### Moved to `handlers/language.py`
- `_write_language_files()` → `write_language_files()` (made public)
- `_format_display_name()` → `format_display_name()` (made public)

### Moved to `services/texture_utils.py`
- `_ensure_placeholder_texture()` → `ensure_placeholder_texture()` (made public)
- `_split_namespace()` → `split_namespace()` (made public)

### Refactored to `converter.py`
The main `convert_resource_pack()` function was split into:
- `convert_resource_pack()` - Main orchestration (high-level only)
- `build_pack_metadata()` - Build metadata (extracted helper)
- `copy_pack_icon()` - Copy pack icon (extracted helper)
- `process_model_overrides()` - Process all overrides (extracted helper)
- `process_single_override()` - Process single override (extracted helper)

## From `models.py` → New Modules

### Moved to `converters/parental.py`
- `resolve_parental()` → `resolve_parental()` (unchanged)
- `_parent_to_model_path()` → `parent_to_model_path()` (made public)

### Moved to `services/texture_atlas.py`
- `generate_atlas()` → `generate_atlas()` (unchanged)

### Moved to `converters/model_converter.py`
- `convert_model()` → `convert_model()` (unchanged)

### Moved to `models/geyser.py`
- `write_geyser_mappings()` → `write_geyser_mappings()` (unchanged)

### Moved to `services/texture_utils.py`
- `_split_namespace()` → `split_namespace()` (made public)
- `_resolve_texture_files()` → `resolve_texture_files()` (made public)
- `_resolve_texture_value()` → `resolve_texture_value()` (made public)

### Moved to `converters/geometry.py`
- `_round()` → `round_value()` (made public, renamed for clarity)
- `_build_geometry()` → `build_geometry()` (made public)

### Moved to `utils/file_ops.py`
- `consolidate_files()` → `consolidate_files()` (unchanged)

### Removed
- `add_to_terrain_mappings()` - Empty placeholder function, not needed

## Summary of Changes

### Functions Made Public (prefix `_` removed)
1. `_split_namespace()` → `split_namespace()`
2. `_locate_pack_root()` → `locate_pack_root()`
3. `_read_pack_description()` → `read_pack_description()`
4. `_write_disable_animation()` → `write_disable_animation()`
5. `_ensure_placeholder_texture()` → `ensure_placeholder_texture()`
6. `_write_texture_manifest()` → `write_texture_manifest()`
7. `_write_language_files()` → `write_language_files()`
8. `_format_display_name()` → `format_display_name()`
9. `_zip_directory()` → `zip_directory()`
10. `_slugify()` → `slugify()`
11. `_parent_to_model_path()` → `parent_to_model_path()`
12. `_resolve_texture_files()` → `resolve_texture_files()`
13. `_resolve_texture_value()` → `resolve_texture_value()`
14. `_round()` → `round_value()` (also renamed)
15. `_build_geometry()` → `build_geometry()`

### New Helper Functions Added
1. `clear_config_cache()` - Clear configuration cache
2. `get_cached_config()` - Get cached config value
3. `ensure_directory()` - Ensure directory exists
4. `copy_file_safe()` - Safe file copy with directory creation

### Functions Extracted for Better Organization
From the main `convert_resource_pack()` function:
1. `build_pack_metadata()` - Extracted metadata building
2. `copy_pack_icon()` - Extracted icon copying
3. `process_model_overrides()` - Extracted override processing
4. `process_single_override()` - Extracted single override processing

## Module Organization Rationale

### `utils/` - Pure utility functions
- **logging.py**: Output and display functions
- **config.py**: Configuration management
- **hashing.py**: Cryptographic functions
- **file_ops.py**: File system operations

### `services/` - Complex business logic services
- **dependency.py**: External dependency management
- **pack_builder.py**: Pack manifest generation
- **texture_atlas.py**: Atlas generation (requires PIL)
- **texture_utils.py**: Texture resolution and utilities

### `handlers/` - File I/O and data handlers
- **pack_handler.py**: Pack extraction and validation
- **manifest.py**: Manifest file writing
- **language.py**: Language file generation

### `converters/` - Model conversion logic
- **parental.py**: Java model inheritance resolution
- **geometry.py**: Bedrock geometry building
- **model_converter.py**: Main model conversion

### `models/` - Data structures and formats
- **geyser.py**: Geyser mapping format generation

### `converter.py` - Main entry point
- High-level orchestration only
- No helper functions
- Clear pipeline structure
- Delegates to specialized modules

## Import Examples

### Old Code (app.py)
```python
from models import convert_model, resolve_parental, write_geyser_mappings
```

### New Code
```python
from converters import convert_model, resolve_parental
from models import write_geyser_mappings
```

### Using Utilities
```python
from utils import status_message, hash_model_identifier, slugify
from services import build_pack_manifests, generate_atlas
from handlers import write_language_files, format_display_name
```

## Benefits

1. **Modularity**: Each module has a single, clear purpose
2. **Testability**: Functions can be tested in isolation
3. **Maintainability**: Easy to find and update specific functionality
4. **Scalability**: Easy to add new features without cluttering existing code
5. **Readability**: Clear organization makes code easier to understand
6. **Type Safety**: All functions have complete type hints
7. **Documentation**: Every function has comprehensive docstrings
