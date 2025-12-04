from pathlib import Path
import math
from PIL import Image

def is_bedrock_glyph(glyph_name: str) -> bool:
    """
    Determines if the given glyph name corresponds to a Bedrock edition glyph.

    Args:
        glyph_name (str): The name of the glyph to check.
    Returns:
        bool: True if the glyph is a Bedrock edition glyph, False otherwise.
    """
    return ord(glyph_name[0]) >= 0xE000 and ord(glyph_name[0]) <= 0xF8FF

def generate_bedrock_glyph_font_file(
    pack_root: Path,
    font_file: Path,
    glyphs: dict[str, str]
) -> None:
    """
    Generates a Bedrock edition glyph font file.

    Args:
        pack_root (Path): The root path of the extracted Java pack.
        font_file (Path): The path to the font file to generate.
        glyphs (Dict[str, str]): A dictionary of char_id -> texture_path.
    """
    # 1. Resolve paths and determine dimensions
    resolved_textures = {}
    max_w, max_h = 0, 0
    
    for char_id, tex_path in glyphs.items():
        # Resolve texture path: namespace:path/to/tex -> assets/namespace/textures/path/to/tex.png
        if ":" in tex_path:
            namespace, path = tex_path.split(":", 1)
        else:
            namespace, path = "minecraft", tex_path
            
        if not path.endswith(".png"):
            path += ".png"
            
        abs_path = pack_root / "assets" / namespace / "textures" / path
        
        if abs_path.exists():
            try:
                with Image.open(abs_path) as img:
                    w, h = img.size
                    max_w = max(max_w, w)
                    max_h = max(max_h, h)
                    resolved_textures[char_id] = abs_path
            except Exception as e:
                print(f"Failed to read texture {abs_path}: {e}")
        else:
            print(f"Texture not found: {abs_path}")

    if not resolved_textures:
        return

    # 2. Calculate sheet dimensions (Power of 2)
    # Determine the largest dimension to ensure square cells
    max_dim = max(max_w, max_h)
    raw_sheet_size = max_dim * 16
    
    # Calculate next power of 2 for the whole sheet
    sheet_size = 2 ** math.ceil(math.log2(raw_sheet_size)) if raw_sheet_size > 0 else 16
    
    # Ensure minimum size
    sheet_size = max(sheet_size, 16)

    cell_w = sheet_size // 16
    cell_h = sheet_size // 16

    # 3. Create and populate atlas
    atlas = Image.new("RGBA", (sheet_size, sheet_size), (0, 0, 0, 0))
    
    for char_id, abs_path in resolved_textures.items():
        # char_id is hex "XY" where X=row, Y=col
        try:
            row = int(char_id[0], 16)
            col = int(char_id[1], 16)
            
            x = col * cell_w
            y = row * cell_h
            
            with Image.open(abs_path) as img:
                # Paste at top-left of the cell
                atlas.paste(img, (x, y))
        except Exception as e:
            print(f"Error processing glyph {char_id}: {e}")

    # 4. Save
    font_file.parent.mkdir(parents=True, exist_ok=True)
    atlas.save(font_file)