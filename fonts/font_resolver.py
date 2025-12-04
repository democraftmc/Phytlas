def is_bedrock_glyph(glyph_name: str) -> bool:
    """
    Determines if the given glyph name corresponds to a Bedrock edition glyph.

    Args:
        glyph_name (str): The name of the glyph to check.
    Returns:
        bool: True if the glyph is a Bedrock edition glyph, False otherwise.
    """
    return ord(glyph_name[0]) >= 0xE000 and ord(glyph_name[0]) <= 0xF8FF