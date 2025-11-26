# LetsFuckCapitalism
Project Code: LetsFuckCapitalism.
Use the magic of python to replace one specific anoying paid tool.

This is a super duper secret project, not even knew by the DEMOCRAFT's staff. Please refer to the code name in the PRs/Issues.

---

**Function Inventory (explicit + nested helpers)**  
- `status_message(type, message)` – centralizes colored logging. Inputs: semantic log level + plain text. Side effects: writes to stdout only; no shared state. External reliance: `printf` escape codes. Python lift: **Easy** (format string helper).  
- `dependency_check(name, site, cmd, grep_expr)` – runs the provided command and looks for a token; exits on failure. Inputs: metadata strings and the probe command. Side effects: process execution; exit 1 on failure. External reliance: `command`, `grep`. Python lift: **Easy** (wrap `shutil.which`/`subprocess.run`).  
- `user_input(var_name, prompt, default, description)` – prompts only if `$var_name` unset, feeding result back into environment. Inputs: indirection via nameref; output stored in shell variable. External reliance: `read`. Python lift: **Easy** (dict-backed config).  
- `wait_for_jobs()` – throttles background jobs to `2*nproc`. Inputs: none; uses `jobs -p`. Side effect: blocks until enough jobs finish. External reliance: `jobs`, `nproc`. Python lift: **Moderate** (needs async executor or semaphore).  
- `ProgressBar(current, total)` – purely cosmetic progress meter. Inputs: counts. External: terminal control codes. Python lift: **Optional/Easy**, but per requirement UI fluff can be skipped.  
- `write_hash(predicate, path, gid, out_file)` – short md5 digests for model id & path; appends CSV rows. Inputs: predicate signature + filesystem path. Side effects: writes to scratch csv. External reliance: `md5sum`. Python lift: **Easy** (hashlib).  
- `resolve_parental(...)` – nested helper invoked per parented model; recursively walks parent JSONs (via repeated `jq` loads) until `elements`, `textures`, and `display` exist or bail. Maintains temp files under `scratch_files/<gid>` to reuse data. External reliance: repeated `jq`, filesystem checks, optional `cp`. Complexity: **High** (json graph traversal, concurrency, heavy jq).  
- `generate_atlas(index)` – invoked per sprite sheet; builds the texture list via `jq`, then runs `spritesheet-js`. External reliance: Node CLI, `spritesheet-js`. Complexity: **High** due to third-party CLI and `.json` merging.  
- `convert_model(...)` – largest helper; selects atlas, emits Bedrock models, animations, attachables, block/item definitions with multiple `jq` programs and filesystem writes, plus progress updates. External reliance: `jq`, `mkdir`, `cp`, `sponge`. Complexity: **Very High** (core business logic).  
- `consolidate_files(target_dir)` – optional renamer that flattens nested directories if `rename_model_files=true`; relies on multiple `find` loops and moves. External reliance: `find`, `mv`. Complexity: **Medium** because of filesystem mutation; Python port doable but less urgent.  
- `write_id_hash(predicate_signature, icon_path, out_file)` – md5 shortening for sprite overrides; similar to `write_hash`. Python lift: **Easy** (pure hashing).  

**Implicit Workflow Stages (treat as pseudo-functions)**  
1. **Argument guard & flag parsing** – ensures resource pack argument exists, handles `getopts`. Inputs: `$1`, optional flags. Output: initial variables. Complexity: Easy; Python mapping via `argparse`.  
2. **ULimit override & warning banner** – optional stack/ARG size boost and big warning print. Inputs: `disable_ulimit`, `warn`. Output: user acknowledgement. Complexity: Easy but mostly UX (can skip TTY art).  
3. **Dependency gating** – sequential `dependency_check` calls for `jq`, `sponge`, `spritesheet-js` etc. Inputs: binary names. Output: exit early if missing. Complexity: Easy.  
4. **Interactive config prompts** – `user_input` for merge target, materials, fallback URL. Inputs: defaults; output: final config values. Complexity: Easy.  
5. **Pack extraction & validation** – unzip Java pack, ensure `pack.mcmeta` and `assets/minecraft/models/item` exist. Inputs: zip path. Output: unpacked tree. Complexity: Medium (filesystem + error-handling).  
6. **Fallback asset acquisition** – optional downloads via `curl`, `unzip`, merges fallback or provided assets, generates placeholder texture, runs ImageMagick cropping. External heavy reliance on CLI tools. Complexity: Hard (I/O + binary deps).  
7. **Predicate/config generation** – massive `jq` pipeline that ingests model overrides, geyser mappings and builds `config.json`, `hashmap.json`, parent listings. Inputs: JSON models. Outputs: normalized config. Complexity: Very High; replacing requires porting all jq logic to Python JSON handling (but aligns with the “jq-heavy pipelines → Python” hint).  
8. **Parent resolution sweep** – iterates `resolve_parental` over each model, determining textures/displays and filtering unsupported models. Inputs: `config.json`, actual model files. Outputs: updated configs + texture copies. Complexity: High (graph traversal).  
9. **Texture atlas generation** – builds texture unions with `jq`, then loops `generate_atlas` to run `spritesheet-js` and update `terrain_texture.json`. External CLI plus concurrency. Complexity: High.  
10. **Model conversion & asset emission** – loops `convert_model`, generating Bedrock models, behaviors, attachables, animations, and updating config-synced state. Inputs: final config entry. Outputs: numerous JSON files per item plus progress. Complexity: Very High (core logic).  
11. **Localization, image normalization, optional file consolidation** – writes lang files via `jq`, runs `mogrify`, optionally renames assets. Complexity: Medium (I/O).  
12. **Pack merging & Geyser mapping** – merges existing Bedrock packs if provided, writes `geyser_mappings.json`, optional sprite overrides. Inputs: merge zip, `sprites.json`. Complexity: Medium–High (JSON merging).  
13. **Cleanup & packaging** – removes temporary assets, optionally archives scratch, produces multiple `.mcpack/.mcaddon` archives, reorganizes outputs. Inputs: `target` dirs. Outputs: packaged artifacts. Complexity: Medium (filesystem + `zip` CLI).  

**Python “Easy Lift” Targets**  
The low-complexity helpers and early workflow stages are prime for initial reimplementation because they rely mostly on stdout, `subprocess`, and filesystem operations already available in Python’s standard library. Higher stages (`resolve_parental`, `generate_atlas`, `convert_model`) should wait until the JSON transformation plan is established (they’re tightly coupled to the jq programs and external tools).

## Python Converter

A Python implementation of the converter is available as `converter.py`. It mirrors the functionality of `converter.sh` but offers better error handling and maintainability.

### Usage

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
