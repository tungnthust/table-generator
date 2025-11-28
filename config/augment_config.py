"""
Augmentation Configuration Module
=================================
Configuration for HTML table augmentation using LLM.
"""

import os
import json
import argparse
from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class AugmentConfig:
    """
    Configuration class for table augmentation.
    
    Attributes:
        num_augmentations: Number of new HTML variations to generate per input
        deviation_level: 0.0-1.0 deviation level for LLM (higher = more creative)
        batch_size: Batch size for LLM processing
        api_key: API key for Google GenAI (can be set via env var GOOGLE_API_KEY)
        model_id: Model ID to use for augmentation
    """
    num_augmentations: int = 5
    deviation_level: float = 0.5
    batch_size: int = 15
    api_key: str = ""
    model_id: str = "gemini-2.5-flash-preview-09-2025"
    
    def __post_init__(self):
        """Load API key from environment if not provided."""
        if not self.api_key:
            self.api_key = os.environ.get("GOOGLE_API_KEY", "")
        
        # Validate deviation_level
        if not 0.0 <= self.deviation_level <= 1.0:
            raise ValueError("deviation_level must be between 0.0 and 1.0")
        
        # Validate num_augmentations
        if self.num_augmentations < 1:
            raise ValueError("num_augmentations must be at least 1")
        
        # Validate batch_size
        if self.batch_size < 1:
            raise ValueError("batch_size must be at least 1")
    
    @classmethod
    def from_cli_args(cls, args: argparse.Namespace) -> 'AugmentConfig':
        """
        Create configuration from CLI arguments.
        
        Args:
            args: Parsed command line arguments
            
        Returns:
            AugmentConfig instance
        """
        return cls(
            num_augmentations=getattr(args, 'num', cls.num_augmentations),
            deviation_level=getattr(args, 'deviation', cls.deviation_level),
            batch_size=getattr(args, 'batch_size', cls.batch_size),
            api_key=getattr(args, 'api_key', "") or os.environ.get("GOOGLE_API_KEY", ""),
            model_id=getattr(args, 'model_id', cls.model_id)
        )
    
    @classmethod
    def from_json(cls, json_path: str) -> 'AugmentConfig':
        """
        Load configuration from JSON file.
        
        Args:
            json_path: Path to JSON configuration file
            
        Returns:
            AugmentConfig instance
        """
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return cls(**data)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'AugmentConfig':
        """
        Create configuration from dictionary.
        
        Args:
            data: Dictionary containing configuration values
            
        Returns:
            AugmentConfig instance
        """
        return cls(**{k: v for k, v in data.items() if hasattr(cls, k)})
    
    def to_json(self, json_path: str) -> None:
        """
        Save configuration to JSON file.
        
        Args:
            json_path: Path to save JSON configuration file
        """
        # Don't save api_key to file for security
        data = asdict(self)
        data.pop('api_key', None)
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    
    def to_dict(self) -> dict:
        """
        Convert configuration to dictionary.
        
        Returns:
            Dictionary representation of configuration
        """
        return asdict(self)
    
    @staticmethod
    def add_cli_arguments(parser: argparse.ArgumentParser) -> None:
        """
        Add augmentation arguments to an argument parser.
        
        Args:
            parser: ArgumentParser to add arguments to
        """
        parser.add_argument(
            '--num', '-n',
            type=int,
            default=5,
            help='Number of augmented versions to generate per input (default: 5)'
        )
        parser.add_argument(
            '--deviation', '-d',
            type=float,
            default=0.5,
            help='Deviation level 0.0-1.0 for LLM creativity (default: 0.5)'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=15,
            help='Batch size for LLM processing (default: 15)'
        )
        parser.add_argument(
            '--api-key',
            type=str,
            default=None,
            help='Google API key (or set GOOGLE_API_KEY env var)'
        )
        parser.add_argument(
            '--model-id',
            type=str,
            default='gemini-2.5-flash-preview-09-2025',
            help='Model ID for augmentation'
        )
