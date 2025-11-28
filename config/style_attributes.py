"""
Style Attributes Module
=======================
Comprehensive collection of style attributes for table rendering.
This file contains various options for all styling aspects that can be
randomly selected and combined based on user requirements.
"""

from typing import Dict, List, Any
from dataclasses import dataclass, field


# =============================================================================
# BORDER ATTRIBUTES
# =============================================================================

BORDER_STYLES = {
    'full': {
        'description': 'All borders visible',
        'style': 'border',
        'remove_row_borders': False,
        'remove_col_borders': False,
        'remove_inner_borders': False,
        'keep_outer_border': True,
        'keep_header_row_border': True,
        'keep_colspan_col_borders': True,
    },
    'borderless': {
        'description': 'No borders',
        'style': 'borderless',
        'remove_row_borders': True,
        'remove_col_borders': True,
        'remove_inner_borders': True,
        'keep_outer_border': False,
        'keep_header_row_border': False,
        'keep_colspan_col_borders': False,
    },
    'outer_only': {
        'description': 'Only outer borders, no inner borders',
        'style': 'partly-borderless',
        'remove_row_borders': True,
        'remove_col_borders': True,
        'remove_inner_borders': True,
        'keep_outer_border': True,
        'keep_header_row_border': False,
        'keep_colspan_col_borders': False,
    },
    'horizontal_only': {
        'description': 'Only horizontal (row) borders',
        'style': 'partly-borderless',
        'remove_row_borders': False,
        'remove_col_borders': True,
        'remove_inner_borders': False,
        'keep_outer_border': True,
        'keep_header_row_border': True,
        'keep_colspan_col_borders': False,
    },
    'vertical_only': {
        'description': 'Only vertical (column) borders',
        'style': 'partly-borderless',
        'remove_row_borders': True,
        'remove_col_borders': False,
        'remove_inner_borders': False,
        'keep_outer_border': True,
        'keep_header_row_border': False,
        'keep_colspan_col_borders': True,
    },
    'header_border_only': {
        'description': 'Borders only for header rows',
        'style': 'partly-borderless',
        'remove_row_borders': True,
        'remove_col_borders': True,
        'remove_inner_borders': True,
        'keep_outer_border': False,
        'keep_header_row_border': True,
        'keep_colspan_col_borders': False,
    },
    'header_with_outer': {
        'description': 'Outer borders plus header borders',
        'style': 'partly-borderless',
        'remove_row_borders': True,
        'remove_col_borders': True,
        'remove_inner_borders': True,
        'keep_outer_border': True,
        'keep_header_row_border': True,
        'keep_colspan_col_borders': False,
    },
    'colspan_aware': {
        'description': 'Keep column borders for colspan cells',
        'style': 'partly-borderless',
        'remove_row_borders': True,
        'remove_col_borders': True,
        'remove_inner_borders': False,
        'keep_outer_border': True,
        'keep_header_row_border': True,
        'keep_colspan_col_borders': True,
    },
}

BORDER_WIDTHS = ['1px', '2px', '3px', '4px', '5px']

BORDER_COLORS = [
    # Basic colors
    'black', 'white', 'gray', 'darkgray', 'lightgray',
    # Professional colors
    '#000000', '#333333', '#444444', '#555555', '#666666', '#777777', '#888888', '#999999',
    # Blue tones
    '#1a237e', '#283593', '#303f9f', '#3949ab', '#3f51b5', '#5c6bc0', '#7986cb', '#9fa8da',
    '#0d47a1', '#1565c0', '#1976d2', '#1e88e5', '#2196f3', '#42a5f5',
    # Green tones
    '#1b5e20', '#2e7d32', '#388e3c', '#43a047', '#4caf50', '#66bb6a',
    # Red tones
    '#b71c1c', '#c62828', '#d32f2f', '#e53935', '#f44336', '#ef5350',
    # Warm tones
    '#bf360c', '#e65100', '#ef6c00', '#f57c00', '#fb8c00',
    # Neutral professional
    '#212121', '#424242', '#616161', '#757575', '#9e9e9e', '#bdbdbd',
]

# =============================================================================
# BACKGROUND COLOR ATTRIBUTES
# =============================================================================

BACKGROUND_PATTERNS = ['none', 'header', 'even-odd', 'first-last', 'striped', 'random', 'checkerboard', 'column-based']

