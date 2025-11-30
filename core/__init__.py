"""
Core module for table-generator.
Contains the main augmentation and rendering logic.
"""

from .augmenter import TableAugmenter
from .renderer import TableRenderer

__all__ = ['TableAugmenter', 'TableRenderer']
