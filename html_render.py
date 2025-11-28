"""
Professional Table Renderer with Configurable Styling
======================================================
This module provides a flexible system for rendering HTML tables with
extensive styling options and annotation extraction.

Main components:
- TableStyleConfig: Configuration class for all styling options
- TableStyler: Applies styles to raw HTML tables
- TableRenderer: Handles the rendering and annotation extraction
"""

import json
import os
import random
from dataclasses import dataclass, field
from typing import Dict, Any, List, Tuple, Optional, Literal
from html.parser import HTMLParser
import asyncio

# Assume image_renderer.py is in the same directory or importable
from image_renderer import render_html_to_image_and_annotate


# ============================================================================
# CONFIGURATION CLASSES
# ============================================================================

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
    keep_colspan_col_borders: bool = True  # Keep col borders under cells with colspan


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
    
    # Special styling for different sections
    header_weight: str = 'bold'
    header_style: str = 'normal'
    footer_weight: str = 'bold'
    footer_style: str = 'normal'


@dataclass
class AlignmentConfig:
    """Configuration for text alignment."""
    horizontal: Literal['left', 'center', 'right', 'random'] = 'center'
    vertical: Literal['top', 'middle', 'bottom', 'random'] = 'middle'
    
    # Column-specific alignment (override)
    column_alignments: Dict[int, str] = field(default_factory=dict)  # {col_index: 'left'|'center'|'right'}


@dataclass
class SpacingConfig:
    """Configuration for spacing and dimensions."""
    padding: str = '8px'
    cell_spacing: str = '0'
    line_height: str = '1.4'
    
    # Row/column specific dimensions
    row_heights: Dict[int, str] = field(default_factory=dict)  # {row_index: '50px'}
    column_widths: Dict[int, str] = field(default_factory=dict)  # {col_index: '100px'}
    
    # Random line breaks in cell content
    random_line_breaks: bool = False
    line_break_probability: float = 0.15  # Chance to add <br> between words


@dataclass
class TableStyleConfig:
    """Main configuration class combining all styling options."""
    border: BorderConfig = field(default_factory=BorderConfig)
    background: BackgroundConfig = field(default_factory=BackgroundConfig)
    font: FontConfig = field(default_factory=FontConfig)
    alignment: AlignmentConfig = field(default_factory=AlignmentConfig)
    spacing: SpacingConfig = field(default_factory=SpacingConfig)
    
    # Table-level properties
    width: str = '100%'
    border_collapse: str = 'collapse'
    
    @classmethod
    def create_default(cls) -> 'TableStyleConfig':
        """Create default configuration matching original style."""
        return cls()
    
    @classmethod
    def create_borderless(cls) -> 'TableStyleConfig':
        """Create borderless table configuration."""
        config = cls()
        config.border.style = 'borderless'
        return config
    
    @classmethod
    def create_minimal(cls) -> 'TableStyleConfig':
        """Create minimal style with only outer borders."""
        config = cls()
        config.border.style = 'partly-borderless'
        config.border.remove_inner_borders = True
        config.border.keep_outer_border = True
        config.background.pattern = 'none'
        return config


# ============================================================================
# TABLE PARSER AND STYLER
# ============================================================================

