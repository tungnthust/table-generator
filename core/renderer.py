"""
Table Renderer Module
=====================
Refactored rendering logic from html_render.py into a clean class.
Preserves all core rendering logic.
"""

import os
import json
import random
import re
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


def analyze_table_for_orientation(html_content: str) -> Dict[str, Any]:
    """
    Analyze HTML table content to determine optimal orientation and layout parameters.
    Uses a scoring system based on multiple factors for robust decision making.
    
    Returns:
        Dict with:
        - orientation: 'portrait' or 'landscape'
        - orientation_score: confidence score (higher = more confident)
        - num_columns: number of columns
        - num_rows: number of rows
        - avg_cell_content_length: average content length per cell
        - max_cell_content_length: max content length in any cell
        - total_content_width: estimated total content width
        - has_long_text_column: whether there's a column with long text
        - recommended_target_width_multiplier: multiplier for target column width
    """
    # Extract text content from cells, organized by rows
    rows_content = []
    
    # Find all rows
    row_pattern = re.compile(r'<tr[^>]*>(.*?)</tr>', re.DOTALL | re.IGNORECASE)
    cell_pattern = re.compile(r'<(?:td|th)[^>]*>(.*?)</(?:td|th)>', re.DOTALL | re.IGNORECASE)
    
    for row_match in row_pattern.finditer(html_content):
        row_html = row_match.group(1)
        cells = []
        for cell_match in cell_pattern.finditer(row_html):
            # Strip HTML tags to get text content
            text = re.sub(r'<[^>]+>', ' ', cell_match.group(1))
            text = re.sub(r'\s+', ' ', text).strip()
            cells.append(text)
        if cells:
            rows_content.append(cells)
    
    row_count = len(rows_content)
    col_count = max(len(row) for row in rows_content) if rows_content else 1
    
    # Flatten all cell contents for analysis
    all_cells = [cell for row in rows_content for cell in row]
    content_lengths = [len(c) for c in all_cells if c]
    
    avg_length = sum(content_lengths) / len(content_lengths) if content_lengths else 0
    max_length = max(content_lengths) if content_lengths else 0
    
    # Analyze per-column content lengths
    col_avg_lengths = []
    for col_idx in range(col_count):
        col_lengths = []
        for row in rows_content:
            if col_idx < len(row) and row[col_idx]:
                col_lengths.append(len(row[col_idx]))
        if col_lengths:
            col_avg_lengths.append(sum(col_lengths) / len(col_lengths))
        else:
            col_avg_lengths.append(0)
    
    # Check for long text columns
    max_col_avg = max(col_avg_lengths) if col_avg_lengths else 0
    has_long_text_column = max_col_avg > 50 or max_length > 100
    
    # Estimate total content width (sum of column widths)
    # Each column width ~ max(avg_length in that column, 5) chars
    total_content_width = sum(max(avg, 8) for avg in col_avg_lengths)
    
    # === SCORING SYSTEM FOR ORIENTATION ===
    # Positive = favor landscape, Negative = favor portrait
    landscape_score = 0
    
    # Factor 1: Number of columns (more columns = landscape)
    if col_count >= 7:
        landscape_score += 40
    elif col_count >= 5:
        landscape_score += 25
    elif col_count >= 4:
        landscape_score += 10
    elif col_count <= 2:
        landscape_score -= 20
    
    # Factor 2: Content width vs height ratio
    # Estimate width: total content chars * ~8px per char
    # Estimate height: rows * ~30px per row
    est_width = total_content_width * 8
    est_height = row_count * 30
    aspect_ratio = est_width / max(est_height, 1)
    
    if aspect_ratio > 3:
        landscape_score += 30
    elif aspect_ratio > 2:
        landscape_score += 20
    elif aspect_ratio > 1.5:
        landscape_score += 10
    elif aspect_ratio < 0.5:
        landscape_score -= 25
    elif aspect_ratio < 0.8:
        landscape_score -= 10
    
    # Factor 3: Long text column presence (even 2-col table can be landscape if content is long)
    if has_long_text_column:
        landscape_score += 20
    if max_col_avg > 80:
        landscape_score += 15
    
    # Factor 4: Average cell content length
    if avg_length > 40:
        landscape_score += 15
    elif avg_length > 25:
        landscape_score += 8
    elif avg_length < 10:
        landscape_score -= 10
    
    # Factor 5: Row to column ratio
    if row_count > col_count * 4:
        landscape_score -= 15  # Very tall table, portrait might be better
    elif col_count > row_count * 2:
        landscape_score += 15  # Very wide table
    
    # Determine orientation with some randomness for diversity
    # Score > 20: strongly favor landscape
    # Score < -20: strongly favor portrait
    # In between: probabilistic
    if landscape_score > 30:
        orientation = 'landscape'
        orientation_probability = 0.9
    elif landscape_score > 10:
        orientation = 'landscape' if random.random() < 0.75 else 'portrait'
        orientation_probability = 0.75
    elif landscape_score > -10:
        # Balanced - could go either way
        orientation = 'landscape' if random.random() < 0.5 else 'portrait'
        orientation_probability = 0.5
    elif landscape_score > -30:
        orientation = 'portrait' if random.random() < 0.75 else 'landscape'
        orientation_probability = 0.75
    else:
        orientation = 'portrait'
        orientation_probability = 0.9
    
    # Calculate recommended width multiplier based on content
    if orientation == 'landscape':
        if has_long_text_column:
            width_multiplier = 1.4
        elif avg_length > 30:
            width_multiplier = 1.2
        else:
            width_multiplier = 1.1
    else:
        if has_long_text_column:
            width_multiplier = 1.0
        elif avg_length < 15:
            width_multiplier = 0.8
        else:
            width_multiplier = 0.9
    
    return {
        'orientation': orientation,
        'orientation_score': landscape_score,
        'orientation_probability': orientation_probability,
        'num_columns': col_count,
        'num_rows': row_count,
        'avg_cell_content_length': avg_length,
        'max_cell_content_length': max_length,
        'col_avg_lengths': col_avg_lengths,
        'total_content_width': total_content_width,
        'has_long_text_column': has_long_text_column,
        'recommended_target_width_multiplier': width_multiplier,
        'rows_content': rows_content,  # Cell content by rows for content-aware alignment
    }


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
    def __init__(self, config: StyleConfig, structure: Dict, table_analysis: Dict = None):
        super().__init__()
        self.config = config
        self.structure = structure
        self.table_analysis = table_analysis or {}
        self.result = []
        self.in_cell = False
        self.cell_content = []
        self.current_section = None
        self.current_row_index = 0
        self.current_cell_index = 0
        self.row_index_global = 0
        
        # Cache column_colors for column-based pattern (avoids repeated getattr calls)
        self._column_colors = getattr(self.config.background, 'column_colors', {})
        
        # Random seed for this variation's line break decisions
        # This ensures different variations have different line break patterns
        self._line_break_seed = random.randint(0, 1000000)
        
        # Pre-compute consistent column alignments for data cells
        # This ensures alignment is consistent within each column (realistic table behavior)
        self._column_alignments = self._compute_column_alignments()
        
        # Pre-compute consistent vertical alignment for all data rows
        # Headers can be different, but all data rows should have same vertical alignment
        self._data_vertical_alignment = self._compute_data_vertical_alignment()
        self._header_vertical_alignment = self._compute_header_vertical_alignment()
        
        # Pre-compute consistent font style for data cells
        # All data cells should have same style (normal), except headers (bold) and colspan rows (can be bold)
        self._data_font_weight = self._compute_data_font_weight()
        self._data_font_style = self._compute_data_font_style()
        
        # Identify rows with colspan (these can have bold style like section headers)
        self._colspan_rows = self._identify_colspan_rows()
    
    def _compute_column_alignments(self) -> Dict[int, str]:
        """
        Pre-compute alignment for each column based on content analysis.
        This ensures data cells within a column have consistent alignment (realistic behavior).
        
        Strategy:
        - Analyze all data cells in each column
        - If column has mostly multi-word text (>2 words): favor 'left' (80%)
        - If column has mostly numeric data: favor 'right' (60%) or 'center' (30%)
        - If column has short text/mixed: use configured alignment or 'center'
        """
        column_alignments = {}
        rows_content = self.table_analysis.get('rows_content', [])
        num_columns = self.table_analysis.get('num_columns', 0)
        
        if not rows_content or num_columns == 0:
            return column_alignments
        
        # Skip header rows (usually first 1-2 rows) for data alignment analysis
        # Headers have their own alignment
        data_rows = rows_content[1:] if len(rows_content) > 1 else rows_content
        
        for col_idx in range(num_columns):
            # Collect all cell contents for this column
            col_cells = []
            for row in data_rows:
                if col_idx < len(row) and row[col_idx]:
                    col_cells.append(row[col_idx])
            
            if not col_cells:
                continue
            
            # Analyze column content
            text_cells = 0  # Cells with 3+ words (descriptive text)
            numeric_cells = 0  # Cells with only numbers/symbols
            short_cells = 0  # Cells with 1-2 words
            
            for cell in col_cells:
                words = cell.split()
                word_count = len(words)
                is_numeric = bool(re.match(r'^[\d\s.,%-]+$', cell.strip()))
                
                if is_numeric:
                    numeric_cells += 1
                elif word_count >= 3:
                    text_cells += 1
                else:
                    short_cells += 1
            
            total = len(col_cells)
            
            # Decide alignment based on dominant content type
            if text_cells / total > 0.4:
                # Column has significant text content - strongly favor left
                alignment = 'left' if random.random() < 0.85 else 'center'
            elif numeric_cells / total > 0.5:
                # Column is mostly numeric - favor right or center
                r = random.random()
                if r < 0.55:
                    alignment = 'right'
                elif r < 0.85:
                    alignment = 'center'
                else:
                    alignment = 'left'
            elif short_cells / total > 0.6:
                # Column has short items - center or left
                alignment = 'center' if random.random() < 0.6 else 'left'
            else:
                # Mixed content - use config default or center
                if self.config.alignment.data_horizontal:
                    alignment = self.config.alignment.data_horizontal
                else:
                    alignment = 'center' if random.random() < 0.5 else 'left'
            
            column_alignments[col_idx] = alignment
        
        return column_alignments
    
    def _compute_data_vertical_alignment(self) -> str:
        """
        Compute a consistent vertical alignment for all data rows.
        Real tables have consistent vertical alignment within data section.
        
        Weights (favor middle/top for realistic look):
        - middle: 60% (most common in real tables)
        - top: 30% (common for multi-line cells)
        - bottom: 10% (rare)
        """
        if self.config.alignment.data_vertical:
            return self.config.alignment.data_vertical
        
        r = random.random()
        if r < 0.60:
            return 'middle'
        elif r < 0.90:
            return 'top'
        else:
            return 'bottom'
    
    def _compute_header_vertical_alignment(self) -> str:
        """
        Compute vertical alignment for header rows.
        Can be different from data rows.
        
        Weights (favor middle for headers):
        - middle: 70% (most common for headers)
        - bottom: 20% (sometimes used when headers are taller)
        - top: 10% (rare for headers)
        """
        if self.config.alignment.header_vertical:
            return self.config.alignment.header_vertical
        
        r = random.random()
        if r < 0.70:
            return 'middle'
        elif r < 0.90:
            return 'bottom'
        else:
            return 'top'
    
    def _compute_data_font_weight(self) -> str:
        """
        Compute consistent font weight for all data cells.
        Data cells should almost always be 'normal' weight.
        Headers are handled separately (usually bold).
        
        Weights:
        - normal: 95% (standard for data)
        - bold: 5% (rare - only for emphasis tables)
        """
        if self.config.font.weight and self.config.font.weight != 'random':
            return self.config.font.weight
        
        return 'normal' if random.random() < 0.95 else 'bold'
    
    def _compute_data_font_style(self) -> str:
        """
        Compute consistent font style for all data cells.
        Data cells should almost always be 'normal' style.
        All italic or mixed styles are weird and should be very rare.
        
        Weights:
        - normal: 98% (standard)
        - italic: 2% (very rare)
        """
        if self.config.font.style and self.config.font.style != 'random':
            return self.config.font.style
        
        return 'normal' if random.random() < 0.98 else 'italic'
    
    def _identify_colspan_rows(self) -> set:
        """
        Identify row indices that have colspan cells.
        These rows can have bold styling (like section headers within table).
        """
        colspan_rows = set()
        for row_idx, row_data in enumerate(self.structure.get('rows', [])):
            cells = row_data.get('cells', [])
            for cell in cells:
                if cell.get('colspan', 1) > 1:
                    colspan_rows.add(row_idx)
                    break
        return colspan_rows
        
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
    
    def _get_font_style(self, is_header: bool = False, is_footer: bool = False, 
                        row_idx: int = 0, has_colspan: bool = False) -> Dict[str, str]:
        """
        Get font styling properties.
        
        CONSISTENCY RULES:
        - All data cells use same font-weight and font-style (pre-computed)
        - Headers use bold weight
        - Colspan rows (like section headers) can optionally be bold
        - No mixing of bold/italic within same row
        """
        styles = {
            'font-family': self.config.font.family,
            'font-size': self.config.font.size,
            'color': self.config.font.color
        }
        
        # === FONT WEIGHT ===
        if is_header:
            # Headers are bold (standard)
            styles['font-weight'] = self.config.font.header_weight or 'bold'
        elif is_footer:
            styles['font-weight'] = self.config.font.footer_weight or 'normal'
        elif row_idx in self._colspan_rows:
            # Colspan rows can be bold (like section headers within table)
            # 40% chance to be bold, 60% use same as data
            if random.random() < 0.4:
                styles['font-weight'] = 'bold'
            else:
                styles['font-weight'] = self._data_font_weight
        else:
            # Regular data cells - use pre-computed consistent weight
            styles['font-weight'] = self._data_font_weight
        
        # === FONT STYLE ===
        if is_header:
            styles['font-style'] = self.config.font.header_style or 'normal'
        elif is_footer:
            styles['font-style'] = self.config.font.footer_style or 'normal'
        else:
            # All data cells use same font-style (pre-computed)
            styles['font-style'] = self._data_font_style
        
        # === TEXT TRANSFORM ===
        # Keep simple - no random per-cell transforms
        if self.config.font.transform and self.config.font.transform != 'none':
            styles['text-transform'] = self.config.font.transform
        
        return styles
    
    def _get_alignment_style(self, col_idx: int = 0, is_header: bool = False, cell_content: str = "") -> Dict[str, str]:
        """Get alignment styling properties.
        
        Uses pre-computed column alignments for consistency within columns.
        Headers get separate alignment (favor center).
        Small probability of per-cell variation for realism.
        
        Args:
            col_idx: Column index for column-specific alignment
            is_header: Whether this is a header cell (uses header_horizontal/vertical)
            cell_content: The text content of the cell (not used directly anymore, column analysis done at init)
        """
        styles = {}
        
        # === HORIZONTAL ALIGNMENT ===
        
        # Priority 1: Explicit column alignments from config
        if col_idx in self.config.alignment.column_alignments:
            styles['text-align'] = self.config.alignment.column_alignments[col_idx]
        
        # Priority 2: Header alignment (headers can differ from data)
        elif is_header:
            if self.config.alignment.header_horizontal:
                styles['text-align'] = self.config.alignment.header_horizontal
            else:
                # Default: headers favor center (80%), sometimes left (20%)
                styles['text-align'] = 'center' if random.random() < 0.8 else 'left'
        
        # Priority 3: Use pre-computed column alignment for data cells (consistent within column)
        elif col_idx in self._column_alignments:
            base_alignment = self._column_alignments[col_idx]
            
            # Small chance (5%) of per-cell variation for natural imperfection
            if random.random() < 0.05:
                # Slight variation - don't stray too far from base
                if base_alignment == 'left':
                    styles['text-align'] = 'center'
                elif base_alignment == 'right':
                    styles['text-align'] = 'center'
                else:  # center
                    styles['text-align'] = 'left' if random.random() < 0.5 else 'right'
            else:
                styles['text-align'] = base_alignment
        
        # Priority 4: Fallback to config data_horizontal or horizontal
        elif self.config.alignment.data_horizontal:
            styles['text-align'] = self.config.alignment.data_horizontal
        elif self.config.alignment.horizontal == 'random':
            # For random, pick once and use consistently (already handled by column alignments above)
            styles['text-align'] = random.choice(['left', 'center', 'right'])
        else:
            styles['text-align'] = self.config.alignment.horizontal
        
        # === VERTICAL ALIGNMENT ===
        # Use pre-computed consistent vertical alignment
        # Headers and data rows can differ, but each section is consistent
        
        if is_header:
            # Use pre-computed header vertical alignment (consistent for all headers)
            styles['vertical-align'] = self._header_vertical_alignment
        else:
            # Use pre-computed data vertical alignment (consistent for all data rows)
            # Small chance (3%) of per-cell variation for natural imperfection
            if random.random() < 0.03:
                # Slight variation
                alts = ['top', 'middle', 'bottom']
                alts.remove(self._data_vertical_alignment) if self._data_vertical_alignment in alts else None
                styles['vertical-align'] = random.choice(alts) if alts else 'middle'
            else:
                styles['vertical-align'] = self._data_vertical_alignment
        
        return styles
    
    def _estimate_text_width(self, text: str, font_size: str) -> int:
        """
        Estimate text width in pixels based on font size.
        Uses approximate character width ratio (varies by font, but ~0.5-0.6 of font size for average).
        """
        try:
            size_px = int(font_size.replace('px', ''))
        except (ValueError, AttributeError):
            size_px = 24
        
        # Average character width is roughly 0.5-0.6 of font size for proportional fonts
        # Use 0.55 as a balanced estimate
        avg_char_width = size_px * 0.55
        return int(len(text) * avg_char_width)
    
    def _get_target_column_width(self, font_size: str, text: str = "") -> int:
        """
        Get a reasonable target column width based on font size and table orientation.
        Uses table analysis to adjust width for portrait vs landscape.
        
        Returns target width in pixels.
        """
        try:
            size_px = int(font_size.replace('px', ''))
        except (ValueError, AttributeError):
            size_px = 24
        
        # Base target characters based on font size
        if size_px <= 18:
            base_target_chars = 22
        elif size_px <= 26:
            base_target_chars = 20
        elif size_px <= 34:
            base_target_chars = 17
        else:
            base_target_chars = 14
        
        # Adjust based on orientation from table analysis
        orientation = self.table_analysis.get('orientation', 'landscape')
        width_multiplier = self.table_analysis.get('recommended_target_width_multiplier', 1.0)
        
        # Apply orientation adjustment
        if orientation == 'landscape':
            # Landscape: allow wider columns
            target_chars = int(base_target_chars * width_multiplier * 1.2)
        else:
            # Portrait: prefer narrower columns, more line breaks
            target_chars = int(base_target_chars * width_multiplier * 0.9)
        
        # Add some randomness per variation (±15%)
        random.seed(self._line_break_seed + hash(text[:20]) if text else self._line_break_seed)
        variation_factor = random.uniform(0.85, 1.15)
        target_chars = int(target_chars * variation_factor)
        
        # Reset random state
        random.seed()
        
        return int(target_chars * size_px * 0.55)
    
    def _apply_random_line_breaks(self, text: str) -> str:
        """
        Intelligently insert <br> tags based on estimated column width and table orientation.
        
        Logic:
        1. Estimate text width based on font size
        2. Consider table orientation (landscape = wider columns, portrait = narrower)
        3. If text exceeds target column width, break to fit
        4. Only break at word boundaries (spaces)
        5. Never break single words/numbers
        6. Ensure each line has reasonable number of words (min 3 words per line)
        7. Don't break if it would create weird short lines
        """
        if not self.config.spacing.random_line_breaks:
            return text
        
        # Don't break if no spaces (single word/number)
        if ' ' not in text:
            return text
        
        words = text.split()
        total_words = len(words)
        
        if total_words <= 1:
            return text
        
        # Get font size and calculate target width (with orientation awareness)
        font_size = self.config.font.size
        target_width = self._get_target_column_width(font_size, text)
        
        # Estimate total text width
        total_width = self._estimate_text_width(text, font_size)
        
        # If text fits in target width, no need to break
        if total_width <= target_width:
            return text
        
        # Calculate how many lines we'd need
        num_lines_needed = max(1, (total_width + target_width - 1) // target_width)
        
        # === KEY CHECK: Ensure reasonable words per line ===
        # Each line should have at least 3 words for readability
        min_words_per_line = 3
        max_reasonable_lines = total_words // min_words_per_line
        
        if max_reasonable_lines < 2:
            # Not enough words to make sensible multi-line, don't break
            return text
        
        # Cap lines to reasonable amount
        num_lines = min(num_lines_needed, max_reasonable_lines, 4)
        
        # If only 1 line after constraints, return as-is
        if num_lines <= 1:
            return text
        
        # Use consistent randomness for this text in this variation
        random.seed(self._line_break_seed + hash(text))
        
        # Sometimes use fewer lines for variation (30% chance)
        if num_lines > 2 and random.random() < 0.3:
            num_lines = max(2, num_lines - 1)
        
        # Calculate target words per line (distribute evenly)
        words_per_line = total_words // num_lines
        
        # Ensure minimum words per line
        if words_per_line < min_words_per_line:
            # Reduce number of lines
            num_lines = total_words // min_words_per_line
            if num_lines < 2:
                random.seed()
                return text
            words_per_line = total_words // num_lines
        
        # Build lines with balanced word distribution
        result = []
        current_line = []
        
        for i, word in enumerate(words):
            current_line.append(word)
            
            # Decide if we should break here
            words_in_current_line = len(current_line)
            words_remaining = total_words - i - 1
            lines_remaining = num_lines - len(result) - 1
            
            should_break = False
            
            if lines_remaining > 0:
                # Check if we have enough words for this line
                if words_in_current_line >= words_per_line:
                    # Make sure remaining words can fill remaining lines
                    min_remaining_needed = lines_remaining * min_words_per_line
                    if words_remaining >= min_remaining_needed:
                        should_break = True
                
                # Also break if current line is getting too wide
                current_line_text = ' '.join(current_line)
                current_width = self._estimate_text_width(current_line_text, font_size)
                if current_width > target_width * 0.9 and words_remaining >= min_words_per_line:
                    should_break = True
            
            if should_break:
                result.append(' '.join(current_line))
                current_line = []
        
        # Add remaining words
        if current_line:
            # Check if last line is too short (less than 2 words) and we have previous lines
            if len(current_line) < 2 and result:
                # Merge with previous line
                last_line_words = result[-1].split()
                result[-1] = ' '.join(last_line_words + current_line)
            else:
                result.append(' '.join(current_line))
        
        # Reset random state
        random.seed()
        
        # Final validation: don't return weird results
        if len(result) <= 1:
            return text
        
        # Check that no line is too short (except last line can be shorter)
        for i, line in enumerate(result[:-1]):
            if len(line.split()) < 2:
                # Something went wrong, return original
                return text
        
        return '<br/>'.join(result)
    
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
            
            # Font style with row context for colspan handling
            font_styles = self._get_font_style(
                is_header, is_footer, 
                self.row_index_global, 
                has_colspan
            )
            cell_styles.update(font_styles)
            
            # Get cell content from pre-analyzed table data for content-aware alignment
            cell_text = ""
            rows_content = self.table_analysis.get('rows_content', [])
            if self.row_index_global < len(rows_content):
                row_data = rows_content[self.row_index_global]
                if self.current_cell_index < len(row_data):
                    cell_text = row_data[self.current_cell_index]
            
            alignment_styles = self._get_alignment_style(self.current_cell_index, is_header, cell_text)
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
    
    def __init__(self, style_config: Optional[StyleConfig] = None, table_analysis: Dict = None):
        """
        Initialize renderer with a style configuration.
        
        Args:
            style_config: StyleConfig instance. If None, uses default config.
            table_analysis: Optional pre-computed table analysis for orientation/layout decisions.
        """
        self.config = style_config or StyleConfig.create_default()
        self.table_analysis = table_analysis or {}
    
    def apply_styles_to_raw_table(self, raw_table_html: str, table_analysis: Dict = None) -> str:
        """
        Apply configured styles to raw HTML table.
        
        Args:
            raw_table_html: Raw HTML table string without styling
            table_analysis: Optional table analysis for orientation-aware styling
            
        Returns:
            Fully styled HTML table string with annotations
        """
        # Use provided analysis or compute it
        analysis = table_analysis or self.table_analysis or analyze_table_for_orientation(raw_table_html)
        
        structure_parser = TableStructureParser()
        structure_parser.feed(raw_table_html)
        structure = structure_parser.get_structure()
        
        # Pass table analysis to styler for orientation-aware line breaks
        styler = TableStyler(self.config, structure, analysis)
        styler.feed(raw_table_html)
        
        return styler.get_styled_html()
    
    async def render_single(
        self,
        html_path: Path,
        output_dir: Path,
        draw_bboxes: bool = True,
        save_debug_html: bool = False,
        page_width: int = 2480,
        page_height: int = 3508,
        dynamic_size: bool = True
    ) -> Dict[str, Path]:
        """
        Render single HTML to images and annotations.
        
        Args:
            html_path: Path to HTML file
            output_dir: Output directory
            draw_bboxes: Whether to draw bounding boxes on image
            save_debug_html: Whether to save debug HTML file
            page_width: Page width in pixels (used as max if dynamic_size=True)
            page_height: Page height in pixels (used as max if dynamic_size=True)
            dynamic_size: If True, image size will be adjusted to fit table dimensions
            
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
            save_debug_html=False,
            dynamic_size=dynamic_size
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
                save_debug_html=save_debug_html,
                dynamic_size=dynamic_size
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
        save_debug_html: bool = False,
        dynamic_size: bool = True,
        fully_random: bool = True
    ) -> List[Dict]:
        """
        Render multiple HTMLs with optional style variations.
        
        Args:
            html_files: List of paths to HTML files
            output_dir: Output directory
            style_variations: Number of style variations per HTML
            draw_bboxes: Whether to draw bounding boxes
            save_debug_html: Whether to save debug HTML
            dynamic_size: If True, image size will be adjusted to fit table dimensions
            fully_random: If True, each variation creates completely new random style
            
        Returns:
            List of dictionaries with paths to generated files
        """
        output_dir = Path(output_dir)
        results = []
        
        for html_file in html_files:
            html_file = Path(html_file)
            
            # Read HTML content once for analysis
            with open(html_file, 'r', encoding='utf-8') as f:
                raw_table_html = f.read()
            
            # Analyze table structure for orientation decision (once per HTML file)
            table_analysis = analyze_table_for_orientation(raw_table_html)
            
            for style_idx in range(style_variations):
                # Create new random style for each variation (not just small tweaks)
                if style_variations > 1:
                    if fully_random:
                        # Create completely new random style
                        config = StyleConfig.create_random()
                    else:
                        # Create small variation of base style
                        config = self.config.create_variation()
                    # Pass table analysis to renderer
                    renderer = TableRenderer(config, table_analysis)
                else:
                    renderer = self
                    renderer.table_analysis = table_analysis
                
                # Modify base name for style variations
                if style_variations > 1:
                    base_name = f"{html_file.stem}_style_{style_idx}"
                else:
                    base_name = html_file.stem
                
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
                    'annotation': annotation_path,
                    'table_analysis': table_analysis
                }
                
                # Render without bboxes
                await renderer.render_table(
                    raw_table_html,
                    str(image_path_clean),
                    str(annotation_path),
                    draw_bboxes=False,
                    save_debug_html=False,
                    dynamic_size=dynamic_size
                )
                
                # Render with bboxes if requested
                if draw_bboxes:
                    image_path_annotated = output_dir / 'images' / 'with_annotation' / f'{base_name}_annotated.png'
                    
                    await renderer.render_table(
                        raw_table_html,
                        str(image_path_annotated),
                        str(annotation_path),
                        draw_bboxes=True,
                        save_debug_html=save_debug_html,
                        dynamic_size=dynamic_size
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
        save_debug_html: bool = True,
        dynamic_size: bool = True,
        size_margin: int = 100
    ) -> Dict[str, Any]:
        """
        Render a raw HTML table to image with annotations.
        This is the exact logic from html_render.py TableRenderer.render_table.
        
        Args:
            raw_table_html: Raw HTML table string without styling
            output_image_path: Path for output PNG image
            output_annotation_path: Path for output JSON annotations
            page_width: Page width in pixels (default: A4 at 300 DPI, used as max if dynamic_size=True)
            page_height: Page height in pixels (default: A4 at 300 DPI, used as max if dynamic_size=True)
            draw_bboxes: Whether to draw bounding boxes on image
            save_debug_html: Whether to save debug HTML file
            dynamic_size: If True, image size will be adjusted to fit table dimensions
            size_margin: Margin around the table when using dynamic sizing
            
        Returns:
            Dictionary containing annotation data
        """
        os.makedirs(os.path.dirname(output_image_path) or '.', exist_ok=True)
        updated_raw_table_html = raw_table_html.replace('<br>', '**line-break**')
        styled_table = self.apply_styles_to_raw_table(updated_raw_table_html)
        styled_table = styled_table.replace('**line-break**', '<br>')
        margin = size_margin
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
            draw_bboxes,
            dynamic_size=dynamic_size,
            size_margin=margin,
            raw_table_html=raw_table_html
        )
        
        with open(output_annotation_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _wrap_with_position(self, table_html: str, bounds: Dict[str, int]) -> str:
        """Wrap table with positioning container."""
        # Remove fixed width/height and overflow:hidden to allow dynamic sizing
        container_style = (
            f"position: absolute; "
            f"left: {bounds['x']}px; top: {bounds['y']}px; "
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
                body {{ margin: 0; padding: 0; background-color: #FFF; }}
                .page {{
                    min-width: {width}px;
                    min-height: {height}px;
                    background-color: white;
                    position: relative;
                    margin: 0;
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
    dynamic_size: bool = True,
    **kwargs
) -> Dict[str, Any]:
    """
    Convenience function to render table with custom configuration.
    
    Args:
        raw_table_html: Raw HTML table without styling
        output_image_path: Output PNG path
        output_annotation_path: Output JSON path
        config: StyleConfig instance (optional)
        dynamic_size: If True, image size will be adjusted to fit table dimensions
        **kwargs: Additional arguments passed to renderer
        
    Returns:
        Annotation dictionary
    """
    renderer = TableRenderer(config)
    return await renderer.render_table(
        raw_table_html,
        output_image_path,
        output_annotation_path,
        dynamic_size=dynamic_size,
        **kwargs
    )
