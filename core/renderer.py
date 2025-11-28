"""
Table Renderer Module
=====================
Refactored rendering logic from html_render.py into a clean class.
Preserves all core rendering logic.
"""

import os
import json
import random
import asyncio
from pathlib import Path
from html.parser import HTMLParser
from dataclasses import dataclass, field
from typing import Dict, Any, List, Tuple, Optional, Literal

# Import configuration
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.style_config import StyleConfig, BorderConfig, BackgroundConfig, FontConfig, AlignmentConfig, SpacingConfig

# Import image renderer
from image_renderer import render_html_to_image_and_annotate


class TableStructureParser(HTMLParser):
    """
    Parses raw HTML table to extract structure information.
    This is the exact logic from html_render.py TableStructureParser.
    """
    def __init__(self):
        super().__init__()
        self.structure = {
            'rows': [],
            'current_section': None,
            'current_row': None,
            'num_columns': 0
        }
        self.in_cell = False
        
    def handle_starttag(self, tag, attrs):
        if tag in ['thead', 'tbody', 'tfoot']:
            self.structure['current_section'] = tag
        elif tag == 'tr':
            self.structure['current_row'] = {
                'section': self.structure['current_section'] or 'tbody',
                'cells': []
            }
        elif tag in ['td', 'th']:
            attrs_dict = dict(attrs)
            cell_info = {
                'tag': tag,
                'colspan': int(attrs_dict.get('colspan', 1)),
                'rowspan': int(attrs_dict.get('rowspan', 1)),
                'attrs': attrs_dict
            }
            self.structure['current_row']['cells'].append(cell_info)
            self.in_cell = True
    
    def handle_endtag(self, tag):
        if tag == 'tr' and self.structure['current_row']:
            self.structure['rows'].append(self.structure['current_row'])
            num_cols = sum(cell['colspan'] for cell in self.structure['current_row']['cells'])
            self.structure['num_columns'] = max(self.structure['num_columns'], num_cols)
            self.structure['current_row'] = None
        elif tag in ['td', 'th']:
            self.in_cell = False
    
    def get_structure(self) -> Dict:
        return self.structure


