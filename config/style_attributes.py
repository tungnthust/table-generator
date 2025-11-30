"""
Style Attributes Module
=======================
Comprehensive collection of style attributes for table rendering.
This file contains various options for all styling aspects that can be
randomly selected and combined based on user requirements.

DESIGN PRINCIPLES:
1. Color Contrast: All background/text color combinations ensure readability (WCAG AA minimum)
2. Spacing Coherence: Font size, padding, and line-height are proportionally matched
3. Alignment Consistency: Alignment rules prevent hard-to-read combinations
4. Professional Combinations: Style combinations reflect real document design patterns
"""

from typing import Dict, List


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
        # Alignment constraint: full borders allow any alignment
        'alignment_constraint': None,
    },
    'borderless': {
        'description': 'No borders - requires consistent alignment and good spacing',
        'style': 'borderless',
        'remove_row_borders': True,
        'remove_col_borders': True,
        'remove_inner_borders': True,
        'keep_outer_border': False,
        'keep_header_row_border': False,
        'keep_colspan_col_borders': False,
        # Alignment constraint: borderless needs consistent alignment to separate columns
        'alignment_constraint': 'consistent',  # All columns same alignment
        'min_padding': '12px',  # Needs more padding for visual separation
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
        'alignment_constraint': 'consistent',
        'min_padding': '10px',
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
        # Horizontal borders separate rows, so column alignment can vary but carefully
        'alignment_constraint': 'column_aware',
        'min_padding': '8px',
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
        'alignment_constraint': None,  # Vertical borders separate columns well
    },
    'header_border_only': {
        'description': 'Borders only under header row',
        'style': 'partly-borderless',
        'remove_row_borders': True,
        'remove_col_borders': True,
        'remove_inner_borders': True,
        'keep_outer_border': False,
        'keep_header_row_border': True,
        'keep_colspan_col_borders': False,
        'alignment_constraint': 'consistent',
        'min_padding': '10px',
    },
    'header_with_outer': {
        'description': 'Outer borders plus header borders - academic style',
        'style': 'partly-borderless',
        'remove_row_borders': True,
        'remove_col_borders': True,
        'remove_inner_borders': True,
        'keep_outer_border': True,
        'keep_header_row_border': True,
        'keep_colspan_col_borders': False,
        'alignment_constraint': 'column_aware',
        'min_padding': '8px',
    },
}

# Border widths - grouped by use case
BORDER_WIDTHS_LIGHT = ['1px', '1.5px']
BORDER_WIDTHS_MEDIUM = ['2px', '2.5px']
BORDER_WIDTHS_HEAVY = ['3px', '4px']
BORDER_WIDTHS = BORDER_WIDTHS_LIGHT + BORDER_WIDTHS_MEDIUM + BORDER_WIDTHS_HEAVY

# Border colors - only dark colors that provide good contrast
BORDER_COLORS = [
    # Standard blacks and grays
    '#000000', '#1a1a1a', '#2d2d2d', '#333333', '#404040', '#4d4d4d',
    '#555555', '#666666', '#757575', '#808080',
    # Professional dark blues
    '#1a237e', '#283593', '#303f9f', '#0d47a1', '#1565c0',
    # Professional dark greens
    '#1b5e20', '#2e7d32', '#004d40',
    # Professional dark reds/browns
    '#b71c1c', '#c62828', '#3e2723', '#4e342e',
]


# =============================================================================
# BACKGROUND COLOR ATTRIBUTES WITH CONTRAST-SAFE TEXT COLORS
# =============================================================================

BACKGROUND_PATTERNS = ['none', 'header', 'even-odd', 'striped']
# Removed problematic patterns: 'random', 'checkerboard', 'column-based', 'first-last'
# These can create visual confusion in real documents

