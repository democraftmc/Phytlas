# LetsFuckCapitalism
Project Code: LetsFuckCapitalism.
Use the magic of python to replace one specific anoying paid tool.

This is a super duper secret project, not even knew by the DEMOCRAFT's staff. Please refer to the code name in the PRs/Issues.

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
- **3D Items**: Converted to Bedrock Items with Attachables.
  - In-hand: Renders the custom 3D geometry.
  - Inventory: Uses a 2D icon (extracted from `layer0` or first texture).
- **2D Items**: Converted to Bedrock Items with standard textures.
- **Atlases**: Automatically generated using Pillow (no external tools required).
- **Manifests**: Automatically generated.

### Requirements
- Python 3.8+
- Pillow (`pip install Pillow`)
