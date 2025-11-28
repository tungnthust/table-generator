"""
Style Configuration Module
==========================
Configuration for table rendering styles.
Reuses and extends TableStyleConfig from html_render.py.

Supports random selection of styles based on user requirements through
command-line arguments.
"""

import json
import random
import argparse
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Literal, Optional, Any, Union

# Import style attributes
from config.style_attributes import (
    BORDER_STYLES, BORDER_WIDTHS, BORDER_COLORS,
    BACKGROUND_PATTERNS, BACKGROUND_COLOR_PALETTES,
    FONT_FAMILIES, FONT_SIZES, FONT_WEIGHTS, FONT_STYLES, FONT_TRANSFORMS, FONT_COLORS,
    HORIZONTAL_ALIGNMENTS, VERTICAL_ALIGNMENTS, COLUMN_ALIGNMENT_PATTERNS,
    PADDING_VALUES, CELL_SPACING_VALUES, LINE_HEIGHT_VALUES,
    ROW_HEIGHT_VALUES, COLUMN_WIDTH_VALUES,
    LINE_BREAK_CONFIGS, STYLE_PRESETS, RANDOM_WEIGHTS,
    get_font_category, get_fonts_by_category
)


@dataclass
class BorderConfig:
    """Configuration for table borders."""
    style: Literal['border', 'borderless', 'partly-borderless'] = 'border'
    width: str = '2px'
    color: str = 'black'
    
    # Partly-borderless options
    remove_row_borders: bool = False
    remove_col_borders: bool = False
    remove_inner_borders: bool = False
    keep_outer_border: bool = True
    keep_header_row_border: bool = True
    keep_colspan_col_borders: bool = True
    
    # Random deletion options
    random_delete_row_borders: bool = False
    random_delete_col_borders: bool = False
    border_delete_probability: float = 0.3


@dataclass
class BackgroundConfig:
    """Configuration for cell background colors."""
    pattern: Literal['none', 'header', 'even-odd', 'first-last', 'striped', 'random', 'checkerboard', 'column-based'] = 'header'
    header_color: str = '#F2F2F2'
    even_color: str = '#FFFFFF'
    odd_color: str = '#F9F9F9'
    first_color: str = '#E8E8E8'
    last_color: str = '#E8E8E8'
    random_colors: List[str] = field(default_factory=lambda: ['#F2F2F2', '#E8F4F8', '#FFF8E8'])
    
    # Data vs header color differentiation
    data_cell_color: str = '#FFFFFF'
    header_text_color: str = '#000000'
    
    # Column-based coloring
    column_colors: Dict[int, str] = field(default_factory=dict)


@dataclass
class FontConfig:
    """Configuration for font styling."""
    family: str = 'Times New Roman, serif'
    size: str = '36px'
    weight: Literal['normal', 'bold', 'random'] = 'normal'
    style: Literal['normal', 'italic', 'random'] = 'normal'
    color: str = 'black'
    transform: Literal['none', 'uppercase', 'lowercase', 'capitalize', 'random'] = 'none'
    
    header_weight: str = 'bold'
    header_style: str = 'normal'
    header_color: str = 'black'
    header_size: str = ''  # Empty means use main size
    
    footer_weight: str = 'bold'
    footer_style: str = 'normal'
    
    # Per-cell random styling
    random_weight_probability: float = 0.3
    random_style_probability: float = 0.2
    random_transform_probability: float = 0.1


@dataclass
class AlignmentConfig:
    """Configuration for text alignment."""
    horizontal: Literal['left', 'center', 'right', 'justify', 'random'] = 'center'
    vertical: Literal['top', 'middle', 'bottom', 'baseline', 'random'] = 'middle'
    
    column_alignments: Dict[int, str] = field(default_factory=dict)
    
    # Header-specific alignment
    header_horizontal: str = 'center'
    header_vertical: str = 'middle'
    
    # Data-specific alignment (overrides general alignment for data cells)
    data_horizontal: str = ''  # Empty means use general horizontal
    data_vertical: str = ''  # Empty means use general vertical


@dataclass
class SpacingConfig:
    """Configuration for spacing and dimensions."""
    padding: str = '8px'
    cell_spacing: str = '0'
    line_height: str = '1.4'
    
    row_heights: Dict[int, str] = field(default_factory=dict)
    column_widths: Dict[int, str] = field(default_factory=dict)
    
    # Min/max dimensions for random generation
    min_row_height: str = '30px'
    max_row_height: str = '80px'
    min_column_width: str = '50px'
    max_column_width: str = '200px'
    
    # Random line break settings
    random_line_breaks: bool = False
    line_break_probability: float = 0.15
    min_words_before_break: int = 3
    max_breaks_per_cell: int = 2
    break_on_punctuation: bool = False
    prefer_natural_breaks: bool = False