# Each palette includes safe text colors that contrast well with backgrounds
BACKGROUND_COLOR_PALETTES = {
    'white_clean': {
        'description': 'Clean white backgrounds - works with any text color',
        'header_color': '#F5F5F5',
        'even_color': '#FFFFFF',
        'odd_color': '#FAFAFA',
        'first_color': '#F5F5F5',
        'last_color': '#F5F5F5',
        'random_colors': ['#FFFFFF', '#FAFAFA', '#F5F5F5'],
        # Safe text colors for this palette (all dark)
        'text_colors': ['#000000', '#1a1a1a', '#2d2d2d', '#333333', '#424242'],
        'header_text_color': '#000000',
    },
    'light_gray': {
        'description': 'Light gray tones - professional and neutral',
        'header_color': '#E0E0E0',
        'even_color': '#FFFFFF',
        'odd_color': '#F5F5F5',
        'first_color': '#EEEEEE',
        'last_color': '#EEEEEE',
        'random_colors': ['#F5F5F5', '#EEEEEE', '#E8E8E8'],
        'text_colors': ['#000000', '#1a1a1a', '#2d2d2d', '#333333'],
        'header_text_color': '#000000',
    },
    'soft_blue': {
        'description': 'Soft blue tones - calming and professional',
        'header_color': '#BBDEFB',
        'even_color': '#FFFFFF',
        'odd_color': '#E3F2FD',
        'first_color': '#BBDEFB',
        'last_color': '#BBDEFB',
        'random_colors': ['#E3F2FD', '#BBDEFB'],
        'text_colors': ['#0d47a1', '#1565c0', '#1a237e', '#1a1a1a', '#000000'],
        'header_text_color': '#0d47a1',
    },
    'soft_green': {
        'description': 'Soft green tones - natural and easy on eyes',
        'header_color': '#C8E6C9',
        'even_color': '#FFFFFF',
        'odd_color': '#E8F5E9',
        'first_color': '#C8E6C9',
        'last_color': '#C8E6C9',
        'random_colors': ['#E8F5E9', '#C8E6C9'],
        'text_colors': ['#1b5e20', '#2e7d32', '#004d40', '#1a1a1a', '#000000'],
        'header_text_color': '#1b5e20',
    },
    'warm_cream': {
        'description': 'Warm cream and beige tones',
        'header_color': '#FFF8E1',
        'even_color': '#FFFFFF',
        'odd_color': '#FFFDE7',
        'first_color': '#FFF8E1',
        'last_color': '#FFF8E1',
        'random_colors': ['#FFFDE7', '#FFF8E1'],
        'text_colors': ['#3e2723', '#4e342e', '#5d4037', '#1a1a1a', '#000000'],
        'header_text_color': '#3e2723',
    },
    'soft_purple': {
        'description': 'Soft purple/lavender tones',
        'header_color': '#E1BEE7',
        'even_color': '#FFFFFF',
        'odd_color': '#F3E5F5',
        'first_color': '#E1BEE7',
        'last_color': '#E1BEE7',
        'random_colors': ['#F3E5F5', '#E1BEE7'],
        'text_colors': ['#4a148c', '#6a1b9a', '#7b1fa2', '#1a1a1a', '#000000'],
        'header_text_color': '#4a148c',
    },
    'corporate_blue': {
        'description': 'Corporate style with blue header',
        'header_color': '#1976D2',
        'even_color': '#FFFFFF',
        'odd_color': '#F5F5F5',
        'first_color': '#1976D2',
        'last_color': '#1976D2',
        'random_colors': ['#FFFFFF', '#F5F5F5'],
        'text_colors': ['#000000', '#1a1a1a', '#2d2d2d'],
        'header_text_color': '#FFFFFF',  # White text on dark blue header
    },
    'corporate_dark': {
        'description': 'Dark corporate header style',
        'header_color': '#37474F',
        'even_color': '#FFFFFF',
        'odd_color': '#ECEFF1',
        'first_color': '#37474F',
        'last_color': '#37474F',
        'random_colors': ['#FFFFFF', '#ECEFF1'],
        'text_colors': ['#000000', '#1a1a1a', '#263238'],
        'header_text_color': '#FFFFFF',
    },
    'teal_accent': {
        'description': 'Teal accent color scheme',
        'header_color': '#B2DFDB',
        'even_color': '#FFFFFF',
        'odd_color': '#E0F2F1',
        'first_color': '#B2DFDB',
        'last_color': '#B2DFDB',
        'random_colors': ['#E0F2F1', '#B2DFDB'],
        'text_colors': ['#004d40', '#00695c', '#00796b', '#1a1a1a', '#000000'],
        'header_text_color': '#004d40',
    },
    'minimal_white': {
        'description': 'Ultra minimal - almost no color variation',
        'header_color': '#FAFAFA',
        'even_color': '#FFFFFF',
        'odd_color': '#FFFFFF',
        'first_color': '#FAFAFA',
        'last_color': '#FAFAFA',
        'random_colors': ['#FFFFFF'],
        'text_colors': ['#000000', '#1a1a1a', '#333333'],
        'header_text_color': '#000000',
    },
}