class TableStructureParser(HTMLParser):
    """
    Parses raw HTML table to extract structure information.
    This is used to analyze the table before applying styles.
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
    Handles all style variations and wraps cell content for annotations.
    """
    def __init__(self, config: TableStyleConfig, structure: Dict):
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
        
    def _get_border_style(self, is_header: bool = False, is_footer: bool = False, 
                          row_idx: int = 0, col_idx: int = 0, has_colspan: bool = False) -> str:
        """Generate border style based on configuration."""
        if self.config.border.style == 'borderless':
            return 'border: none'
        
        if self.config.border.style == 'border':
            return f'border: {self.config.border.width} solid {self.config.border.color}'
        
        # Partly-borderless logic
        parts = []
        border_spec = f'{self.config.border.width} solid {self.config.border.color}'
        
        if self.config.border.remove_inner_borders:
            # Only outer borders
            if self.config.border.keep_outer_border:
                return f'border: {border_spec}'
            return 'border: none'
        
        # Custom border combinations
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
                              row_idx: int = 0, total_rows: int = 0) -> str:
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
        
        return ''
    
    def _get_font_style(self, is_header: bool = False, is_footer: bool = False) -> Dict[str, str]:
        """Get font styling properties."""
        styles = {
            'font-family': self.config.font.family,
            'font-size': self.config.font.size,
            'color': self.config.font.color
        }
        
        # Font weight
        if is_header:
            styles['font-weight'] = self.config.font.header_weight
        elif is_footer:
            styles['font-weight'] = self.config.font.footer_weight
        elif self.config.font.weight == 'random':
            styles['font-weight'] = random.choice(['normal', 'bold'])
        else:
            styles['font-weight'] = self.config.font.weight
        
        # Font style
        if is_header:
            styles['font-style'] = self.config.font.header_style
        elif is_footer:
            styles['font-style'] = self.config.font.footer_style
        elif self.config.font.style == 'random':
            styles['font-style'] = random.choice(['normal', 'italic'])
        else:
            styles['font-style'] = self.config.font.style
        
        # Text transform
        if self.config.font.transform == 'random':
            styles['text-transform'] = random.choice(['none', 'uppercase', 'lowercase', 'capitalize'])
        elif self.config.font.transform != 'none':
            styles['text-transform'] = self.config.font.transform
        
        return styles
    
    def _get_alignment_style(self, col_idx: int = 0) -> Dict[str, str]:
        """Get alignment styling properties."""
        styles = {}
        
        # Horizontal alignment
        if col_idx in self.config.alignment.column_alignments:
            styles['text-align'] = self.config.alignment.column_alignments[col_idx]
        elif self.config.alignment.horizontal == 'random':
            styles['text-align'] = random.choice(['left', 'center', 'right'])
        else:
            styles['text-align'] = self.config.alignment.horizontal
        
        # Vertical alignment
        if self.config.alignment.vertical == 'random':
            styles['vertical-align'] = random.choice(['top', 'middle', 'bottom'])
        else:
            styles['vertical-align'] = self.config.alignment.vertical
        
        return styles
    
    def _apply_random_line_breaks(self, text: str) -> str:
        """Randomly insert <br> tags into text."""
        if not self.config.spacing.random_line_breaks:
            return text
        
        words = text.split()
        if len(words) <= 1:
            return text
        
        result = []
        for i, word in enumerate(words):
            result.append(word)
            if i < len(words) - 1 and random.random() < self.config.spacing.line_break_probability:
                result.append('<br/>')
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
            
            # Build cell styles
            cell_styles = {}
            
            # Border
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
            
            # Background
            bg_color = self._get_background_color(
                is_header, is_footer,
                self.row_index_global,
                len(self.structure['rows'])
            )
            if bg_color:
                cell_styles['background-color'] = bg_color
            
            # Font
            font_styles = self._get_font_style(is_header, is_footer)
            cell_styles.update(font_styles)
            
            # Alignment
            alignment_styles = self._get_alignment_style(self.current_cell_index)
            cell_styles.update(alignment_styles)
            
            # Spacing
            cell_styles['padding'] = self.config.spacing.padding
            cell_styles['line-height'] = self.config.spacing.line_height
            
            # Row/column specific dimensions
            if self.row_index_global in self.config.spacing.row_heights:
                cell_styles['height'] = self.config.spacing.row_heights[self.row_index_global]
            if self.current_cell_index in self.config.spacing.column_widths:
                cell_styles['width'] = self.config.spacing.column_widths[self.current_cell_index]
            
            # Preserve colspan/rowspan
            colspan = f' colspan="{attrs_dict["colspan"]}"' if 'colspan' in attrs_dict else ''
            rowspan = f' rowspan="{attrs_dict["rowspan"]}"' if 'rowspan' in attrs_dict else ''
            
            style_str = '; '.join([f"{k}: {v}" for k, v in cell_styles.items()])
            self.result.append(f'<{tag} style="{style_str}"{colspan}{rowspan}>')
            
            self.current_cell_index += 1
            return
        
        # Preserve other tags (like <br>)
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
            # Apply random line breaks and wrap content
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


# ============================================================================
# TABLE RENDERER
# ============================================================================

