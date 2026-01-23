from pathlib import Path
import json

def get_sounds_from_pack(java_root : Path) -> dict[str, list[str]]:
    """
    Retrieve a list of sound files from the default sound pack.

    Returns:
        list: A list of sound file names.
    """
    namespaces_dir = java_root / "assets"
    sound_files: dict[str, list[str]] = {}
    if namespaces_dir.exists():
        for namespace in namespaces_dir.iterdir():
            if (namespace / "sounds.json").exists():
                sound_files.update(get_sounds_from_namespace(namespace))
    return sound_files

def get_sounds_from_namespace(namespace : Path) -> dict[str, list[str]]:
    """
    Retrieve a list of sound files associated with a given namespace.

    Args:
        namespace (str): The namespace to retrieve sounds from.

    Returns:
        list: A list of sound file names.
    """
    response: dict[str, list[str]] = {}
    raw_sounds = (namespace / "sounds.json").open("r").read()
    raw_sounds = json.loads(raw_sounds)
    namespace_name = namespace.name
    for sound in raw_sounds.keys():
        response[f"{namespace_name}:{sound}"] = raw_sounds[sound]
    return response


def create_sound_mapping(mappings : dict[str, list[str]], output_path: Path):
    """
    Create a mapping of sound file names to their respective paths.

    Args:
        mappings (dict): A dictionary mapping sound file names to their paths.
        output_path (Path): The path where the mapping file will be saved.

    Returns:
        None. Writes the sound mapping file to disk.
    """

    geyser_json = {
        "format_version": "1.14.0",
        "sound_definitions": mappings
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(geyser_json), encoding="utf-8")