# =============================================================================
# FONT ATTRIBUTES - ORGANIZED BY USE CASE
# =============================================================================

# Fonts categorized by type
FONTS_SERIF = [
    'Times New Roman, Times, serif',
    'Georgia, serif',
    'Palatino Linotype, Book Antiqua, Palatino, serif',
    'Cambria, serif',
    'Garamond, serif',
]

FONTS_SANS_SERIF = [
    'Arial, Helvetica, sans-serif',
    'Helvetica Neue, Helvetica, Arial, sans-serif',
    'Verdana, Geneva, sans-serif',
    'Tahoma, Geneva, sans-serif',
    'Calibri, sans-serif',
    'Segoe UI, sans-serif',
]

FONTS_MONOSPACE = [
    'Courier New, Courier, monospace',
    'Consolas, Monaco, monospace',
]

FONT_FAMILIES = FONTS_SERIF + FONTS_SANS_SERIF + FONTS_MONOSPACE

# Weighted font selection - favor Times New Roman, then Arial, then others
# Each font repeated by its weight factor
FONTS_WEIGHTED = (
    ['Times New Roman, Times, serif'] * 35 +           # 35% - Most common
    ['Arial, Helvetica, sans-serif'] * 25 +            # 25% - Second most common
    ['Georgia, serif'] * 8 +                           # 8%
    ['Calibri, sans-serif'] * 7 +                      # 7%
    ['Verdana, Geneva, sans-serif'] * 5 +              # 5%
    ['Helvetica Neue, Helvetica, Arial, sans-serif'] * 5 +  # 5%
    ['Segoe UI, sans-serif'] * 4 +                     # 4%
    ['Tahoma, Geneva, sans-serif'] * 3 +               # 3%
    ['Palatino Linotype, Book Antiqua, Palatino, serif'] * 3 +  # 3%
    ['Cambria, serif'] * 2 +                           # 2%
    ['Garamond, serif'] * 2 +                          # 2%
    ['Courier New, Courier, monospace'] * 1            # 1%
)

# Font size tiers with corresponding spacing recommendations
# Each tier includes: sizes, recommended padding range, recommended line-height range
# FAVOR TIGHTER SPACING for realistic document look
FONT_SIZE_TIERS = {
    'small': {
        'sizes': ['14px', '16px', '18px'],
        'padding_range': ('3px', '5px'),       # Tight for small text
        'line_height_range': ('1.2', '1.35'),  # Compact
        'description': 'Small text - dense information tables',
    },
    'medium': {
        'sizes': ['20px', '22px', '24px', '26px'],
        'padding_range': ('5px', '8px'),       # Normal
        'line_height_range': ('1.25', '1.4'),  # Standard
        'description': 'Medium text - standard tables',
    },
    'large': {
        'sizes': ['28px', '30px', '32px', '34px'],
        'padding_range': ('6px', '10px'),      # Slightly more
        'line_height_range': ('1.3', '1.45'),  # Standard-ish
        'description': 'Large text - prominent tables',
    },
    'xlarge': {
        'sizes': ['36px', '38px', '40px'],
        'padding_range': ('8px', '12px'),      # Reasonable
        'line_height_range': ('1.35', '1.5'),  # Not too spacious
        'description': 'Extra large text - hero tables, presentations',
    },
}