class TableRenderer:
    """
    Main renderer class that coordinates parsing, styling, and rendering.
    """
    
    def __init__(self, config: Optional[TableStyleConfig] = None):
        """
        Initialize renderer with a style configuration.
        
        Args:
            config: TableStyleConfig instance. If None, uses default config.
        """
        self.config = config or TableStyleConfig.create_default()
    
    def apply_styles_to_raw_table(self, raw_table_html: str) -> str:
        """
        Apply configured styles to raw HTML table.
        
        Args:
            raw_table_html: Raw HTML table string without styling
            
        Returns:
            Fully styled HTML table string with annotations
        """
        # First pass: analyze structure
        structure_parser = TableStructureParser()
        structure_parser.feed(raw_table_html)
        structure = structure_parser.get_structure()
        
        # Second pass: apply styles
        styler = TableStyler(self.config, structure)
        styler.feed(raw_table_html)
        
        return styler.get_styled_html()
    
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
        # Create output directory
        os.makedirs(os.path.dirname(output_image_path) or '.', exist_ok=True)
        
        # Apply styles to table
        styled_table = self.apply_styles_to_raw_table(raw_table_html)
        
        # Position table on page
        margin = 100
        table_bounds = {
            'x': margin,
            'y': margin,
            'width': page_width - 2 * margin,
            'height': page_height - 2 * margin
        }
        
        # Wrap with positioning div
        positioned_table = self._wrap_with_position(styled_table, table_bounds)
        
        # Create complete HTML document
        final_html = self._create_html_document(positioned_table, page_width, page_height)
        
        # Save debug HTML
        if save_debug_html:
            html_path = output_image_path.replace('.png', '_debug.html')
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(final_html)
            print(f"Debug HTML saved: {html_path}")
        
        # Render and extract annotations
        await render_html_to_image_and_annotate(
            final_html,
            output_image_path,
            output_annotation_path,
            page_width,
            page_height,
            draw_bboxes
        )
        
        # Return annotations
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


# ============================================================================
# CONVENIENCE FUNCTION
# ============================================================================

