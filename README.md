<div align="center">

<img src="./blob/images/logo.png" alt="Phytlas Logo" width="200"/>

# 🐍 Phytlas  
### _Really Real Geyser Converter_

<div align="center">
A project from
<br/>
<a href="https://democraft.fr/oss">
<img src="https://github.com/democraftfr/.github/blob/main/titre-couleur-democraft.png?raw=true" alt="DEMOCRAFT Logo" width="220"/>
</a>
</div>

---

</div>

## 🚀 Introduction
**Pythlas** is 

## Features

- **Full Python Implementation**: Replaces the legacy Bash/jq script with a robust Python codebase.
- **3D Model Conversion**: Converts Java block/item models to Bedrock geometry and attachables.
- **Display Settings Mapping**: Accurately maps Java `display` settings (rotation, translation, scale) to Bedrock animations using a nested bone structure (`root` -> `x` -> `y` -> `z`) to prevent gimbal lock and ensure correct orientation.
- **2D Item Support**: Handles standard 2D items with custom model data.
- **Atlas Generation**: Automatically generates texture atlases using Pillow (no Node.js required).
- **Manifest Generation**: Creates valid `manifest.json` for Behavior and Resource packs.

## Requirements
- Python 3.8+
- Pillow (`pip install Pillow`)

## Usage

```bash
python3 converter.py <path_to_resource_pack.zip> [options]
```

**Options:**
- `-o`, `--output`: Output directory (default: `target`)
- `--attachable-material`: Material for attachables (default: `entity_alphatest_one_sided`)
- `--block-material`: Material for blocks (default: `alpha_test`)

## TODO/Bug Reports

- [x] Create 2 different processors depending if an item is 2D/3D
- [x] Fix 3D model height (flying)
- [x] Implement Bloc Mappings
- [ ] Fix mapping not allowed by Geyser (note=0)
- [ ] Fix 3D model icon in inventory 
