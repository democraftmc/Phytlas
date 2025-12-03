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
**Pythlas** is a Minecraft: Java edition to Minecraft: Bedrock edition ressource pack converter. It uses the mappings provided by [Geyser](https://geysermc.org/) to fill the gaps between the two editions (see more bellow).

Pythlas is a open source project driven by the ocmmunity. If you want to suppor devopment, consider [sponsoring us](https://github.com/sponsors/Funasitien) or [donate trough ko-fi](https://ko-fi.com/funasitien).

## ✨ Features

- 🐍 **Full Python Implementation**: Replaces the legacy Bash/jq script with a robust Python codebase.
- ⚔ **2D Item Support**: Handles standard 2D items with custom model data withouth fake 3D models.
- 🎲 **3D Model Conversion**: Converts Java block/item models to Bedrock geometry and attachables.
- 📦 **Custom Bloc Support**: Converts Java blocks texture and map them to custom bedrock variants
- 🔎 **Display Settings Mapping**: Accurately maps Java `display` settings (rotation, translation, scale) to Bedrock animations using a nested bone structure (`root` -> `x` -> `y` -> `z`) to prevent gimbal lock and ensure correct orientation.
- 🖌️ **Atlas Generation**: Automatically generates texture atlases using Pillow (no Node.js required).
- 📝 **Manifest Generation**: Creates valid `manifest.json` for Behavior and Resource packs.

## 🔥 Requirements
- Python 3.8+
- Pillow (`pip install Pillow`)

## 📚 Usage

```bash
python3 converter.py <path_to_resource_pack.zip> [options]
```

**Options:**
- `-o`, `--output`: Output directory (default: `target`)
- `--attachable-material`: Material for attachables (default: `entity_alphatest_one_sided`)
- `--block-material`: Material for blocks (default: `alpha_test`)

## 📌 TODO/Bug Reports

- [x] Create 2 different processors depending if an item is 2D/3D
- [x] Fix 3D model height (flying)
- [x] Implement Bloc Mappings
- [ ] Fix block mappings not allowed by Geyser (note=0)
- [ ] Fix 3D render icon rotation in inventory 
- [ ] Fix 3D render icon for blocks
- [ ] Add support for Sounds
- [ ] Add support for armors (latest components only, not shaders)

## 🪄 If you liked Pythlas...
**...You might be interested in theses others projects :**

- [BedrockAdder](https://github.com/Antwns/BedrockAdder), a V2 mapping converter by *Antwns* written in C
- [IAGeyser](https://gitlab.com/pixlstudios/iageyser-rewrite), A PHP CLI tool to convert Minecraft Java Edition ItemsAdder packs to Geyser-compatible resource packs and custom mappings.