async def render_raw_table_with_config(
    raw_table_html: str,
    output_image_path: str,
    output_annotation_path: str,
    config: Optional[TableStyleConfig] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Convenience function to render table with custom configuration.
    
    Args:
        raw_table_html: Raw HTML table without styling
        output_image_path: Output PNG path
        output_annotation_path: Output JSON path
        config: TableStyleConfig instance (optional)
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


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

async def main():
    """Demonstrate various styling configurations."""
    
    # Sample raw table
    raw_table = """
    <table>
<thead>
<tr>
<th rowspan="2">NỘI DUNG (DESCRIPTION)</th>
<th rowspan="2">Mã (Code)</th>
<th rowspan="2">Ghi chú (Note)</th>
<th colspan="2">Tháng 6 (June)</th>
<th colspan="2">Lũy kế 6 tháng (6 Months YTD)</th>
</tr>
<tr>
<th>2026</th>
<th>2025</th>
<th>2026</th>
<th>2025</th>
</tr>
</thead>
<tbody>
<tr>
<td class="annotated-cell-text">1. Doanh thu phí bảo hiểm gốc (Gross written premiums)</td>
<td class="annotated-cell-text">01</td>
<td class="annotated-cell-text">V.01</td>
<td class="annotated-cell-text">985.230.150.000</td>
<td class="annotated-cell-text">850.120.400.000</td>
<td class="annotated-cell-text">2.100.560.800.000</td>
<td class="annotated-cell-text">1.950.300.200.000</td>
</tr>
<tr>
<td class="annotated-cell-text">2. Phí nhượng tái bảo hiểm (Reinsurance ceded)</td>
<td class="annotated-cell-text">02</td>
<td class="annotated-cell-text">V.02</td>
<td class="annotated-cell-text">120.500.000.000</td>
<td class="annotated-cell-text">95.000.000.000</td>
<td class="annotated-cell-text">250.000.000.000</td>
<td class="annotated-cell-text">210.000.000.000</td>
</tr>
<tr>
<td class="annotated-cell-text">3. Doanh thu thuần hoạt động kinh doanh bảo hiểm (Net insurance revenue)</td>
<td class="annotated-cell-text">10</td>
<td class="annotated-cell-text"></td>
<td class="annotated-cell-text">864.730.150.000</td>
<td class="annotated-cell-text">755.120.400.000</td>
<td class="annotated-cell-text">1.850.560.800.000</td>
<td class="annotated-cell-text">1.740.300.200.000</td>
</tr>
<tr>
<td colspan="3">(10=01-02)</td>
<td class="annotated-cell-text">-</td>
<td class="annotated-cell-text">-</td>
<td class="annotated-cell-text"></td>
<td class="annotated-cell-text"></td>
</tr>
<tr>
<td class="annotated-cell-text">4. Tổng chi phí bồi thường và chi phí khác (Total claim expenses and others)</td>
<td class="annotated-cell-text">11</td>
<td class="annotated-cell-text">V.03</td>
<td class="annotated-cell-text">750.100.500.000</td>
<td class="annotated-cell-text">680.200.300.000</td>
<td class="annotated-cell-text">1.500.300.100.000</td>
<td class="annotated-cell-text">1.400.500.800.000</td>
</tr>
<tr>
<td class="annotated-cell-text">5. Lợi nhuận gộp hoạt động kinh doanh bảo hiểm (Gross profit from insurance activities)</td>
<td class="annotated-cell-text">20</td>
<td class="annotated-cell-text"></td>
<td class="annotated-cell-text">114.629.650.000</td>
<td class="annotated-cell-text">74.920.100.000</td>
<td class="annotated-cell-text">350.260.700.000</td>
<td class="annotated-cell-text">339.799.400.000</td>
</tr>
<tr>
<td class="annotated-cell-text">(20=10-11)</td>
<td class="annotated-cell-text"></td>
<td class="annotated-cell-text"></td>
<td class="annotated-cell-text">-</td>
<td class="annotated-cell-text">-</td>
<td class="annotated-cell-text"></td>
<td class="annotated-cell-text"></td>
</tr>
<tr>
<td class="annotated-cell-text">6. Doanh thu hoạt động tài chính (Financial income)</td>
<td class="annotated-cell-text">21</td>
<td class="annotated-cell-text">VI.1</td>
<td class="annotated-cell-text">15.600.000.000</td>
<td class="annotated-cell-text">12.300.000.000</td>
<td class="annotated-cell-text">30.500.000.000</td>
<td class="annotated-cell-text">28.100.000.000</td>
</tr>
<tr>
<td class="annotated-cell-text">7. Chi phí tài chính (Financial expenses)</td>
<td class="annotated-cell-text">22</td>
<td class="annotated-cell-text">VI.2</td>
<td class="annotated-cell-text">5.200.000.000</td>
<td class="annotated-cell-text">4.800.000.000</td>
<td class="annotated-cell-text">10.100.000.000</td>
<td class="annotated-cell-text">9.500.000.000</td>
</tr>
<tr>
<td class="annotated-cell-text">- Trong đó: Lãi vay (In which: Interest expense)</td>
<td class="annotated-cell-text">23</td>
<td class="annotated-cell-text"></td>
<td class="annotated-cell-text">2.100.000.000</td>
<td class="annotated-cell-text">2.000.000.000</td>
<td class="annotated-cell-text">4.500.000.000</td>
<td class="annotated-cell-text">4.100.000.000</td>
</tr>
<tr>
<td class="annotated-cell-text">8. Chi phí bán hàng (Selling expenses)</td>
<td class="annotated-cell-text">24</td>
<td class="annotated-cell-text">VI.3</td>
<td class="annotated-cell-text">25.300.000.000</td>
<td class="annotated-cell-text">22.100.000.000</td>
<td class="annotated-cell-text">55.600.000.000</td>
<td class="annotated-cell-text">50.200.000.000</td>
</tr>
<tr>
<td class="annotated-cell-text">9. Chi phí quản lý doanh nghiệp (General and administration expenses)</td>
<td class="annotated-cell-text">25</td>
<td class="annotated-cell-text">VI.4</td>
<td class="annotated-cell-text">18.500.000.000</td>
<td class="annotated-cell-text">16.200.000.000</td>
<td class="annotated-cell-text">40.100.000.000</td>
<td class="annotated-cell-text">38.500.000.000</td>
</tr>
<tr>
<td class="annotated-cell-text">10. Lợi nhuận thuần từ hoạt động kinh doanh (Net operating profit)</td>
<td class="annotated-cell-text">30</td>
<td class="annotated-cell-text"></td>
<td class="annotated-cell-text">81.229.650.000</td>
<td class="annotated-cell-text">44.120.100.000</td>
<td class="annotated-cell-text">274.960.700.000</td>
<td class="annotated-cell-text">269.699.400.000</td>
</tr>
<tr>
<td class="annotated-cell-text">{30=20+(21-22)-(24+25)}</td>
<td class="annotated-cell-text"></td>
<td class="annotated-cell-text"></td>
<td class="annotated-cell-text">-</td>
<td class="annotated-cell-text">-</td>
<td class="annotated-cell-text">-</td>
<td class="annotated-cell-text">-</td>
</tr>
<tr>
<td class="annotated-cell-text">11. Thu nhập khác (Other income)</td>
<td class="annotated-cell-text">31</td>
<td class="annotated-cell-text">VI.5</td>
<td class="annotated-cell-text">1.500.000.000</td>
<td class="annotated-cell-text">2.100.000.000</td>
<td class="annotated-cell-text">5.600.000.000</td>
<td class="annotated-cell-text">4.200.000.000</td>
</tr>
<tr>
<td class="annotated-cell-text">12. Chi phí bất thường (Extraordinary expenses)</td>
<td class="annotated-cell-text">32</td>
<td class="annotated-cell-text">IX.2</td>
<td class="annotated-cell-text">1.245.500.000</td>
<td class="annotated-cell-text">850.120.000</td>
<td class="annotated-cell-text">3.890.650.000</td>
<td class="annotated-cell-text">2.100.450.000</td>
</tr>
<tr>
<td class="annotated-cell-text">13. Lợi nhuận khác (40=31-32) Other profit (40=31-32)</td>
<td class="annotated-cell-text">40</td>
<td class="annotated-cell-text">IX.3</td>
<td class="annotated-cell-text">45.200.150.000</td>
<td class="annotated-cell-text">38.500.900.000</td>
<td class="annotated-cell-text">92.150.800.000</td>
<td class="annotated-cell-text">75.600.250.000</td>
</tr>
</tbody>
    </table>
    """
    
    output_dir = "generated_documents"
    os.makedirs(output_dir, exist_ok=True)
    
    # Example 1: Default style
    print("1. Rendering with default style...")
    config1 = TableStyleConfig.create_default()
    await render_raw_table_with_config(
        raw_table,
        f"{output_dir}/table_default.png",
        f"{output_dir}/table_default.json",
        config1
    )
    
    # Example 2: Borderless style
    print("2. Rendering borderless table...")
    config2 = TableStyleConfig.create_borderless()
    config2.background.pattern = 'even-odd'
    await render_raw_table_with_config(
        raw_table,
        f"{output_dir}/table_borderless.png",
        f"{output_dir}/table_borderless.json",
        config2
    )
    
    # Example 3: Custom style with random elements
    print("3. Rendering with custom random style...")
    config3 = TableStyleConfig()
    config3.border.style = 'partly-borderless'
    config3.border.remove_row_borders = True
    config3.border.keep_header_row_border = True
    config3.background.pattern = 'striped'
    config3.font.weight = 'random'
    config3.font.transform = 'random'
    config3.alignment.horizontal = 'random'
    config3.spacing.random_line_breaks = True
    config3.spacing.line_break_probability = 0.2
    await render_raw_table_with_config(
        raw_table,
        f"{output_dir}/table_custom.png",
        f"{output_dir}/table_custom.json",
        config3
    )
    
    # Example 4: Minimal style
    print("4. Rendering minimal style...")
    config4 = TableStyleConfig.create_minimal()
    config4.font.size = '32px'
    config4.spacing.padding = '12px'
    await render_raw_table_with_config(
        raw_table,
        f"{output_dir}/table_minimal.png",
        f"{output_dir}/table_minimal.json",
        config4
    )
    
    print("\n✓ All examples rendered successfully!")
    print(f"Check '{output_dir}' folder for outputs.")


if __name__ == "__main__":
    asyncio.run(main())