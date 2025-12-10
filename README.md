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
**Phytlas** is a simple converter that turns Minecraft: Java Edition resource packs into Minecraft: Bedrock Edition resource packs. It uses mappings provided by [Geyser](https://geysermc.org/) to bridge differences between the two editions.

Phytlas is open source and driven by the community. If you'd like to support development, consider [sponsoring us](https://github.com/sponsors/Funasitien) or [donating through Ko-fi](https://ko-fi.com/funasitien).

## ✨ Features

- 🐍 **Pure Python** — replaces the old Bash/jq script with a robust Python codebase.  
- 🎨 **2D Item Support** — handles standard 2D items with custom model data (no fake 3D models).  
- 🎲 **3D Model Conversion** — converts Java block/item models into Bedrock geometry and attachables.  
- 📦 **Custom Block Support** — converts Java block textures and maps them to custom Bedrock variants.  
- 🔎 **Display Mapping** — maps Java `display` settings (rotation, translation, scale) to Bedrock animations using a nested bone structure (`root` → `x` → `y` → `z`) to avoid gimbal lock and keep correct orientation.  
- 🖌️ **Atlas Generation** — builds texture atlases automatically using Pillow (no Node.js required).  
- 📝 **Manifest Generation** — creates valid `manifest.json` files for Behavior and Resource packs.

## 🔥 Requirements
- Python 3.8 or newer  
- Pillow (`pip install Pillow`)
- Numpy (`pip install numpy`)

## 📚 Usage
1. Clone the repository on your PC using git
2. Install Python and the necessary extension(s) with pip : `pip install Pillow` and `pip install numpy`
3. Put your pack in the folder you just created by cloning the repo
4. Run the folowing command:
python3 converter.py <path_to_resource_pack.zip> [options]
```

**Options**

* `-o`, `--output` — Output directory (default: `target`)
* `--attachable-material` — Material used for attachables (default: `entity_alphatest_one_sided`)
* `--block-material` — Material used for blocks (default: `alpha_test`)

## 📌 TODO / Known issues

* [x] Use two processors depending on whether an item is 2D or 3D
* [x] Fix 3D model height (floating models)
* [x] Implement block mappings
* [x] Add custom font support (by converting only compatible E`X` glyphs)
* [x] Add minecraft sounds support
* [ ] Fix block mappings rejected by Geyser (note = 0)
* [ ] Fix 3D item icon rotation in inventory
* [ ] Fix 3D item icon rendering for blocks
* [ ] Add custom sounds support
* [ ] Add armor support (latest components only — not shaders)

## 🪄 If you liked Phytlas...

You might also be interested in these projects:

* [BedrockAdder](https://github.com/Antwns/BedrockAdder) — a V2 mapping converter by *Antwns* (C)
* [IAGeyser](https://gitlab.com/pixlstudios/iageyser-rewrite) — a PHP CLI tool to convert ItemsAdder packs to Geyser-compatible resource packs
