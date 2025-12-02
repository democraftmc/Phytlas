<div align="center">

<img src="./blob/images/logo.png" alt="Phytlas Logo" width="200"/>

# 🐍 Phytlas  
### _Context-Aware Translation Manager for DEMOCRAFT_

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

## TODO/Bug Reports

- [ ] Fix 3D model height (flying)
- [ ] Fix 3D model icon in inventory 

## Usage

```bash
python3 converter.py <path_to_resource_pack.zip> [options]
```

**Options:**
- `-o`, `--output`: Output directory (default: `target`)
- `--attachable-material`: Material for attachables (default: `entity_alphatest_one_sided`)
- `--block-material`: Material for blocks (default: `alpha_test`)

### Features

- **Full Python Implementation**: Replaces the legacy Bash/jq script with a robust Python codebase.
- **3D Model Conversion**: Converts Java block/item models to Bedrock geometry and attachables.
- **Display Settings Mapping**: Accurately maps Java `display` settings (rotation, translation, scale) to Bedrock animations using a nested bone structure (`root` -> `x` -> `y` -> `z`) to prevent gimbal lock and ensure correct orientation.
- **2D Item Support**: Handles standard 2D items with custom model data.
- **Atlas Generation**: Automatically generates texture atlases using Pillow (no Node.js required).
- **Manifest Generation**: Creates valid `manifest.json` for Behavior and Resource packs.

### Requirements
- Python 3.8+
- Pillow (`pip install Pillow`)
