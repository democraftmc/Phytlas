"""Converter modules for model transformation.

Provides separate modules for 2D and 3D item conversion:
- item_2d.py: 2D sprite/generated item conversion
- item_3d.py: 3D model item conversion  
- model_converter.py: Dispatcher that routes to appropriate converter
"""

from .parental import resolve_parental
from .item_2d import convert_2d_item
from .item_3d import convert_3d_item, create_3d_item_definition, create_3d_attachable_definition
from .geometry import build_geometry, round_value

__all__ = [
    # Main entry points
    "resolve_parental",
    # 2D item conversion (separate from 3D)
    "convert_2d_item",
    # 3D item conversion (separate from 2D)
    "convert_3d_item",
    "create_3d_attachable_definition",
    # Geometry utilities
    "build_geometry",
    "round_value",
]
