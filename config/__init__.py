"""
Configuration module for table-generator.
Contains configuration classes for augmentation and styling.
"""

from .augment_config import AugmentConfig
from .style_config import (
    StyleConfig,
    BorderConfig,
    BackgroundConfig,
    FontConfig,
    AlignmentConfig,
    SpacingConfig,
    random_select_style,
    generate_multiple_styles,
    list_available_options
)
from .style_attributes import (
    BORDER_STYLES,
    BORDER_WIDTHS,
    BORDER_COLORS,
    BACKGROUND_PATTERNS,
    BACKGROUND_COLOR_PALETTES,
    FONT_FAMILIES,
    FONT_SIZES,
    FONT_WEIGHTS,
    FONT_STYLES,
    FONT_TRANSFORMS,
    FONT_COLORS,
    HORIZONTAL_ALIGNMENTS,
    VERTICAL_ALIGNMENTS,
    COLUMN_ALIGNMENT_PATTERNS,
    PADDING_VALUES,
    CELL_SPACING_VALUES,
    LINE_HEIGHT_VALUES,
    ROW_HEIGHT_VALUES,
    COLUMN_WIDTH_VALUES,
    LINE_BREAK_CONFIGS,
    STYLE_PRESETS,
    RANDOM_WEIGHTS
)

__all__ = [
    # Configuration classes
    'AugmentConfig',
    'StyleConfig',
    'BorderConfig',
    'BackgroundConfig',
    'FontConfig',
    'AlignmentConfig',
    'SpacingConfig',
    
    # Style selection functions
    'random_select_style',
    'generate_multiple_styles',
    'list_available_options',
    
    # Style attributes
    'BORDER_STYLES',
    'BORDER_WIDTHS',
    'BORDER_COLORS',
    'BACKGROUND_PATTERNS',
    'BACKGROUND_COLOR_PALETTES',
    'FONT_FAMILIES',
    'FONT_SIZES',
    'FONT_WEIGHTS',
    'FONT_STYLES',
    'FONT_TRANSFORMS',
    'FONT_COLORS',
    'HORIZONTAL_ALIGNMENTS',
    'VERTICAL_ALIGNMENTS',
    'COLUMN_ALIGNMENT_PATTERNS',
    'PADDING_VALUES',
    'CELL_SPACING_VALUES',
    'LINE_HEIGHT_VALUES',
    'ROW_HEIGHT_VALUES',
    'COLUMN_WIDTH_VALUES',
    'LINE_BREAK_CONFIGS',
    'STYLE_PRESETS',
    'RANDOM_WEIGHTS'
]
