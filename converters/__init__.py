"""Converter modules for model transformation.

Provides separate modules for 2D and 3D item conversion:
- item_2d.py: 2D sprite/generated item conversion
- item_3d.py: 3D model item conversion  
- model_converter.py: Dispatcher that routes to appropriate converter
"""

from .parental import resolve_parental
from .item_2d import convert_2d_item
from .item_3d import convert_3d_item, create_3d_attachable_definition
from .geometry import build_geometry, round_value

__all__ = [
    "resolve_parental",
    "convert_2d_item",
    "convert_3d_item",
    "create_3d_attachable_definition",
    "build_geometry",
    "round_value",
]