# Flat list for backward compatibility
FONT_SIZES = []
for tier in FONT_SIZE_TIERS.values():
    FONT_SIZES.extend(tier['sizes'])

FONT_WEIGHTS = ['normal', 'bold']  # Simplified - only commonly used weights

FONT_STYLES = ['normal', 'italic']  # Simplified

FONT_TRANSFORMS = ['none', 'uppercase', 'capitalize']  # Removed lowercase - rarely used

# Font colors now depend on background - see BACKGROUND_COLOR_PALETTES
FONT_COLORS = [
    '#000000', '#1a1a1a', '#2d2d2d', '#333333', '#424242', '#555555',
]


# =============================================================================
# ALIGNMENT ATTRIBUTES - WITH REALISTIC CONSTRAINTS
# =============================================================================

HORIZONTAL_ALIGNMENTS = ['left', 'center', 'right']  # Removed 'justify' - problematic in tables

VERTICAL_ALIGNMENTS = ['top', 'middle', 'bottom']  # Removed 'baseline' - rarely used in tables

# Realistic column alignment patterns
# These patterns reflect how real documents align table columns
COLUMN_ALIGNMENT_PATTERNS = {
    'all_left': {
        'description': 'All columns left-aligned - good for text-heavy tables',
        'pattern': 'uniform',
        'default_align': 'left',
        'works_with_borderless': True,
    },
    'all_center': {
        'description': 'All columns centered - good for short content',
        'pattern': 'uniform',
        'default_align': 'center',
        'works_with_borderless': True,
    },
    'all_right': {
        'description': 'All columns right-aligned - good for numeric tables',
        'pattern': 'uniform',
        'default_align': 'right',
        'works_with_borderless': True,
    },
    'left_with_right_numbers': {
        'description': 'Text left, numbers right - standard data table pattern',
        'pattern': 'first_different',
        'first_align': 'left',
        'rest_align': 'right',
        'works_with_borderless': False,  # Needs column borders
    },
    'left_with_center_header': {
        'description': 'Header centered, data left-aligned',
        'pattern': 'header_different',
        'header_align': 'center',
        'data_align': 'left',
        'works_with_borderless': True,
    },
}


# =============================================================================
# SPACING ATTRIBUTES - COHERENT GROUPINGS
# =============================================================================

# Padding values grouped by intensity
# FAVOR REALISTIC VALUES: Most real documents use tight to medium padding
PADDING_TIGHT = ['3px', '4px', '5px']       # Compact tables
PADDING_NORMAL = ['6px', '7px', '8px']      # Standard - MOST COMMON
PADDING_MEDIUM = ['9px', '10px', '11px']    # Slightly spacious
PADDING_GENEROUS = ['12px', '14px', '16px'] # Very spacious - less common

PADDING_VALUES = PADDING_TIGHT + PADDING_NORMAL + PADDING_MEDIUM + PADDING_GENEROUS

# Symmetric padding weights - FAVOR NORMAL/TIGHT values for realistic look
# Weighted list: normal values repeated more
PADDING_SYMMETRIC_WEIGHTED = (
    PADDING_TIGHT * 2 +      # 20% tight
    PADDING_NORMAL * 5 +     # 50% normal (most common)
    PADDING_MEDIUM * 2 +     # 20% medium
    PADDING_GENEROUS * 1     # 10% generous
)

# Simple list for compatibility
PADDING_SYMMETRIC = ['4px', '5px', '6px', '7px', '8px', '10px', '12px']

# Asymmetric padding - rarely used in real tables
PADDING_ASYMMETRIC = ['4px 6px', '5px 8px', '6px 10px']

CELL_SPACING_VALUES = ['0']  # Always 0 - most realistic

# Line height values - FAVOR NORMAL/TIGHT for realistic look
# 1.2-1.4 is standard, 1.5+ is spacious
LINE_HEIGHT_VALUES = ['1.2', '1.25', '1.3', '1.35', '1.4']
LINE_HEIGHT_TIGHT = ['1.15', '1.2', '1.25']
LINE_HEIGHT_NORMAL = ['1.3', '1.35', '1.4']      # Most common
LINE_HEIGHT_SPACIOUS = ['1.45', '1.5', '1.6']    # Less common

