"""
Style Configuration Module
==========================
Configuration for table rendering styles.
Reuses and extends TableStyleConfig from html_render.py.
"""

import json
import random
import argparse
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Literal, Optional, Any


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


@dataclass
class BackgroundConfig:
    """Configuration for cell background colors."""
    pattern: Literal['none', 'header', 'even-odd', 'first-last', 'striped', 'random'] = 'header'
    header_color: str = '#F2F2F2'
    even_color: str = '#FFFFFF'
    odd_color: str = '#F9F9F9'
    first_color: str = '#E8E8E8'
    last_color: str = '#E8E8E8'
    random_colors: List[str] = field(default_factory=lambda: ['#F2F2F2', '#E8F4F8', '#FFF8E8'])


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
    footer_weight: str = 'bold'
    footer_style: str = 'normal'


@dataclass
class AlignmentConfig:
    """Configuration for text alignment."""
    horizontal: Literal['left', 'center', 'right', 'random'] = 'center'
    vertical: Literal['top', 'middle', 'bottom', 'random'] = 'middle'
    
    column_alignments: Dict[int, str] = field(default_factory=dict)


@dataclass
class SpacingConfig:
    """Configuration for spacing and dimensions."""
    padding: str = '8px'
    cell_spacing: str = '0'
    line_height: str = '1.4'
    
    row_heights: Dict[int, str] = field(default_factory=dict)
    column_widths: Dict[int, str] = field(default_factory=dict)
    
    random_line_breaks: bool = False
    line_break_probability: float = 0.15


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
    def create_random(cls) -> 'StyleConfig':
        """Create a random style configuration."""
        config = cls()
        
        # Random border style
        config.border.style = random.choice(['border', 'borderless', 'partly-borderless'])
        config.border.width = random.choice(['1px', '2px', '3px'])
        config.border.color = random.choice(['black', '#333333', '#666666'])
        
        # Random background
        config.background.pattern = random.choice(['none', 'header', 'even-odd', 'striped'])
        
        # Random font
        config.font.family = random.choice([
            'Times New Roman, serif',
            'Arial, sans-serif',
            'Georgia, serif',
            'Helvetica, sans-serif'
        ])
        config.font.size = random.choice(['32px', '36px', '40px'])
        
        # Random alignment
        config.alignment.horizontal = random.choice(['left', 'center', 'right'])
        
        # Random spacing
        config.spacing.padding = random.choice(['6px', '8px', '10px', '12px'])
        
        return config
    
    @classmethod
    def from_preset(cls, preset: str) -> 'StyleConfig':
        """
        Create configuration from a named preset.
        
        Args:
            preset: One of 'default', 'borderless', 'minimal', 'random'
            
        Returns:
            StyleConfig instance
        """
        presets = {
            'default': cls.create_default,
            'borderless': cls.create_borderless,
            'minimal': cls.create_minimal,
            'random': cls.create_random
        }
        
        if preset not in presets:
            raise ValueError(f"Unknown preset: {preset}. Available: {list(presets.keys())}")
        
        return presets[preset]()
    
    # ===== VARIATION METHODS =====
    
    def create_variation(self) -> 'StyleConfig':
        """
        Create a random variation of this style within reasonable bounds.
        
        Returns:
            New StyleConfig with random variations
        """
        # Create a copy
        config = StyleConfig.from_dict(self.to_dict())
        
        # Apply random variations
        if random.random() > 0.5:
            config.border.width = random.choice(['1px', '2px', '3px'])
        
        if random.random() > 0.5:
            config.font.size = random.choice(['32px', '36px', '40px'])
        
        if random.random() > 0.5:
            config.spacing.padding = random.choice(['6px', '8px', '10px', '12px'])
        
        if random.random() > 0.7:
            config.alignment.horizontal = random.choice(['left', 'center', 'right'])
        
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
        parser.add_argument(
            '--style-preset',
            type=str,
            choices=['default', 'borderless', 'minimal', 'random'],
            default='default',
            help='Style preset to use (default: default)'
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
            return cls.from_json(style_config_path)
        
        # Otherwise use preset
        preset = getattr(args, 'style_preset', 'default')
        return cls.from_preset(preset)