BACKGROUND_COLOR_PALETTES = {
    'neutral': {
        'header_color': '#E0E0E0',
        'even_color': '#FFFFFF',
        'odd_color': '#F5F5F5',
        'first_color': '#EEEEEE',
        'last_color': '#EEEEEE',
        'random_colors': ['#F5F5F5', '#EEEEEE', '#E0E0E0', '#D5D5D5'],
    },
    'blue': {
        'header_color': '#BBDEFB',
        'even_color': '#FFFFFF',
        'odd_color': '#E3F2FD',
        'first_color': '#BBDEFB',
        'last_color': '#90CAF9',
        'random_colors': ['#E3F2FD', '#BBDEFB', '#90CAF9', '#64B5F6'],
    },
    'green': {
        'header_color': '#C8E6C9',
        'even_color': '#FFFFFF',
        'odd_color': '#E8F5E9',
        'first_color': '#C8E6C9',
        'last_color': '#A5D6A7',
        'random_colors': ['#E8F5E9', '#C8E6C9', '#A5D6A7', '#81C784'],
    },
    'warm': {
        'header_color': '#FFECB3',
        'even_color': '#FFFFFF',
        'odd_color': '#FFF8E1',
        'first_color': '#FFECB3',
        'last_color': '#FFE082',
        'random_colors': ['#FFF8E1', '#FFECB3', '#FFE082', '#FFD54F'],
    },
    'purple': {
        'header_color': '#E1BEE7',
        'even_color': '#FFFFFF',
        'odd_color': '#F3E5F5',
        'first_color': '#E1BEE7',
        'last_color': '#CE93D8',
        'random_colors': ['#F3E5F5', '#E1BEE7', '#CE93D8', '#BA68C8'],
    },
    'teal': {
        'header_color': '#B2DFDB',
        'even_color': '#FFFFFF',
        'odd_color': '#E0F2F1',
        'first_color': '#B2DFDB',
        'last_color': '#80CBC4',
        'random_colors': ['#E0F2F1', '#B2DFDB', '#80CBC4', '#4DB6AC'],
    },
    'orange': {
        'header_color': '#FFE0B2',
        'even_color': '#FFFFFF',
        'odd_color': '#FFF3E0',
        'first_color': '#FFE0B2',
        'last_color': '#FFCC80',
        'random_colors': ['#FFF3E0', '#FFE0B2', '#FFCC80', '#FFB74D'],
    },
    'pink': {
        'header_color': '#F8BBD9',
        'even_color': '#FFFFFF',
        'odd_color': '#FCE4EC',
        'first_color': '#F8BBD9',
        'last_color': '#F48FB1',
        'random_colors': ['#FCE4EC', '#F8BBD9', '#F48FB1', '#EC407A'],
    },
    'corporate_blue': {
        'header_color': '#1976D2',
        'even_color': '#FFFFFF',
        'odd_color': '#F5F5F5',
        'first_color': '#1976D2',
        'last_color': '#1565C0',
        'random_colors': ['#FFFFFF', '#F5F5F5', '#E3F2FD'],
    },
    'minimal': {
        'header_color': '#FAFAFA',
        'even_color': '#FFFFFF',
        'odd_color': '#FAFAFA',
        'first_color': '#F5F5F5',
        'last_color': '#F5F5F5',
        'random_colors': ['#FFFFFF', '#FAFAFA', '#F5F5F5'],
    },
}

# =============================================================================
# FONT ATTRIBUTES
# =============================================================================

FONT_FAMILIES = [
    # Serif fonts
    'Times New Roman, Times, serif',
    'Georgia, serif',
    'Palatino Linotype, Book Antiqua, Palatino, serif',
    'Cambria, serif',
    'Garamond, serif',
    'Book Antiqua, serif',
    
    # Sans-serif fonts
    'Arial, Helvetica, sans-serif',
    'Helvetica Neue, Helvetica, Arial, sans-serif',
    'Verdana, Geneva, sans-serif',
    'Tahoma, Geneva, sans-serif',
    'Trebuchet MS, sans-serif',
    'Calibri, sans-serif',
    'Segoe UI, sans-serif',
    'Roboto, sans-serif',
    'Open Sans, sans-serif',
    'Lato, sans-serif',
    
    # Monospace fonts
    'Courier New, Courier, monospace',
    'Consolas, Monaco, monospace',
    'Lucida Console, Monaco, monospace',
]