# Weighted list for realistic selection
LINE_HEIGHT_WEIGHTED = (
    LINE_HEIGHT_TIGHT * 2 +     # 20% tight
    LINE_HEIGHT_NORMAL * 6 +    # 60% normal (most common)
    LINE_HEIGHT_SPACIOUS * 2    # 20% spacious
)

# Row heights - should be proportional to font size + padding
ROW_HEIGHT_VALUES = ['auto']  # Let browser calculate - most realistic

# Column widths - should be auto or percentage based
COLUMN_WIDTH_VALUES = ['auto']  # Let browser calculate


# =============================================================================
# LINE BREAK CONFIGURATION
# =============================================================================

LINE_BREAK_CONFIGS = {
    'none': {
        'enabled': False,
        'description': 'No line breaks - content stays on single line',
    },
    'light': {
        'enabled': True,
        'description': 'Light line breaks - only break very long content',
        # Width-based breaking will handle the logic
    },
    'moderate': {
        'enabled': True,
        'description': 'Moderate line breaks - break when exceeding column width',
    },
    'content_aware': {
        'enabled': True,
        'description': 'Content-aware breaks - intelligently break based on text width vs column width',
    },
}


# =============================================================================
# COHERENT STYLE PROFILES
# =============================================================================

# These profiles ensure all style attributes work well together
STYLE_PROFILES = {
    'compact_data': {
        'description': 'Compact style for data-dense tables',
        'font_size_tier': 'small',
        'padding_category': 'light',
        'line_height': '1.3',
        'border_style': 'full',
        'alignment': 'left',
    },
    'standard_document': {
        'description': 'Standard document table',
        'font_size_tier': 'medium',
        'padding_category': 'medium',
        'line_height': '1.4',
        'border_style': 'full',
        'alignment': 'center',
    },
    'spacious_modern': {
        'description': 'Modern spacious tables',
        'font_size_tier': 'medium',
        'padding_category': 'generous',
        'line_height': '1.5',
        'border_style': 'horizontal_only',
        'alignment': 'left',
    },
    'academic_paper': {
        'description': 'Academic paper style',
        'font_size_tier': 'small',
        'padding_category': 'light',
        'line_height': '1.4',
        'border_style': 'header_with_outer',
        'alignment': 'center',
    },
    'presentation': {
        'description': 'Presentation/large display',
        'font_size_tier': 'xlarge',
        'padding_category': 'generous',
        'line_height': '1.5',
        'border_style': 'full',
        'alignment': 'center',
    },
    'minimal_clean': {
        'description': 'Minimal clean design',
        'font_size_tier': 'medium',
        'padding_category': 'generous',
        'line_height': '1.6',
        'border_style': 'borderless',
        'alignment': 'left',  # Consistent alignment required for borderless
    },
}


# =============================================================================
# STYLE PRESETS (Complete Configurations)
# =============================================================================

