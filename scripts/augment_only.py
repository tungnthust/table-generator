#!/usr/bin/env python3
"""
Augment Only Script
===================
Script dedicated for augmentation only.
Generates augmented HTML variations from input HTML files.

Usage examples:
    python scripts/augment_only.py --input-dir html_input --output-dir output/augmented_html --num 5 --deviation 0.7
    python scripts/augment_only.py --input html_input/sample_1.html --num 3
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.augment_config import AugmentConfig
from core.augmenter import TableAugmenter


def find_html_files(input_path: Path) -> list:
    """Find all HTML files in a directory or return single file."""
    if input_path.is_file():
        if input_path.suffix.lower() in ['.html', '.htm']:
            return [input_path]
        else:
            raise ValueError(f"Input file must be HTML: {input_path}")
    elif input_path.is_dir():
        html_files = list(input_path.glob('*.html')) + list(input_path.glob('*.htm'))
        if not html_files:
            raise ValueError(f"No HTML files found in directory: {input_path}")
        return sorted(html_files)
    else:
        raise ValueError(f"Input path does not exist: {input_path}")


def main():
    parser = argparse.ArgumentParser(
        description='Augment HTML tables using LLM',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python scripts/augment_only.py --input-dir html_input --num 5 --deviation 0.7
    python scripts/augment_only.py --input html_input/sample_1.html --num 3
    python scripts/augment_only.py --input-dir html_input --output-dir output/augmented_html
        """
    )
    
    # Input/Output arguments
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        '--input-dir',
        type=Path,
        help='Directory containing input HTML files'
    )
    input_group.add_argument(
        '--input',
        type=Path,
        help='Single input HTML file'
    )
    
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=Path('output/augmented_html'),
        help='Output directory for augmented HTML files (default: output/augmented_html)'
    )
    
    # Add augmentation config arguments
    AugmentConfig.add_cli_arguments(parser)
    
    # Parse arguments
    args = parser.parse_args()
    
    # Determine input path
    input_path = args.input_dir if args.input_dir else args.input
    
    # Find HTML files
    try:
        html_files = find_html_files(input_path)
        print(f"Found {len(html_files)} HTML file(s) to process")
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    # Create configuration
    config = AugmentConfig.from_cli_args(args)
    
    # Check API key
    if not config.api_key:
        print("Error: No API key provided. Set GOOGLE_API_KEY environment variable or use --api-key")
        sys.exit(1)
    
    print(f"\nAugmentation Configuration:")
    print(f"  - Number of augmentations per file: {config.num_augmentations}")
    print(f"  - Deviation level: {config.deviation_level}")
    print(f"  - Batch size: {config.batch_size}")
    print(f"  - Model: {config.model_id}")
    print(f"  - Output directory: {args.output_dir}")
    print()
    
    # Create augmenter
    try:
        augmenter = TableAugmenter(config)
    except Exception as e:
        print(f"Error initializing augmenter: {e}")
        sys.exit(1)
    
    # Create output directory
    args.output_dir.mkdir(parents=True, exist_ok=True)
    
    # Process files
    total_generated = 0
    for html_file in html_files:
        print(f"\nProcessing: {html_file.name}")
        
        try:
            generated = augmenter.augment_batch([html_file], args.output_dir)
            total_generated += len(generated)
            print(f"  Generated {len(generated)} augmented file(s)")
        except Exception as e:
            print(f"  Error processing {html_file.name}: {e}")
    
    print(f"\n{'='*50}")
    print(f"Augmentation complete!")
    print(f"  Total files generated: {total_generated}")
    print(f"  Output directory: {args.output_dir}")


if __name__ == '__main__':
    main()