class TableStyler(HTMLParser):
    """
    Applies styling to raw HTML table based on configuration.
    This is the exact logic from html_render.py TableStyler.
    """
    def __init__(self, config: StyleConfig, structure: Dict):
        super().__init__()
        self.config = config
        self.structure = structure
        self.result = []
        self.in_cell = False
        self.cell_content = []
        self.current_section = None
        self.current_row_index = 0
        self.current_cell_index = 0
        self.row_index_global = 0
        
        # Cache column_colors for column-based pattern (avoids repeated getattr calls)
        self._column_colors = getattr(self.config.background, 'column_colors', {})
        
    def _get_border_style(self, is_header: bool = False, is_footer: bool = False, 
                          row_idx: int = 0, col_idx: int = 0, has_colspan: bool = False) -> str:
        """Generate border style based on configuration."""
        if self.config.border.style == 'borderless':
            return 'border: none'
        
        if self.config.border.style == 'border':
            return f'border: {self.config.border.width} solid {self.config.border.color}'
        
        parts = []
        border_spec = f'{self.config.border.width} solid {self.config.border.color}'
        
        if self.config.border.remove_inner_borders:
            if self.config.border.keep_outer_border:
                return f'border: {border_spec}'
            return 'border: none'
        
        if not self.config.border.remove_row_borders:
            if is_header and self.config.border.keep_header_row_border:
                parts.append(f'border-top: {border_spec}')
                parts.append(f'border-bottom: {border_spec}')
            else:
                parts.append(f'border-top: {border_spec}')
                parts.append(f'border-bottom: {border_spec}')
        
        if not self.config.border.remove_col_borders:
            if has_colspan and self.config.border.keep_colspan_col_borders:
                parts.append(f'border-left: {border_spec}')
                parts.append(f'border-right: {border_spec}')
            else:
                parts.append(f'border-left: {border_spec}')
                parts.append(f'border-right: {border_spec}')
        
        return '; '.join(parts) if parts else f'border: {border_spec}'
    
    def _get_background_color(self, is_header: bool = False, is_footer: bool = False,
                              row_idx: int = 0, col_idx: int = 0, total_rows: int = 0) -> str:
        """Get background color based on pattern."""
        pattern = self.config.background.pattern
        
        if pattern == 'none':
            return ''
        
        if pattern == 'header' and is_header:
            return self.config.background.header_color
        
        if pattern == 'even-odd':
            return self.config.background.even_color if row_idx % 2 == 0 else self.config.background.odd_color
        
        if pattern == 'striped':
            return self.config.background.odd_color if row_idx % 2 == 1 else ''
        
        if pattern == 'first-last':
            if row_idx == 0:
                return self.config.background.first_color
            if row_idx == total_rows - 1:
                return self.config.background.last_color
            return ''
        
        if pattern == 'random':
            return random.choice(self.config.background.random_colors)
        
        if pattern == 'checkerboard':
            if (row_idx + col_idx) % 2 == 0:
                return self.config.background.even_color
            else:
                return self.config.background.odd_color
        
        if pattern == 'column-based':
            if col_idx in self._column_colors:
                return self._column_colors[col_idx]
            # Fallback to alternating colors
            return self.config.background.even_color if col_idx % 2 == 0 else self.config.background.odd_color
        
        return ''
    
    def _get_font_style(self, is_header: bool = False, is_footer: bool = False) -> Dict[str, str]:
        """Get font styling properties."""
        styles = {
            'font-family': self.config.font.family,
            'font-size': self.config.font.size,
            'color': self.config.font.color
        }
        
        if is_header:
            styles['font-weight'] = self.config.font.header_weight
        elif is_footer:
            styles['font-weight'] = self.config.font.footer_weight
        elif self.config.font.weight == 'random':
            styles['font-weight'] = random.choice(['normal', 'bold'])
        else:
            styles['font-weight'] = self.config.font.weight
        
        if is_header:
            styles['font-style'] = self.config.font.header_style
        elif is_footer:
            styles['font-style'] = self.config.font.footer_style
        elif self.config.font.style == 'random':
            styles['font-style'] = random.choice(['normal', 'italic'])
        else:
            styles['font-style'] = self.config.font.style
        
        if self.config.font.transform == 'random':
            styles['text-transform'] = random.choice(['none', 'uppercase', 'lowercase', 'capitalize'])
        elif self.config.font.transform != 'none':
            styles['text-transform'] = self.config.font.transform
        
        return styles
    
    def _get_alignment_style(self, col_idx: int = 0) -> Dict[str, str]:
        """Get alignment styling properties."""
        styles = {}
        
        if col_idx in self.config.alignment.column_alignments:
            styles['text-align'] = self.config.alignment.column_alignments[col_idx]
        elif self.config.alignment.horizontal == 'random':
            styles['text-align'] = random.choice(['left', 'center', 'right'])
        else:
            styles['text-align'] = self.config.alignment.horizontal
        
        if self.config.alignment.vertical == 'random':
            styles['vertical-align'] = random.choice(['top', 'middle', 'bottom'])
        else:
            styles['vertical-align'] = self.config.alignment.vertical
        
        return styles
    
    def _apply_random_line_breaks(self, text: str) -> str:
        """Randomly insert <br> tags into text based on configuration."""
        if not self.config.spacing.random_line_breaks:
            return text
        
        words = text.split()
        if len(words) <= 1:
            return text
        
        # Get configuration values with defaults
        probability = getattr(self.config.spacing, 'line_break_probability', 0.15)
        min_words_before = getattr(self.config.spacing, 'min_words_before_break', 3)
        max_breaks = getattr(self.config.spacing, 'max_breaks_per_cell', 2)
        break_on_punct = getattr(self.config.spacing, 'break_on_punctuation', False)
        prefer_natural = getattr(self.config.spacing, 'prefer_natural_breaks', False)
        
        result = []
        breaks_inserted = 0
        words_since_break = 0
        
        for i, word in enumerate(words):
            result.append(word)
            words_since_break += 1
            
            if i < len(words) - 1:
                # Check if we can add more breaks
                if breaks_inserted >= max_breaks:
                    result.append(' ')
                    continue
                
                # Check minimum words before break
                if words_since_break < min_words_before:
                    result.append(' ')
                    continue
                
                # Determine if we should break here
                should_break = False
                
                # Prefer natural breaks (after punctuation)
                if prefer_natural or break_on_punct:
                    if word.endswith((',', ';', ':', '-', '–', '—')):
                        should_break = random.random() < (probability * 2)  # Higher chance at punctuation
                    elif word.endswith('.') and i < len(words) - 2:  # Not at end of sentence
                        should_break = random.random() < (probability * 1.5)
                
                # Random break check
                if not should_break and random.random() < probability:
                    should_break = True
                
                if should_break:
                    result.append('<br/>')
                    breaks_inserted += 1
                    words_since_break = 0
                else:
                    result.append(' ')
        
        return ''.join(result).strip()
    
    def handle_starttag(self, tag, attrs):
        if tag in ['thead', 'tbody', 'tfoot']:
            self.current_section = tag
            self.result.append(f'<{tag}>')
            self.current_row_index = 0
            return
        
        if tag == 'table':
            table_styles = {
                'width': self.config.width,
                'border-collapse': self.config.border_collapse,
                'font-family': self.config.font.family
            }
            style_str = '; '.join([f"{k}: {v}" for k, v in table_styles.items()])
            self.result.append(f'<table class="bbox-content-target" style="{style_str}">')
            return
        
        if tag == 'tr':
            self.result.append('<tr>')
            self.current_cell_index = 0
            return
        
        if tag in ['td', 'th']:
            self.in_cell = True
            self.cell_content = []
            
            attrs_dict = dict(attrs)
            is_header = (self.current_section == 'thead' or tag == 'th')
            is_footer = (self.current_section == 'tfoot')
            has_colspan = 'colspan' in attrs_dict
            
            cell_styles = {}
            
            border_style = self._get_border_style(
                is_header, is_footer, 
                self.row_index_global, 
                self.current_cell_index,
                has_colspan
            )
            if border_style:
                for style in border_style.split(';'):
                    if ':' in style:
                        k, v = style.split(':', 1)
                        cell_styles[k.strip()] = v.strip()
            
            bg_color = self._get_background_color(
                is_header, is_footer,
                self.row_index_global,
                self.current_cell_index,
                len(self.structure['rows'])
            )
            if bg_color:
                cell_styles['background-color'] = bg_color
            
            font_styles = self._get_font_style(is_header, is_footer)
            cell_styles.update(font_styles)
            
            alignment_styles = self._get_alignment_style(self.current_cell_index)
            cell_styles.update(alignment_styles)
            
            cell_styles['padding'] = self.config.spacing.padding
            cell_styles['line-height'] = self.config.spacing.line_height
            
            if self.row_index_global in self.config.spacing.row_heights:
                cell_styles['height'] = self.config.spacing.row_heights[self.row_index_global]
            if self.current_cell_index in self.config.spacing.column_widths:
                cell_styles['width'] = self.config.spacing.column_widths[self.current_cell_index]
            
            colspan = f' colspan="{attrs_dict["colspan"]}"' if 'colspan' in attrs_dict else ''
            rowspan = f' rowspan="{attrs_dict["rowspan"]}"' if 'rowspan' in attrs_dict else ''
            
            style_str = '; '.join([f"{k}: {v}" for k, v in cell_styles.items()])
            self.result.append(f'<{tag} style="{style_str}"{colspan}{rowspan}>')
            
            self.current_cell_index += 1
            return
        
        if self.in_cell:
            attrs_str = ' '.join([f'{k}="{v}"' for k, v in attrs])
            self.result.append(f'<{tag}' + (f' {attrs_str}' if attrs_str else '') + '>')
    
    def handle_endtag(self, tag):
        if tag in ['thead', 'tbody', 'tfoot']:
            self.result.append(f'</{tag}>')
            self.current_section = None
            return
        
        if tag == 'tr':
            self.result.append('</tr>')
            self.current_row_index += 1
            self.row_index_global += 1
            return
        
        if tag in ['td', 'th']:
            content = ''.join(self.cell_content)
            content = self._apply_random_line_breaks(content)
            self.result.append(f'<span class="annotated-cell-text">{content}</span>')
            self.result.append(f'</{tag}>')
            self.in_cell = False
            self.cell_content = []
            return
        
        self.result.append(f'</{tag}>')
    
    def handle_data(self, data):
        if self.in_cell:
            self.cell_content.append(data)
    
    def handle_startendtag(self, tag, attrs):
        if self.in_cell:
            attrs_str = ' '.join([f'{k}="{v}"' for k, v in attrs])
            self.result.append(f'<{tag}' + (f' {attrs_str}' if attrs_str else '') + ' />')
    
    def get_styled_html(self) -> str:
        return ''.join(self.result)