STYLE_PRESETS = {
    'default': {
        'description': 'Standard table style with borders and header highlighting',
        'border': BORDER_STYLES['full'],
        'background': BACKGROUND_COLOR_PALETTES['light_gray'],
        'background_pattern': 'header',
        'font_family': 'Times New Roman, Times, serif',
        'font_size': '28px',
        'font_color': '#000000',
        'alignment': 'center',
        'padding': '8px',
        'line_height': '1.4',
    },
    'modern': {
        'description': 'Clean modern style with subtle colors',
        'border': BORDER_STYLES['horizontal_only'],
        'background': BACKGROUND_COLOR_PALETTES['minimal_white'],
        'background_pattern': 'none',
        'font_family': 'Segoe UI, sans-serif',
        'font_size': '24px',
        'font_color': '#1a1a1a',
        'alignment': 'left',
        'padding': '12px',
        'line_height': '1.5',
    },
    'corporate': {
        'description': 'Professional corporate style',
        'border': BORDER_STYLES['full'],
        'background': BACKGROUND_COLOR_PALETTES['corporate_blue'],
        'background_pattern': 'header',
        'font_family': 'Arial, Helvetica, sans-serif',
        'font_size': '22px',
        'font_color': '#000000',
        'alignment': 'center',
        'padding': '10px',
        'line_height': '1.4',
    },
    'minimal': {
        'description': 'Minimalist style with clean lines',
        'border': BORDER_STYLES['outer_only'],
        'background': BACKGROUND_COLOR_PALETTES['minimal_white'],
        'background_pattern': 'none',
        'font_family': 'Helvetica Neue, Helvetica, Arial, sans-serif',
        'font_size': '24px',
        'font_color': '#333333',
        'alignment': 'left',
        'padding': '14px',
        'line_height': '1.5',
    },
    'striped': {
        'description': 'Alternating row colors for readability',
        'border': BORDER_STYLES['horizontal_only'],
        'background': BACKGROUND_COLOR_PALETTES['light_gray'],
        'background_pattern': 'striped',
        'font_family': 'Verdana, Geneva, sans-serif',
        'font_size': '22px',
        'font_color': '#1a1a1a',
        'alignment': 'left',
        'padding': '10px',
        'line_height': '1.4',
    },
    'academic': {
        'description': 'Traditional academic paper style',
        'border': BORDER_STYLES['header_with_outer'],
        'background': BACKGROUND_COLOR_PALETTES['white_clean'],
        'background_pattern': 'none',
        'font_family': 'Times New Roman, Times, serif',
        'font_size': '18px',
        'font_color': '#000000',
        'alignment': 'center',
        'padding': '6px',
        'line_height': '1.3',
    },
    'financial': {
        'description': 'Financial report style',
        'border': BORDER_STYLES['full'],
        'background': BACKGROUND_COLOR_PALETTES['white_clean'],
        'background_pattern': 'header',
        'font_family': 'Calibri, sans-serif',
        'font_size': '20px',
        'font_color': '#000000',
        'alignment': 'right',
        'padding': '8px',
        'line_height': '1.3',
    },
    'presentation': {
        'description': 'Large text for presentations',
        'border': BORDER_STYLES['full'],
        'background': BACKGROUND_COLOR_PALETTES['soft_blue'],
        'background_pattern': 'header',
        'font_family': 'Arial, Helvetica, sans-serif',
        'font_size': '36px',
        'font_color': '#0d47a1',
        'alignment': 'center',
        'padding': '16px',
        'line_height': '1.5',
    },
}


# =============================================================================
# RANDOM SELECTION WEIGHTS - FAVOR REALISTIC COMBINATIONS
# =============================================================================

