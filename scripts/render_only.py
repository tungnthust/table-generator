#!/usr/bin/env python3
"""
Render Only Script
==================
Script dedicated for rendering HTML tables to images with annotations.

Usage examples:
    python scripts/render_only.py --input-dir output/augmented_html --output-dir output
    python scripts/render_only.py --input output/augmented_html/sample_1_aug_0.html --style-preset minimal
    python scripts/render_only.py --input-dir html_input --style-config my_style.json --num-styles 3
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.style_config import StyleConfig
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
                       num_styles: int = 1, draw_bboxes: bool = True, 
                       save_debug_html: bool = False):
    """Render HTML files to images."""
    renderer = TableRenderer(config)
    
    total_rendered = 0
    
    for html_file in html_files:
        html_file = Path(html_file)
        print(f"\nRendering: {html_file.name}")
        
        try:
            if num_styles > 1:
                # Generate multiple style variations
                results = await renderer.render_batch(
                    [html_file], 
                    output_dir, 
                    style_variations=num_styles,
                    draw_bboxes=draw_bboxes,
                    save_debug_html=save_debug_html
                )
                total_rendered += len(results)
                print(f"  Generated {len(results)} style variation(s)")
            else:
                # Single style
                result = await renderer.render_single(
                    html_file,
                    output_dir,
                    draw_bboxes=draw_bboxes,
                    save_debug_html=save_debug_html
                )
                total_rendered += 1
                print(f"  Generated: {result['image_clean'].name}")
                
        except Exception as e:
            print(f"  Error rendering {html_file.name}: {e}")
    
    return total_rendered


def main():
    parser = argparse.ArgumentParser(
        description='Render HTML tables to images with annotations',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python scripts/render_only.py --input-dir output/augmented_html --output-dir output
    python scripts/render_only.py --input sample.html --style-preset minimal
    python scripts/render_only.py --input-dir html_input --style-config my_style.json
    python scripts/render_only.py --input-dir html_input --num-styles 3
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
        help='Output directory for rendered images and annotations (default: output)'
    )
    
    # Add style config arguments
    StyleConfig.add_cli_arguments(parser)
    
    # Additional rendering options
    parser.add_argument(
        '--no-bbox',
        action='store_true',
        help='Do not generate images with bounding boxes'
    )
    parser.add_argument(
        '--save-debug',
        action='store_true',
        help='Save debug HTML files'
    )
    parser.add_argument(
        '--page-width',
        type=int,
        default=2480,
        help='Page width in pixels (default: 2480 for A4 at 300 DPI)'
    )
    parser.add_argument(
        '--page-height',
        type=int,
        default=3508,
        help='Page height in pixels (default: 3508 for A4 at 300 DPI)'
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Determine input path
    input_path = args.input_dir if args.input_dir else args.input
    
    # Find HTML files
    try:
        html_files = find_html_files(input_path)
        print(f"Found {len(html_files)} HTML file(s) to render")
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    # Create style configuration
    try:
        config = StyleConfig.from_cli_args(args)
    except Exception as e:
        print(f"Error loading style configuration: {e}")
        sys.exit(1)
    
    num_styles = getattr(args, 'num_styles', 1)
    
    print(f"\nRendering Configuration:")
    print(f"  - Style preset: {getattr(args, 'style_preset', 'default')}")
    if getattr(args, 'style_config', None):
        print(f"  - Style config file: {args.style_config}")
    print(f"  - Number of style variations: {num_styles}")
    print(f"  - Draw bounding boxes: {not args.no_bbox}")
    print(f"  - Save debug HTML: {args.save_debug}")
    print(f"  - Page size: {args.page_width}x{args.page_height}")
    print(f"  - Output directory: {args.output_dir}")
    print()
    
    # Create output directory
    args.output_dir.mkdir(parents=True, exist_ok=True)
    
    # Run rendering
    try:
        total_rendered = asyncio.run(render_files(
            html_files,
            args.output_dir,
            config,
            num_styles=num_styles,
            draw_bboxes=not args.no_bbox,
            save_debug_html=args.save_debug
        ))
        
        print(f"\n{'='*50}")
        print(f"Rendering complete!")
        print(f"  Total files rendered: {total_rendered}")
        print(f"  Output structure:")
        print(f"    - Images (clean): {args.output_dir}/images/without_annotation/")
        print(f"    - Images (annotated): {args.output_dir}/images/with_annotation/")
        print(f"    - Annotations: {args.output_dir}/annotations/")
        if args.save_debug:
            print(f"    - Debug HTML: {args.output_dir}/debug_html/")
            
    except Exception as e:
        print(f"Error during rendering: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