class TableRenderer:
    """
    Main renderer class that coordinates parsing, styling, and rendering.
    This extends the logic from html_render.py TableRenderer.
    """
    
    def __init__(self, style_config: Optional[StyleConfig] = None):
        """
        Initialize renderer with a style configuration.
        
        Args:
            style_config: StyleConfig instance. If None, uses default config.
        """
        self.config = style_config or StyleConfig.create_default()
    
    def apply_styles_to_raw_table(self, raw_table_html: str) -> str:
        """
        Apply configured styles to raw HTML table.
        
        Args:
            raw_table_html: Raw HTML table string without styling
            
        Returns:
            Fully styled HTML table string with annotations
        """
        structure_parser = TableStructureParser()
        structure_parser.feed(raw_table_html)
        structure = structure_parser.get_structure()
        
        styler = TableStyler(self.config, structure)
        styler.feed(raw_table_html)
        
        return styler.get_styled_html()
    
    async def render_single(
        self,
        html_path: Path,
        output_dir: Path,
        draw_bboxes: bool = True,
        save_debug_html: bool = False,
        page_width: int = 2480,
        page_height: int = 3508
    ) -> Dict[str, Path]:
        """
        Render single HTML to images and annotations.
        
        Args:
            html_path: Path to HTML file
            output_dir: Output directory
            draw_bboxes: Whether to draw bounding boxes on image
            save_debug_html: Whether to save debug HTML file
            page_width: Page width in pixels
            page_height: Page height in pixels
            
        Returns:
            Dictionary with paths to generated files
        """
        html_path = Path(html_path)
        output_dir = Path(output_dir)
        
        # Read HTML content
        with open(html_path, 'r', encoding='utf-8') as f:
            raw_table_html = f.read()
        
        # Generate output paths
        base_name = html_path.stem
        
        # Create output directories
        (output_dir / 'images' / 'without_annotation').mkdir(parents=True, exist_ok=True)
        (output_dir / 'images' / 'with_annotation').mkdir(parents=True, exist_ok=True)
        (output_dir / 'annotations').mkdir(parents=True, exist_ok=True)
        
        result_paths = {}
        
        # Render without bboxes
        image_path_clean = output_dir / 'images' / 'without_annotation' / f'{base_name}.png'
        annotation_path = output_dir / 'annotations' / f'{base_name}.json'
        
        await self.render_table(
            raw_table_html,
            str(image_path_clean),
            str(annotation_path),
            page_width=page_width,
            page_height=page_height,
            draw_bboxes=False,
            save_debug_html=False
        )
        result_paths['image_clean'] = image_path_clean
        result_paths['annotation'] = annotation_path
        
        # Render with bboxes if requested
        if draw_bboxes:
            image_path_annotated = output_dir / 'images' / 'with_annotation' / f'{base_name}_annotated.png'
            
            await self.render_table(
                raw_table_html,
                str(image_path_annotated),
                str(annotation_path),  # Reuse same annotation file
                page_width=page_width,
                page_height=page_height,
                draw_bboxes=True,
                save_debug_html=save_debug_html
            )
            result_paths['image_annotated'] = image_path_annotated
        
        # Save debug HTML if requested
        if save_debug_html:
            debug_dir = output_dir / 'debug_html'
            debug_dir.mkdir(parents=True, exist_ok=True)
            debug_path = debug_dir / f'{base_name}_debug.html'
            result_paths['debug_html'] = debug_path
        
        return result_paths
    
    async def render_batch(
        self,
        html_files: List[Path],
        output_dir: Path,
        style_variations: int = 1,
        draw_bboxes: bool = True,
        save_debug_html: bool = False
    ) -> List[Dict]:
        """
        Render multiple HTMLs with optional style variations.
        
        Args:
            html_files: List of paths to HTML files
            output_dir: Output directory
            style_variations: Number of style variations per HTML
            draw_bboxes: Whether to draw bounding boxes
            save_debug_html: Whether to save debug HTML
            
        Returns:
            List of dictionaries with paths to generated files
        """
        output_dir = Path(output_dir)
        results = []
        
        for html_file in html_files:
            html_file = Path(html_file)
            
            for style_idx in range(style_variations):
                # Use variation config if multiple styles
                if style_variations > 1:
                    config = self.config.create_variation()
                    renderer = TableRenderer(config)
                else:
                    renderer = self
                
                # Modify base name for style variations
                if style_variations > 1:
                    base_name = f"{html_file.stem}_style_{style_idx}"
                else:
                    base_name = html_file.stem
                
                # Read and render
                with open(html_file, 'r', encoding='utf-8') as f:
                    raw_table_html = f.read()
                
                # Create paths
                (output_dir / 'images' / 'without_annotation').mkdir(parents=True, exist_ok=True)
                (output_dir / 'images' / 'with_annotation').mkdir(parents=True, exist_ok=True)
                (output_dir / 'annotations').mkdir(parents=True, exist_ok=True)
                
                image_path_clean = output_dir / 'images' / 'without_annotation' / f'{base_name}.png'
                annotation_path = output_dir / 'annotations' / f'{base_name}.json'
                
                result = {
                    'source': html_file,
                    'style_index': style_idx,
                    'image_clean': image_path_clean,
                    'annotation': annotation_path
                }
                
                # Render without bboxes
                await renderer.render_table(
                    raw_table_html,
                    str(image_path_clean),
                    str(annotation_path),
                    draw_bboxes=False,
                    save_debug_html=False
                )
                
                # Render with bboxes if requested
                if draw_bboxes:
                    image_path_annotated = output_dir / 'images' / 'with_annotation' / f'{base_name}_annotated.png'
                    
                    await renderer.render_table(
                        raw_table_html,
                        str(image_path_annotated),
                        str(annotation_path),
                        draw_bboxes=True,
                        save_debug_html=save_debug_html
                    )
                    result['image_annotated'] = image_path_annotated
                
                results.append(result)
        
        return results
    
    async def render_table(
        self,
        raw_table_html: str,
        output_image_path: str,
        output_annotation_path: str,
        page_width: int = 2480,
        page_height: int = 3508,
        draw_bboxes: bool = True,
        save_debug_html: bool = True
    ) -> Dict[str, Any]:
        """
        Render a raw HTML table to image with annotations.
        This is the exact logic from html_render.py TableRenderer.render_table.
        
        Args:
            raw_table_html: Raw HTML table string without styling
            output_image_path: Path for output PNG image
            output_annotation_path: Path for output JSON annotations
            page_width: Page width in pixels (default: A4 at 300 DPI)
            page_height: Page height in pixels (default: A4 at 300 DPI)
            draw_bboxes: Whether to draw bounding boxes on image
            save_debug_html: Whether to save debug HTML file
            
        Returns:
            Dictionary containing annotation data
        """
        os.makedirs(os.path.dirname(output_image_path) or '.', exist_ok=True)
        
        styled_table = self.apply_styles_to_raw_table(raw_table_html)
        
        margin = 100
        table_bounds = {
            'x': margin,
            'y': margin,
            'width': page_width - 2 * margin,
            'height': page_height - 2 * margin
        }
        
        positioned_table = self._wrap_with_position(styled_table, table_bounds)
        final_html = self._create_html_document(positioned_table, page_width, page_height)
        
        if save_debug_html:
            html_path = output_image_path.replace('.png', '_debug.html')
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(final_html)
            print(f"Debug HTML saved: {html_path}")
        
        await render_html_to_image_and_annotate(
            final_html,
            output_image_path,
            output_annotation_path,
            page_width,
            page_height,
            draw_bboxes
        )
        
        with open(output_annotation_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _wrap_with_position(self, table_html: str, bounds: Dict[str, int]) -> str:
        """Wrap table with positioning container."""
        container_style = (
            f"position: absolute; "
            f"left: {bounds['x']}px; top: {bounds['y']}px; "
            f"width: {bounds['width']}px; height: {bounds['height']}px; "
            f"overflow: hidden;"
        )
        return f'<div class="annotated-element" data-element-type="table" style="{container_style}">{table_html}</div>'
    
    def _create_html_document(self, content: str, width: int, height: int) -> str:
        """Create complete HTML document."""
        return f"""
        <!DOCTYPE html>
        <html lang="vi">
        <head>
            <meta charset="UTF-8">
            <title>Table Annotation</title>
            <style>
                body {{ margin: 0; padding: 0; background-color: #CCC; }}
                .page {{
                    width: {width}px;
                    height: {height}px;
                    background-color: white;
                    position: relative;
                    box-shadow: 0 0 10px rgba(0,0,0,0.5);
                    margin: 20px auto;
                    overflow: hidden;
                }}
                .annotated-element {{ box-sizing: border-box; }}
                .bbox-content-target {{ /* Target for bbox measurements */ }}
                .annotated-cell-text {{ display: inline-block; }}
            </style>
        </head>
        <body>
            <div class="page">{content}</div>
        </body>
        </html>
        """


async def render_raw_table_with_config(
    raw_table_html: str,
    output_image_path: str,
    output_annotation_path: str,
    config: Optional[StyleConfig] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Convenience function to render table with custom configuration.
    
    Args:
        raw_table_html: Raw HTML table without styling
        output_image_path: Output PNG path
        output_annotation_path: Output JSON path
        config: StyleConfig instance (optional)
        **kwargs: Additional arguments passed to renderer
        
    Returns:
        Annotation dictionary
    """
    renderer = TableRenderer(config)
    return await renderer.render_table(
        raw_table_html,
        output_image_path,
        output_annotation_path,
        **kwargs
    )