RANDOM_WEIGHTS = {
    'border_styles': {
        'full': 30,              # Full borders - common
        'borderless': 25,        # No borders - common for modern docs
        'horizontal_only': 20,   # Horizontal lines only
        'header_with_outer': 15, # Header + outer borders
        'outer_only': 5,         # Just outer frame
        'vertical_only': 3,      # Rare
        'header_border_only': 2, # Rare
    },
    'background_patterns': {
        'none': 50,              # Most common - no background coloring
        'header': 30,            # Header only has background
        'even-odd': 15,          # Zebra striping
        'striped': 5,            # Less common striping
    },
    'font_categories': {
        'sans-serif': 55,
        'serif': 40,
        'monospace': 5,
    },
    'font_size_tiers': {
        'small': 15,             # Less common - too small for most uses
        'medium': 50,            # Most common - standard readable size
        'large': 28,             # Common for emphasis
        'xlarge': 7,             # Rare - only for presentations/headers
    },
    'line_breaks': {
        'none': 30,              # Some tables have short content - no breaks needed
        'light': 25,             # Light breaking for moderate content
        'content_aware': 35,     # Most common - break based on content width
        'moderate': 10,          # More aggressive breaking
    },
    'background_palettes': {
        'white_clean': 40,       # Pure white - most common
        'minimal_white': 25,     # Minimal styling
        'light_gray': 15,        # Light gray
        'soft_blue': 5,          # Colored backgrounds less common
        'soft_green': 4,
        'warm_cream': 4,
        'corporate_blue': 3,
        'corporate_dark': 2,
        'teal_accent': 1,
        'soft_purple': 1,
    },
    # Text color weights - heavily favor black
    'text_colors': {
        'black': 75,             # Normal black text
        'dark_gray': 15,         # Dark gray
        'colored': 10,           # Colored text (from palette)
    },
    # Border color weights - favor black/dark
    'border_colors': {
        'black': 60,             # #000000
        'dark_gray': 25,         # #333333, #444444
        'medium_gray': 10,       # #666666, #888888
        'light_gray': 5,         # #cccccc, #dddddd
    },
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_font_category(font_family: str) -> str:
    """Determine the category of a font family."""
    font_lower = font_family.lower()
    if 'monospace' in font_lower or 'courier' in font_lower or 'consolas' in font_lower:
        return 'monospace'
    elif any(x in font_lower for x in ['times', 'georgia', 'palatino', 'cambria', 'garamond']):
        return 'serif'
    else:
        return 'sans-serif'


def get_fonts_by_category(category: str) -> List[str]:
    """Get fonts from a specific category."""
    if category == 'serif':
        return FONTS_SERIF
    elif category == 'sans-serif':
        return FONTS_SANS_SERIF
    elif category == 'monospace':
        return FONTS_MONOSPACE
    return FONTS_SANS_SERIF  # Default


def get_contrasting_text_color(background_palette: str) -> str:
    """Get a safe text color that contrasts with the background palette."""
    if background_palette in BACKGROUND_COLOR_PALETTES:
        palette = BACKGROUND_COLOR_PALETTES[background_palette]
        return palette.get('text_colors', ['#000000'])[0]
    return '#000000'


def get_coherent_spacing(font_size: str) -> Dict[str, str]:
    """Get coherent spacing values based on font size."""
    # Extract numeric value from font size
    try:
        size_px = int(font_size.replace('px', ''))
    except (ValueError, AttributeError):
        size_px = 24  # Default
    
    # Find which tier this font size belongs to
    # FAVOR TIGHTER/NORMAL spacing for realistic look
    for tier_name, tier_data in FONT_SIZE_TIERS.items():
        if font_size in tier_data['sizes']:
            min_pad, max_pad = tier_data['padding_range']
            min_lh, max_lh = tier_data['line_height_range']
            # Use minimum values for tighter, more realistic look
            # Add small random variation for diversity
            import random
            pad_values = [min_pad]  # Favor minimum
            lh_values = [min_lh]    # Favor minimum
            return {
                'padding': random.choice(pad_values),
                'line_height': random.choice(lh_values),
            }
    
    # Default for unknown sizes - use TIGHTER values
    if size_px <= 18:
        return {'padding': '4px', 'line_height': '1.25'}
    elif size_px <= 26:
        return {'padding': '6px', 'line_height': '1.3'}
    elif size_px <= 34:
        return {'padding': '8px', 'line_height': '1.35'}
    else:
        return {'padding': '10px', 'line_height': '1.4'}


def validate_alignment_for_border(border_style: str, alignment_pattern: str) -> bool:
    """Check if alignment pattern is valid for the border style."""
    if border_style not in BORDER_STYLES:
        return True
    
    border_data = BORDER_STYLES[border_style]
    constraint = border_data.get('alignment_constraint')
    
    if constraint is None:
        return True  # No constraint
    
    if constraint == 'consistent':
        # Must use uniform alignment
        if alignment_pattern in COLUMN_ALIGNMENT_PATTERNS:
            pattern_data = COLUMN_ALIGNMENT_PATTERNS[alignment_pattern]
            return pattern_data.get('works_with_borderless', False)
        return alignment_pattern in ['left', 'center', 'right']
    
    return True


def get_safe_alignment_for_border(border_style: str) -> str:
    """Get a safe alignment choice for the given border style."""
    if border_style in ['borderless', 'outer_only', 'header_border_only']:
        # These need consistent alignment - pick one uniformly
        return 'left'  # Most readable for borderless
    return 'center'  # Default for bordered tables