FONT_SIZES = [
    '12px', '14px', '16px', '18px', '20px', '22px', '24px',
    '26px', '28px', '30px', '32px', '34px', '36px', '38px',
    '40px', '42px', '44px', '48px', '52px', '56px', '60px'
]

FONT_WEIGHTS = ['normal', 'bold', 'lighter', 'bolder', '100', '200', '300', '400', '500', '600', '700', '800', '900']

FONT_STYLES = ['normal', 'italic', 'oblique']

FONT_TRANSFORMS = ['none', 'uppercase', 'lowercase', 'capitalize']

FONT_COLORS = [
    # Basic colors
    'black', 'white', 'gray', 'darkgray',
    # Professional colors
    '#000000', '#111111', '#222222', '#333333', '#444444', '#555555',
    # Blue tones
    '#1a237e', '#283593', '#303f9f', '#0d47a1', '#1565c0', '#1976d2',
    # Green tones
    '#1b5e20', '#2e7d32', '#388e3c', '#004d40',
    # Red/brown tones
    '#b71c1c', '#c62828', '#bf360c', '#3e2723',
    # Neutral
    '#212121', '#424242', '#616161', '#757575',
]

# =============================================================================
# ALIGNMENT ATTRIBUTES
# =============================================================================

HORIZONTAL_ALIGNMENTS = ['left', 'center', 'right', 'justify']

VERTICAL_ALIGNMENTS = ['top', 'middle', 'bottom', 'baseline']

# Common column alignment patterns
COLUMN_ALIGNMENT_PATTERNS = {
    'first_left_rest_center': {
        0: 'left',
        'default': 'center',
    },
    'first_left_rest_right': {
        0: 'left',
        'default': 'right',
    },
    'all_left': {
        'default': 'left',
    },
    'all_center': {
        'default': 'center',
    },
    'all_right': {
        'default': 'right',
    },
    'alternating': {
        'even': 'left',
        'odd': 'right',
    },
    'numbers_right': {
        0: 'left',
        1: 'center',
        2: 'center',
        'default': 'right',
    },
}

# =============================================================================
# SPACING ATTRIBUTES
# =============================================================================

PADDING_VALUES = [
    '2px', '4px', '5px', '6px', '8px', '10px', '12px', '14px', '16px', '18px', '20px',
    '2px 4px', '4px 8px', '6px 12px', '8px 16px', '10px 20px',
    '4px 8px 4px 8px', '6px 10px 6px 10px', '8px 12px 8px 12px',
]

CELL_SPACING_VALUES = ['0', '1px', '2px', '3px', '4px', '5px']

LINE_HEIGHT_VALUES = ['1.0', '1.2', '1.3', '1.4', '1.5', '1.6', '1.8', '2.0']

ROW_HEIGHT_VALUES = [
    'auto', '30px', '35px', '40px', '45px', '50px', '55px', '60px',
    '70px', '80px', '90px', '100px'
]

COLUMN_WIDTH_VALUES = [
    'auto', '50px', '60px', '70px', '80px', '90px', '100px',
    '120px', '140px', '160px', '180px', '200px', '250px', '300px',
    '10%', '15%', '20%', '25%', '30%', '40%', '50%'
]

# =============================================================================
# LINE BREAK CONFIGURATION
# =============================================================================

LINE_BREAK_CONFIGS = {
    'none': {
        'enabled': False,
        'probability': 0.0,
        'min_words_before_break': 999,
        'max_breaks_per_cell': 0,
    },
    'light': {
        'enabled': True,
        'probability': 0.1,
        'min_words_before_break': 4,
        'max_breaks_per_cell': 1,
    },
    'moderate': {
        'enabled': True,
        'probability': 0.2,
        'min_words_before_break': 3,
        'max_breaks_per_cell': 2,
    },
    'heavy': {
        'enabled': True,
        'probability': 0.35,
        'min_words_before_break': 2,
        'max_breaks_per_cell': 3,
    },
    'content_aware': {
        'enabled': True,
        'probability': 0.25,
        'min_words_before_break': 3,
        'max_breaks_per_cell': 2,
        'break_on_punctuation': True,
        'prefer_natural_breaks': True,
    },
}