def _weighted_choice(weights: Dict[str, int]) -> str:
    """
    Choose a random item based on weights.
    
    Args:
        weights: Dictionary mapping items to their weights
        
    Returns:
        Randomly selected item key
    """
    items = list(weights.keys())
    weight_values = list(weights.values())
    total = sum(weight_values)
    cumulative = 0
    rand_val = random.random() * total
    
    for item, weight in zip(items, weight_values):
        cumulative += weight
        if rand_val <= cumulative:
            return item
    
    return items[-1]  # Fallback to last item


@dataclass
class StyleConfig:
    """
    Main configuration class combining all styling options.
    This is an extended version of TableStyleConfig with additional utility methods.
    """
    border: BorderConfig = field(default_factory=BorderConfig)
    background: BackgroundConfig = field(default_factory=BackgroundConfig)
    font: FontConfig = field(default_factory=FontConfig)
    alignment: AlignmentConfig = field(default_factory=AlignmentConfig)
    spacing: SpacingConfig = field(default_factory=SpacingConfig)
    
    # Table-level properties
    width: str = '100%'
    border_collapse: str = 'collapse'
    
    # ===== FACTORY METHODS FOR COMMON PRESETS =====
    
    @classmethod
    def create_default(cls) -> 'StyleConfig':
        """Create default configuration matching original style."""
        return cls()
    
    @classmethod
    def create_borderless(cls) -> 'StyleConfig':
        """Create borderless table configuration."""
        config = cls()
        config.border.style = 'borderless'
        return config
    
    @classmethod
    def create_minimal(cls) -> 'StyleConfig':
        """Create minimal style with only outer borders."""
        config = cls()
        config.border.style = 'partly-borderless'
        config.border.remove_inner_borders = True
        config.border.keep_outer_border = True
        config.background.pattern = 'none'
        return config
    
    @classmethod
    def create_random(cls, 
                      border_style: Optional[str] = None,
                      background_palette: Optional[str] = None,
                      font_category: Optional[str] = None,
                      line_break_config: Optional[str] = None,
                      randomize_all: bool = True) -> 'StyleConfig':
        """
        Create a random style configuration with optional constraints.
        
        Args:
            border_style: Specific border style to use (from BORDER_STYLES keys)
            background_palette: Specific color palette (from BACKGROUND_COLOR_PALETTES keys)
            font_category: Font category to use ('serif', 'sans-serif', 'monospace')
            line_break_config: Line break configuration (from LINE_BREAK_CONFIGS keys)
            randomize_all: If True, randomize all aspects; otherwise only specified ones
            
        Returns:
            StyleConfig instance with random/specified options
        """
        config = cls()
        
        # === BORDER CONFIGURATION ===
        if border_style and border_style in BORDER_STYLES:
            border_attrs = BORDER_STYLES[border_style]
        elif randomize_all:
            # Weighted random selection
            border_style = _weighted_choice(RANDOM_WEIGHTS['border_styles'])
            border_attrs = BORDER_STYLES[border_style]
        else:
            border_attrs = BORDER_STYLES['full']
        
        config.border.style = border_attrs.get('style', 'border')
        config.border.remove_row_borders = border_attrs.get('remove_row_borders', False)
        config.border.remove_col_borders = border_attrs.get('remove_col_borders', False)
        config.border.remove_inner_borders = border_attrs.get('remove_inner_borders', False)
        config.border.keep_outer_border = border_attrs.get('keep_outer_border', True)
        config.border.keep_header_row_border = border_attrs.get('keep_header_row_border', True)
        config.border.keep_colspan_col_borders = border_attrs.get('keep_colspan_col_borders', True)
        
        if randomize_all:
            config.border.width = random.choice(BORDER_WIDTHS)
            config.border.color = random.choice(BORDER_COLORS)
        
        # === BACKGROUND CONFIGURATION ===
        if background_palette and background_palette in BACKGROUND_COLOR_PALETTES:
            bg_palette = BACKGROUND_COLOR_PALETTES[background_palette]
        elif randomize_all:
            palette_name = random.choice(list(BACKGROUND_COLOR_PALETTES.keys()))
            bg_palette = BACKGROUND_COLOR_PALETTES[palette_name]
        else:
            bg_palette = BACKGROUND_COLOR_PALETTES['neutral']
        
        config.background.header_color = bg_palette['header_color']
        config.background.even_color = bg_palette['even_color']
        config.background.odd_color = bg_palette['odd_color']
        config.background.first_color = bg_palette['first_color']
        config.background.last_color = bg_palette['last_color']
        config.background.random_colors = bg_palette['random_colors']
        
        if randomize_all:
            config.background.pattern = _weighted_choice(RANDOM_WEIGHTS['background_patterns'])
        
        # === FONT CONFIGURATION ===
        if font_category and font_category in ['serif', 'sans-serif', 'monospace']:
            fonts = get_fonts_by_category(font_category)
            config.font.family = random.choice(fonts) if fonts else FONT_FAMILIES[0]
        elif randomize_all:
            # Weighted font category selection
            category = _weighted_choice(RANDOM_WEIGHTS['font_categories'])
            fonts = get_fonts_by_category(category)
            config.font.family = random.choice(fonts) if fonts else FONT_FAMILIES[0]
        
        if randomize_all:
            config.font.size = random.choice(FONT_SIZES)
            config.font.color = random.choice(FONT_COLORS)
            
            # Random font styling with probability
            if random.random() < 0.3:
                config.font.weight = 'random'
            if random.random() < 0.2:
                config.font.style = 'random'
            if random.random() < 0.15:
                config.font.transform = 'random'
        
        # === ALIGNMENT CONFIGURATION ===
        if randomize_all:
            config.alignment.horizontal = random.choice(HORIZONTAL_ALIGNMENTS)
            config.alignment.vertical = random.choice(VERTICAL_ALIGNMENTS)
            
            # Random column-specific alignments
            if random.random() < 0.3:
                num_cols = random.randint(2, 7)
                for col in range(num_cols):
                    if random.random() < 0.4:
                        config.alignment.column_alignments[col] = random.choice(HORIZONTAL_ALIGNMENTS)
        
        # === SPACING CONFIGURATION ===
        if randomize_all:
            config.spacing.padding = random.choice(PADDING_VALUES)
            config.spacing.cell_spacing = random.choice(CELL_SPACING_VALUES)
            config.spacing.line_height = random.choice(LINE_HEIGHT_VALUES)
        
        # === LINE BREAK CONFIGURATION ===
        if line_break_config and line_break_config in LINE_BREAK_CONFIGS:
            lb_config = LINE_BREAK_CONFIGS[line_break_config]
        elif randomize_all:
            lb_name = _weighted_choice(RANDOM_WEIGHTS['line_breaks'])
            lb_config = LINE_BREAK_CONFIGS[lb_name]
        else:
            lb_config = LINE_BREAK_CONFIGS['none']
        
        config.spacing.random_line_breaks = lb_config.get('enabled', False)
        config.spacing.line_break_probability = lb_config.get('probability', 0.0)
        config.spacing.min_words_before_break = lb_config.get('min_words_before_break', 3)
        config.spacing.max_breaks_per_cell = lb_config.get('max_breaks_per_cell', 2)
        config.spacing.break_on_punctuation = lb_config.get('break_on_punctuation', False)
        config.spacing.prefer_natural_breaks = lb_config.get('prefer_natural_breaks', False)
        
        return config
    
    @classmethod
    def from_preset(cls, preset: str) -> 'StyleConfig':
        """
        Create configuration from a named preset.
        
        Args:
            preset: One of 'default', 'borderless', 'minimal', 'random', 'modern', 
                   'corporate', 'striped', 'colorful', 'academic', 'financial'
            
        Returns:
            StyleConfig instance
        """
        # Basic presets using factory methods
        basic_presets = {
            'default': cls.create_default,
            'borderless': cls.create_borderless,
            'minimal': cls.create_minimal,
            'random': cls.create_random
        }
        
        if preset in basic_presets:
            return basic_presets[preset]()
        
        # Extended presets from STYLE_PRESETS
        if preset in STYLE_PRESETS:
            preset_data = STYLE_PRESETS[preset]
            config = cls()
            
            # Apply border settings
            if 'border' in preset_data:
                border_attrs = preset_data['border']
                config.border.style = border_attrs.get('style', 'border')
                config.border.remove_row_borders = border_attrs.get('remove_row_borders', False)
                config.border.remove_col_borders = border_attrs.get('remove_col_borders', False)
                config.border.remove_inner_borders = border_attrs.get('remove_inner_borders', False)
                config.border.keep_outer_border = border_attrs.get('keep_outer_border', True)
                config.border.keep_header_row_border = border_attrs.get('keep_header_row_border', True)
                config.border.keep_colspan_col_borders = border_attrs.get('keep_colspan_col_borders', True)
            
            # Apply background settings
            if 'background' in preset_data:
                bg_palette = preset_data['background']
                config.background.header_color = bg_palette.get('header_color', '#F2F2F2')
                config.background.even_color = bg_palette.get('even_color', '#FFFFFF')
                config.background.odd_color = bg_palette.get('odd_color', '#F9F9F9')
                config.background.first_color = bg_palette.get('first_color', '#E8E8E8')
                config.background.last_color = bg_palette.get('last_color', '#E8E8E8')
                config.background.random_colors = bg_palette.get('random_colors', ['#F2F2F2'])
            
            if 'background_pattern' in preset_data:
                config.background.pattern = preset_data['background_pattern']
            
            # Apply font settings
            if 'font_family' in preset_data:
                config.font.family = preset_data['font_family']
            if 'font_size' in preset_data:
                config.font.size = preset_data['font_size']
            
            # Apply alignment settings
            if 'alignment' in preset_data:
                config.alignment.horizontal = preset_data['alignment']
            
            # Apply padding settings
            if 'padding' in preset_data:
                config.spacing.padding = preset_data['padding']
            
            return config
        
        # List all available presets
        all_presets = list(basic_presets.keys()) + list(STYLE_PRESETS.keys())
        raise ValueError(f"Unknown preset: {preset}. Available: {all_presets}")
    
    # ===== VARIATION METHODS =====
    
    def create_variation(self) -> 'StyleConfig':
        """
        Create a random variation of this style within reasonable bounds.
        
        Returns:
            New StyleConfig with random variations
        """
        # Create a copy
        config = StyleConfig.from_dict(self.to_dict())
        
        # Apply random variations using the new attributes
        if random.random() > 0.5:
            config.border.width = random.choice(BORDER_WIDTHS)
        
        if random.random() > 0.7:
            config.border.color = random.choice(BORDER_COLORS)
        
        if random.random() > 0.5:
            config.font.size = random.choice(FONT_SIZES)
        
        if random.random() > 0.7:
            config.font.color = random.choice(FONT_COLORS)
        
        if random.random() > 0.5:
            config.spacing.padding = random.choice(PADDING_VALUES)
        
        if random.random() > 0.7:
            config.alignment.horizontal = random.choice(HORIZONTAL_ALIGNMENTS)
        
        if random.random() > 0.8:
            config.alignment.vertical = random.choice(VERTICAL_ALIGNMENTS)
        
        if random.random() > 0.7:
            config.spacing.line_height = random.choice(LINE_HEIGHT_VALUES)
        
        # Randomly enable line breaks
        if random.random() > 0.8:
            lb_name = random.choice(list(LINE_BREAK_CONFIGS.keys()))
            lb_config = LINE_BREAK_CONFIGS[lb_name]
            config.spacing.random_line_breaks = lb_config.get('enabled', False)
            config.spacing.line_break_probability = lb_config.get('probability', 0.0)
        
        return config
    
    # ===== JSON SERIALIZATION =====
    
    @classmethod
    def from_json(cls, json_path: str) -> 'StyleConfig':
        """
        Load configuration from JSON file.
        
        Args:
            json_path: Path to JSON configuration file
            
        Returns:
            StyleConfig instance
        """
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return cls.from_dict(data)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'StyleConfig':
        """
        Create configuration from dictionary.
        
        Args:
            data: Dictionary containing configuration values
            
        Returns:
            StyleConfig instance
        """
        config = cls()
        
        # Handle nested configurations
        if 'border' in data:
            for k, v in data['border'].items():
                if hasattr(config.border, k):
                    setattr(config.border, k, v)
        
        if 'background' in data:
            for k, v in data['background'].items():
                if hasattr(config.background, k):
                    setattr(config.background, k, v)
        
        if 'font' in data:
            for k, v in data['font'].items():
                if hasattr(config.font, k):
                    setattr(config.font, k, v)
        
        if 'alignment' in data:
            for k, v in data['alignment'].items():
                if hasattr(config.alignment, k):
                    setattr(config.alignment, k, v)
        
        if 'spacing' in data:
            for k, v in data['spacing'].items():
                if hasattr(config.spacing, k):
                    setattr(config.spacing, k, v)
        
        # Handle top-level properties
        if 'width' in data:
            config.width = data['width']
        if 'border_collapse' in data:
            config.border_collapse = data['border_collapse']
        
        return config
    
    def to_json(self, json_path: str) -> None:
        """
        Save configuration to JSON file.
        
        Args:
            json_path: Path to save JSON configuration file
        """
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    def to_dict(self) -> dict:
        """
        Convert configuration to dictionary.
        
        Returns:
            Dictionary representation of configuration
        """
        return {
            'border': asdict(self.border),
            'background': asdict(self.background),
            'font': asdict(self.font),
            'alignment': asdict(self.alignment),
            'spacing': asdict(self.spacing),
            'width': self.width,
            'border_collapse': self.border_collapse
        }
    
    # ===== CLI ARGUMENT SUPPORT =====
    
    @staticmethod
    def add_cli_arguments(parser: argparse.ArgumentParser) -> None:
        """
        Add style arguments to an argument parser.
        
        Args:
            parser: ArgumentParser to add arguments to
        """
        # Get all available presets
        basic_presets = ['default', 'borderless', 'minimal', 'random']
        extended_presets = list(STYLE_PRESETS.keys())
        all_presets = basic_presets + [p for p in extended_presets if p not in basic_presets]
        
        parser.add_argument(
            '--style-preset',
            type=str,
            choices=all_presets,
            default='default',
            help=f'Style preset to use. Available: {", ".join(all_presets)} (default: default)'
        )
        parser.add_argument(
            '--style-config',
            type=str,
            default=None,
            help='Path to JSON style configuration file'
        )
        parser.add_argument(
            '--num-styles',
            type=int,
            default=1,
            help='Number of style variations to generate per HTML (default: 1)'
        )
        
        # Border style options
        parser.add_argument(
            '--border-style',
            type=str,
            choices=list(BORDER_STYLES.keys()),
            default=None,
            help='Specific border style to use'
        )
        parser.add_argument(
            '--border-color',
            type=str,
            default=None,
            help='Border color (e.g., "black", "#333333")'
        )
        parser.add_argument(
            '--border-width',
            type=str,
            default=None,
            help='Border width (e.g., "1px", "2px")'
        )
        
        # Background options
        parser.add_argument(
            '--background-palette',
            type=str,
            choices=list(BACKGROUND_COLOR_PALETTES.keys()),
            default=None,
            help='Background color palette to use'
        )
        parser.add_argument(
            '--background-pattern',
            type=str,
            choices=BACKGROUND_PATTERNS,
            default=None,
            help='Background color pattern'
        )
        
        # Font options
        parser.add_argument(
            '--font-family',
            type=str,
            default=None,
            help='Font family (e.g., "Arial, sans-serif")'
        )
        parser.add_argument(
            '--font-size',
            type=str,
            default=None,
            help='Font size (e.g., "32px", "36px")'
        )
        parser.add_argument(
            '--font-color',
            type=str,
            default=None,
            help='Font color (e.g., "black", "#333333")'
        )
        parser.add_argument(
            '--font-category',
            type=str,
            choices=['serif', 'sans-serif', 'monospace'],
            default=None,
            help='Font category for random selection'
        )
        
        # Alignment options
        parser.add_argument(
            '--align-horizontal',
            type=str,
            choices=HORIZONTAL_ALIGNMENTS + ['random'],
            default=None,
            help='Horizontal text alignment'
        )
        parser.add_argument(
            '--align-vertical',
            type=str,
            choices=VERTICAL_ALIGNMENTS + ['random'],
            default=None,
            help='Vertical text alignment'
        )
        
        # Spacing options
        parser.add_argument(
            '--padding',
            type=str,
            default=None,
            help='Cell padding (e.g., "8px", "10px 20px")'
        )
        parser.add_argument(
            '--line-height',
            type=str,
            default=None,
            help='Line height (e.g., "1.4", "1.6")'
        )
        
        # Line break options
        parser.add_argument(
            '--line-break-config',
            type=str,
            choices=list(LINE_BREAK_CONFIGS.keys()),
            default=None,
            help='Line break configuration for cell content'
        )
        parser.add_argument(
            '--random-line-breaks',
            action='store_true',
            help='Enable random line breaks in cell content'
        )
        parser.add_argument(
            '--line-break-probability',
            type=float,
            default=None,
            help='Probability of inserting line break (0.0-1.0)'
        )
    
    @classmethod
    def from_cli_args(cls, args: argparse.Namespace) -> 'StyleConfig':
        """
        Create configuration from CLI arguments.
        
        Args:
            args: Parsed command line arguments
            
        Returns:
            StyleConfig instance
        """
        # If style config file is provided, load from it
        style_config_path = getattr(args, 'style_config', None)
        if style_config_path:
            config = cls.from_json(style_config_path)
        else:
            # Check if using random preset with specific constraints
            preset = getattr(args, 'style_preset', 'default')
            
            if preset == 'random':
                # Use create_random with optional constraints
                config = cls.create_random(
                    border_style=getattr(args, 'border_style', None),
                    background_palette=getattr(args, 'background_palette', None),
                    font_category=getattr(args, 'font_category', None),
                    line_break_config=getattr(args, 'line_break_config', None),
                    randomize_all=True
                )
            else:
                config = cls.from_preset(preset)
        
        # Apply CLI overrides
        if getattr(args, 'border_style', None) and args.border_style in BORDER_STYLES:
            border_attrs = BORDER_STYLES[args.border_style]
            config.border.style = border_attrs.get('style', 'border')
            config.border.remove_row_borders = border_attrs.get('remove_row_borders', False)
            config.border.remove_col_borders = border_attrs.get('remove_col_borders', False)
            config.border.remove_inner_borders = border_attrs.get('remove_inner_borders', False)
            config.border.keep_outer_border = border_attrs.get('keep_outer_border', True)
            config.border.keep_header_row_border = border_attrs.get('keep_header_row_border', True)
            config.border.keep_colspan_col_borders = border_attrs.get('keep_colspan_col_borders', True)
        
        if getattr(args, 'border_color', None):
            config.border.color = args.border_color
        
        if getattr(args, 'border_width', None):
            config.border.width = args.border_width
        
        if getattr(args, 'background_palette', None) and args.background_palette in BACKGROUND_COLOR_PALETTES:
            bg_palette = BACKGROUND_COLOR_PALETTES[args.background_palette]
            config.background.header_color = bg_palette['header_color']
            config.background.even_color = bg_palette['even_color']
            config.background.odd_color = bg_palette['odd_color']
            config.background.first_color = bg_palette['first_color']
            config.background.last_color = bg_palette['last_color']
            config.background.random_colors = bg_palette['random_colors']
        
        if getattr(args, 'background_pattern', None):
            config.background.pattern = args.background_pattern
        
        if getattr(args, 'font_family', None):
            config.font.family = args.font_family
        
        if getattr(args, 'font_size', None):
            config.font.size = args.font_size
        
        if getattr(args, 'font_color', None):
            config.font.color = args.font_color
        
        if getattr(args, 'align_horizontal', None):
            config.alignment.horizontal = args.align_horizontal
        
        if getattr(args, 'align_vertical', None):
            config.alignment.vertical = args.align_vertical
        
        if getattr(args, 'padding', None):
            config.spacing.padding = args.padding
        
        if getattr(args, 'line_height', None):
            config.spacing.line_height = args.line_height
        
        # Line break settings
        if getattr(args, 'line_break_config', None) and args.line_break_config in LINE_BREAK_CONFIGS:
            lb_config = LINE_BREAK_CONFIGS[args.line_break_config]
            config.spacing.random_line_breaks = lb_config.get('enabled', False)
            config.spacing.line_break_probability = lb_config.get('probability', 0.0)
            config.spacing.min_words_before_break = lb_config.get('min_words_before_break', 3)
            config.spacing.max_breaks_per_cell = lb_config.get('max_breaks_per_cell', 2)
        
        if getattr(args, 'random_line_breaks', False):
            config.spacing.random_line_breaks = True
            if config.spacing.line_break_probability == 0.0:
                config.spacing.line_break_probability = 0.15
        
        if getattr(args, 'line_break_probability', None) is not None:
            config.spacing.random_line_breaks = True
            config.spacing.line_break_probability = args.line_break_probability
        
        return config


