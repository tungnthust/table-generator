#!/usr/bin/env python3
"""
Augment and Render Script
=========================
Combined script for augmentation and rendering pipeline.

Usage example:
    python scripts/augment_and_render.py --input-dir html_input --num-augments 5 --deviation 0.6 --num-styles 2
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.augment_config import AugmentConfig
from config.style_config import StyleConfig
from core.augmenter import TableAugmenter
from core.renderer import TableRenderer


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


async def render_files(html_files: list, output_dir: Path, config: StyleConfig, 
                       num_styles: int = 1, draw_bboxes: bool = True):
    """Render HTML files to images."""
    renderer = TableRenderer(config)
    
    results = await renderer.render_batch(
        html_files, 
        output_dir, 
        style_variations=num_styles,
        draw_bboxes=draw_bboxes
    )
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description='Augment and render HTML tables',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python scripts/augment_and_render.py --input-dir html_input --num-augments 5 --deviation 0.6
    python scripts/augment_and_render.py --input sample.html --num-augments 3 --num-styles 2
    python scripts/augment_and_render.py --input-dir html_input --style-preset borderless
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
        default=Path('output'),
        help='Output directory (default: output)'
    )
    
    # Augmentation arguments
    parser.add_argument(
        '--num-augments', '-n',
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
    
    # Style arguments
    StyleConfig.add_cli_arguments(parser)
    
    # Additional rendering options
    parser.add_argument(
        '--no-bbox',
        action='store_true',
        help='Do not generate images with bounding boxes'
    )
    parser.add_argument(
        '--skip-augment',
        action='store_true',
        help='Skip augmentation, only render original HTML files'
    )
    parser.add_argument(
        '--skip-render',
        action='store_true',
        help='Skip rendering, only generate augmented HTML files'
    )
    
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
    
    # Create output directories
    augmented_dir = args.output_dir / 'augmented_html'
    augmented_dir.mkdir(parents=True, exist_ok=True)
    
    # =========================================================================
    # PHASE 1: AUGMENTATION
    # =========================================================================
    
    if not args.skip_augment:
        print("\n" + "="*50)
        print("PHASE 1: AUGMENTATION")
        print("="*50)
        
        # Create augmentation config
        augment_config = AugmentConfig(
            num_augmentations=args.num_augments,
            deviation_level=args.deviation,
            batch_size=args.batch_size,
            api_key=args.api_key or "",
            model_id=args.model_id
        )
        
        # Check API key
        if not augment_config.api_key:
            print("Error: No API key provided. Set GOOGLE_API_KEY environment variable or use --api-key")
            sys.exit(1)
        
        print(f"\nAugmentation Configuration:")
        print(f"  - Number of augmentations per file: {augment_config.num_augmentations}")
        print(f"  - Deviation level: {augment_config.deviation_level}")
        print(f"  - Batch size: {augment_config.batch_size}")
        print(f"  - Model: {augment_config.model_id}")
        print()
        
        # Create augmenter
        try:
            augmenter = TableAugmenter(augment_config)
        except Exception as e:
            print(f"Error initializing augmenter: {e}")
            sys.exit(1)
        
        # Process files
        augmented_files = []
        for html_file in html_files:
            print(f"\nAugmenting: {html_file.name}")
            
            try:
                generated = augmenter.augment_batch([html_file], augmented_dir)
                augmented_files.extend(generated)
                print(f"  Generated {len(generated)} augmented file(s)")
            except Exception as e:
                print(f"  Error augmenting {html_file.name}: {e}")
        
        print(f"\nTotal augmented files: {len(augmented_files)}")
    else:
        print("\n[Skipping augmentation]")
        augmented_files = list(html_files)
    
    # =========================================================================
    # PHASE 2: RENDERING
    # =========================================================================
    
    if not args.skip_render:
        print("\n" + "="*50)
        print("PHASE 2: RENDERING")
        print("="*50)
        
        # Create style configuration
        try:
            style_config = StyleConfig.from_cli_args(args)
        except Exception as e:
            print(f"Error loading style configuration: {e}")
            sys.exit(1)
        
        num_styles = getattr(args, 'num_styles', 1)
        
        print(f"\nRendering Configuration:")
        print(f"  - Style preset: {getattr(args, 'style_preset', 'default')}")
        print(f"  - Number of style variations: {num_styles}")
        print(f"  - Draw bounding boxes: {not args.no_bbox}")
        print()
        
        # Determine files to render
        if not args.skip_augment:
            files_to_render = augmented_files
        else:
            files_to_render = html_files
        
        # Render files
        try:
            results = asyncio.run(render_files(
                files_to_render,
                args.output_dir,
                style_config,
                num_styles=num_styles,
                draw_bboxes=not args.no_bbox
            ))
            
            print(f"\nTotal rendered: {len(results)} file(s)")
            
        except Exception as e:
            print(f"Error during rendering: {e}")
            sys.exit(1)
    else:
        print("\n[Skipping rendering]")
    
    # =========================================================================
    # SUMMARY
    # =========================================================================
    
    print("\n" + "="*50)
    print("PIPELINE COMPLETE")
    print("="*50)
    print(f"\nOutput directory: {args.output_dir}")
    print(f"  - Augmented HTML: {augmented_dir}/")
    if not args.skip_render:
        print(f"  - Images (clean): {args.output_dir}/images/without_annotation/")
        print(f"  - Images (annotated): {args.output_dir}/images/with_annotation/")
        print(f"  - Annotations: {args.output_dir}/annotations/")


if __name__ == '__main__':
    main()