# =============================================================================
# STYLE PRESETS (Complete Configurations)
# =============================================================================

STYLE_PRESETS = {
    'default': {
        'description': 'Standard table style with borders and header highlighting',
        'border': BORDER_STYLES['full'],
        'background': BACKGROUND_COLOR_PALETTES['neutral'],
        'font_family': 'Times New Roman, Times, serif',
        'font_size': '36px',
        'alignment': 'center',
        'padding': '8px',
    },
    'modern': {
        'description': 'Clean modern style with subtle colors',
        'border': BORDER_STYLES['horizontal_only'],
        'background': BACKGROUND_COLOR_PALETTES['minimal'],
        'font_family': 'Segoe UI, sans-serif',
        'font_size': '32px',
        'alignment': 'left',
        'padding': '12px',
    },
    'corporate': {
        'description': 'Professional corporate style',
        'border': BORDER_STYLES['full'],
        'background': BACKGROUND_COLOR_PALETTES['corporate_blue'],
        'font_family': 'Arial, Helvetica, sans-serif',
        'font_size': '28px',
        'alignment': 'center',
        'padding': '10px',
    },
    'minimal': {
        'description': 'Minimalist style with outer borders only',
        'border': BORDER_STYLES['outer_only'],
        'background': BACKGROUND_COLOR_PALETTES['minimal'],
        'font_family': 'Helvetica Neue, Helvetica, Arial, sans-serif',
        'font_size': '30px',
        'alignment': 'left',
        'padding': '16px',
    },
    'striped': {
        'description': 'Alternating row colors for readability',
        'border': BORDER_STYLES['horizontal_only'],
        'background': BACKGROUND_COLOR_PALETTES['neutral'],
        'background_pattern': 'striped',
        'font_family': 'Verdana, Geneva, sans-serif',
        'font_size': '28px',
        'alignment': 'left',
        'padding': '10px',
    },
    'colorful': {
        'description': 'Vibrant colors for visual appeal',
        'border': BORDER_STYLES['full'],
        'background': BACKGROUND_COLOR_PALETTES['blue'],
        'font_family': 'Tahoma, Geneva, sans-serif',
        'font_size': '32px',
        'alignment': 'center',
        'padding': '8px',
    },
    'academic': {
        'description': 'Traditional academic paper style',
        'border': BORDER_STYLES['header_with_outer'],
        'background': BACKGROUND_COLOR_PALETTES['neutral'],
        'font_family': 'Times New Roman, Times, serif',
        'font_size': '24px',
        'alignment': 'center',
        'padding': '6px',
    },
    'financial': {
        'description': 'Financial report style with right-aligned numbers',
        'border': BORDER_STYLES['full'],
        'background': BACKGROUND_COLOR_PALETTES['neutral'],
        'font_family': 'Calibri, sans-serif',
        'font_size': '26px',
        'alignment': 'right',
        'padding': '8px',
    },
}

# =============================================================================
# RANDOM SELECTION WEIGHTS
# =============================================================================

# Define weights for random selection (higher = more likely)
RANDOM_WEIGHTS = {
    'border_styles': {
        'full': 30,
        'borderless': 10,
        'outer_only': 15,
        'horizontal_only': 20,
        'vertical_only': 5,
        'header_border_only': 10,
        'header_with_outer': 15,
        'colspan_aware': 5,
    },
    'background_patterns': {
        'none': 10,
        'header': 30,
        'even-odd': 25,
        'first-last': 5,
        'striped': 20,
        'random': 5,
        'checkerboard': 3,
        'column-based': 2,
    },
    'font_categories': {
        'serif': 40,
        'sans-serif': 50,
        'monospace': 10,
    },
    'line_breaks': {
        'none': 50,
        'light': 25,
        'moderate': 15,
        'heavy': 5,
        'content_aware': 5,
    },
}


def get_font_category(font_family: str) -> str:
    """Determine the category of a font family."""
    font_lower = font_family.lower()
    if 'monospace' in font_lower or 'courier' in font_lower or 'consolas' in font_lower:
        return 'monospace'
    elif 'serif' in font_lower and 'sans' not in font_lower:
        return 'serif'
    else:
        return 'sans-serif'


def get_fonts_by_category(category: str) -> List[str]:
    """Get fonts from a specific category."""
    return [f for f in FONT_FAMILIES if get_font_category(f) == category]