# =============================================================================
# STANDALONE FUNCTIONS FOR RANDOM STYLE SELECTION
# =============================================================================

def random_select_style(
    border_style: Optional[str] = None,
    background_palette: Optional[str] = None,
    background_pattern: Optional[str] = None,
    font_category: Optional[str] = None,
    font_family: Optional[str] = None,
    font_size: Optional[str] = None,
    font_color: Optional[str] = None,
    alignment: Optional[str] = None,
    padding: Optional[str] = None,
    line_break_config: Optional[str] = None,
    randomize_unspecified: bool = True
) -> StyleConfig:
    """
    Create a random style configuration with optional constraints.
    
    This is the main function for randomly selecting and combining style attributes
    based on user requirements through arguments.
    
    Args:
        border_style: Specific border style from BORDER_STYLES keys
                     ('full', 'borderless', 'outer_only', 'horizontal_only', 
                      'vertical_only', 'header_border_only', 'header_with_outer', 'colspan_aware')
        background_palette: Color palette from BACKGROUND_COLOR_PALETTES keys
                           ('neutral', 'blue', 'green', 'warm', 'purple', 'teal', 
                            'orange', 'pink', 'corporate_blue', 'minimal')
        background_pattern: Pattern from BACKGROUND_PATTERNS
                           ('none', 'header', 'even-odd', 'first-last', 'striped', 
                            'random', 'checkerboard', 'column-based')
        font_category: Font category ('serif', 'sans-serif', 'monospace')
        font_family: Specific font family string
        font_size: Specific font size (e.g., '32px', '36px')
        font_color: Specific font color
        alignment: Horizontal alignment ('left', 'center', 'right', 'justify')
        padding: Cell padding value
        line_break_config: Line break configuration from LINE_BREAK_CONFIGS keys
                          ('none', 'light', 'moderate', 'heavy', 'content_aware')
        randomize_unspecified: If True, randomly select unspecified attributes;
                              otherwise use defaults
    
    Returns:
        StyleConfig instance with selected/random options
    
    Examples:
        # Fully random style
        config = random_select_style()
        
        # Random with blue color scheme
        config = random_select_style(background_palette='blue')
        
        # Random with serif font and striped background
        config = random_select_style(font_category='serif', background_pattern='striped')
        
        # Specific border style with random other attributes
        config = random_select_style(border_style='horizontal_only')
        
        # Multiple constraints
        config = random_select_style(
            border_style='full',
            background_palette='corporate_blue',
            font_category='sans-serif',
            alignment='center'
        )
    """
    config = StyleConfig()
    
    # === BORDER CONFIGURATION ===
    if border_style and border_style in BORDER_STYLES:
        border_attrs = BORDER_STYLES[border_style]
    elif randomize_unspecified:
        selected_style = _weighted_choice(RANDOM_WEIGHTS['border_styles'])
        border_attrs = BORDER_STYLES[selected_style]
    else:
        border_attrs = BORDER_STYLES['full']
    
    config.border.style = border_attrs.get('style', 'border')
    config.border.remove_row_borders = border_attrs.get('remove_row_borders', False)
    config.border.remove_col_borders = border_attrs.get('remove_col_borders', False)
    config.border.remove_inner_borders = border_attrs.get('remove_inner_borders', False)
    config.border.keep_outer_border = border_attrs.get('keep_outer_border', True)
    config.border.keep_header_row_border = border_attrs.get('keep_header_row_border', True)
    config.border.keep_colspan_col_borders = border_attrs.get('keep_colspan_col_borders', True)
    
    if randomize_unspecified:
        config.border.width = random.choice(BORDER_WIDTHS)
        config.border.color = random.choice(BORDER_COLORS)
    
    # === BACKGROUND CONFIGURATION ===
    if background_palette and background_palette in BACKGROUND_COLOR_PALETTES:
        bg_palette = BACKGROUND_COLOR_PALETTES[background_palette]
    elif randomize_unspecified:
        palette_name = random.choice(list(BACKGROUND_COLOR_PALETTES.keys()))
        bg_palette = BACKGROUND_COLOR_PALETTES[palette_name]
    else:
        bg_palette = BACKGROUND_COLOR_PALETTES['neutral']
    
    config.background.header_color = bg_palette['header_color']
    config.background.even_color = bg_palette['even_color']
    config.background.odd_color = bg_palette['odd_color']
    config.background.first_color = bg_palette['first_color']
    config.background.last_color = bg_palette['last_color']
    config.background.random_colors = bg_palette['random_colors']
    
    if background_pattern:
        config.background.pattern = background_pattern
    elif randomize_unspecified:
        config.background.pattern = _weighted_choice(RANDOM_WEIGHTS['background_patterns'])
    
    # === FONT CONFIGURATION ===
    if font_family:
        config.font.family = font_family
    elif font_category and font_category in ['serif', 'sans-serif', 'monospace']:
        fonts = get_fonts_by_category(font_category)
        config.font.family = random.choice(fonts) if fonts else FONT_FAMILIES[0]
    elif randomize_unspecified:
        category = _weighted_choice(RANDOM_WEIGHTS['font_categories'])
        fonts = get_fonts_by_category(category)
        config.font.family = random.choice(fonts) if fonts else FONT_FAMILIES[0]
    
    if font_size:
        config.font.size = font_size
    elif randomize_unspecified:
        config.font.size = random.choice(FONT_SIZES)
    
    if font_color:
        config.font.color = font_color
    elif randomize_unspecified:
        config.font.color = random.choice(FONT_COLORS)
    
    if randomize_unspecified:
        # Random font styling with probability
        if random.random() < 0.3:
            config.font.weight = 'random'
        if random.random() < 0.2:
            config.font.style = 'random'
        if random.random() < 0.15:
            config.font.transform = 'random'
    
    # === ALIGNMENT CONFIGURATION ===
    if alignment:
        config.alignment.horizontal = alignment
    elif randomize_unspecified:
        config.alignment.horizontal = random.choice(HORIZONTAL_ALIGNMENTS)
    
    if randomize_unspecified:
        config.alignment.vertical = random.choice(VERTICAL_ALIGNMENTS)
    
    # === SPACING CONFIGURATION ===
    if padding:
        config.spacing.padding = padding
    elif randomize_unspecified:
        config.spacing.padding = random.choice(PADDING_VALUES)
    
    if randomize_unspecified:
        config.spacing.cell_spacing = random.choice(CELL_SPACING_VALUES)
        config.spacing.line_height = random.choice(LINE_HEIGHT_VALUES)
    
    # === LINE BREAK CONFIGURATION ===
    if line_break_config and line_break_config in LINE_BREAK_CONFIGS:
        lb_config = LINE_BREAK_CONFIGS[line_break_config]
    elif randomize_unspecified:
        lb_name = _weighted_choice(RANDOM_WEIGHTS['line_breaks'])
        lb_config = LINE_BREAK_CONFIGS[lb_name]
    else:
        lb_config = LINE_BREAK_CONFIGS['none']
    
    config.spacing.random_line_breaks = lb_config.get('enabled', False)
    config.spacing.line_break_probability = lb_config.get('probability', 0.0)
    config.spacing.min_words_before_break = lb_config.get('min_words_before_break', 3)
    config.spacing.max_breaks_per_cell = lb_config.get('max_breaks_per_cell', 2)
    config.spacing.break_on_punctuation = lb_config.get('break_on_punctuation', False)
    config.spacing.prefer_natural_breaks = lb_config.get('prefer_natural_breaks', False)
    
    return config


def generate_multiple_styles(
    count: int = 5,
    constraints: Optional[Dict[str, Any]] = None
) -> List[StyleConfig]:
    """
    Generate multiple random style configurations.
    
    Args:
        count: Number of styles to generate
        constraints: Optional dictionary of constraints to apply to all styles
                    (same keys as random_select_style arguments)
    
    Returns:
        List of StyleConfig instances
    
    Examples:
        # Generate 5 completely random styles
        styles = generate_multiple_styles(5)
        
        # Generate 10 styles with blue color scheme
        styles = generate_multiple_styles(10, {'background_palette': 'blue'})
        
        # Generate styles with multiple constraints
        styles = generate_multiple_styles(5, {
            'font_category': 'sans-serif',
            'background_pattern': 'striped'
        })
    """
    constraints = constraints or {}
    return [random_select_style(**constraints) for _ in range(count)]


def list_available_options() -> Dict[str, List[str]]:
    """
    List all available style options.
    
    Returns:
        Dictionary with all available options for each category
    """
    return {
        'border_styles': list(BORDER_STYLES.keys()),
        'background_palettes': list(BACKGROUND_COLOR_PALETTES.keys()),
        'background_patterns': BACKGROUND_PATTERNS,
        'font_families': FONT_FAMILIES,
        'font_sizes': FONT_SIZES,
        'font_colors': FONT_COLORS[:10],  # Sample of colors
        'font_categories': ['serif', 'sans-serif', 'monospace'],
        'horizontal_alignments': HORIZONTAL_ALIGNMENTS,
        'vertical_alignments': VERTICAL_ALIGNMENTS,
        'padding_values': PADDING_VALUES[:10],  # Sample of padding values
        'line_break_configs': list(LINE_BREAK_CONFIGS.keys()),
        'style_presets': list(STYLE_PRESETS.keys()),
    }
