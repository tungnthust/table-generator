"""
Table Augmenter Module
======================
Refactored augmentation logic from html_synthesis.py into a clean class.
Preserves all core augmentation logic.
"""

import os
import json
import time
import uuid
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional, Set
from dataclasses import dataclass

from bs4 import BeautifulSoup

# Import configuration
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.augment_config import AugmentConfig

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


class TableAugmenter:
    """
    Main augmenter class that handles HTML table augmentation using LLM.
    Wraps the existing augmentation logic from html_synthesis.py.
    """
    
    def __init__(self, config: Optional[AugmentConfig] = None):
        """
        Initialize augmenter with configuration.
        
        Args:
            config: AugmentConfig instance. If None, uses default config.
        """
        self.config = config or AugmentConfig()
        self._client = None
        
        # Initialize Google GenAI client
        self._init_client()
    
    def _init_client(self):
        """Initialize the Google GenAI client."""
        try:
            from google import genai
            if self.config.api_key:
                self._client = genai.Client(api_key=self.config.api_key)
            else:
                logging.warning("No API key provided. Set GOOGLE_API_KEY environment variable or pass api_key to config.")
        except ImportError:
            logging.warning("google-genai not installed. Run: pip install google-genai")
    
    def augment_html(self, html_content: str) -> str:
        """
        Augment a single HTML and return new HTML.
        
        Args:
            html_content: Raw HTML table content
            
        Returns:
            Augmented HTML content
        """
        if not self._client:
            raise RuntimeError("Google GenAI client not initialized. Check API key.")
        
        # Parse HTML
        payload, registry, soup = self._parse_html_with_id_reference(html_content)
        
        # Process with deviation
        updates = self._process_table_with_deviation(
            payload, 
            deviation_level=self.config.deviation_level
        )
        
        # Reconstruct HTML
        final_html = self._run_augmentation_pipeline(
            original_html=html_content,
            payload=payload,
            registry=registry,
            soup=soup,
            llm_output_list=updates
        )
        
        return final_html
    
    def augment_batch(self, html_files: List[Path], output_dir: Path) -> List[Path]:
        """
        Augment multiple HTML files and save to output directory.
        
        Args:
            html_files: List of paths to HTML files
            output_dir: Directory to save augmented HTML files
            
        Returns:
            List of paths to generated augmented HTML files
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        generated_files = []
        
        for html_file in html_files:
            html_file = Path(html_file)
            logging.info(f"Processing: {html_file.name}")
            
            # Read HTML content
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Generate N augmented versions
            for i in range(self.config.num_augmentations):
                try:
                    augmented_html = self.augment_html(html_content)
                    
                    # Save augmented HTML
                    output_name = f"{html_file.stem}_aug_{i}.html"
                    output_path = output_dir / output_name
                    
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(augmented_html)
                    
                    generated_files.append(output_path)
                    logging.info(f"  Generated: {output_name}")
                    
                except Exception as e:
                    logging.error(f"  Failed to generate augmentation {i}: {e}")
        
        return generated_files
    
    # =========================================================================
    # CORE AUGMENTATION LOGIC (preserved from html_synthesis.py)
    # =========================================================================
    
    def _parse_html_with_id_reference(self, html_content: str) -> Tuple[List[Dict], Dict, Any]:
        """
        Parse HTML table and return payload, registry, and soup.
        This is the exact logic from html_synthesis.py parse_html_with_id_reference.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        table = soup.find('table')
        
        if not table:
            raise ValueError("No <table> found in the HTML content")

        cell_registry = {} 

        rows = table.find_all('tr')
        grid = [] 
        header_row_indices = set()
        
        for r_idx, tr in enumerate(rows):
            while len(grid) <= r_idx: 
                grid.append([])
            
            if (tr.parent.name == 'thead') or (tr.find('th') is not None):
                header_row_indices.add(r_idx)

            col_idx = 0
            cells = tr.find_all(['td', 'th'])
            
            for cell in cells:
                while col_idx < len(grid[r_idx]) and grid[r_idx][col_idx] is not None:
                    col_idx += 1
                
                cell_id = f"cell_{uuid.uuid4().hex[:8]}"
                cell_registry[cell_id] = cell

                rowspan = int(cell.get('rowspan', 1))
                colspan = int(cell.get('colspan', 1))
                text_content = cell.get_text(separator=' ', strip=True)
                
                for r in range(rowspan):
                    for c in range(colspan):
                        target_row = r_idx + r
                        while len(grid) <= target_row: 
                            grid.append([])
                        while len(grid[target_row]) <= col_idx + c: 
                            grid[target_row].append(None)
                        
                        grid[target_row][col_idx + c] = {
                            "id": cell_id,
                            "text": text_content,
                            "type": cell.name,
                            "is_real": (r == 0 and c == 0),
                            "colspan": colspan,
                            "origin_row": r_idx
                        }
                col_idx += colspan

        max_cols = max(len(r) for r in grid) if grid else 0
        col_headers_map = {} 
        
        for c_idx in range(max_cols):
            headers = []
            seen_header_ids = set()
            
            for r_idx in sorted(list(header_row_indices)):
                if c_idx < len(grid[r_idx]) and grid[r_idx][c_idx] is not None:
                    cell_info = grid[r_idx][c_idx]
                    
                    if cell_info['id'] not in seen_header_ids:
                        headers.append({
                            "id": cell_info['id'],
                            "content": cell_info['text'],
                            "row_index": cell_info['origin_row']
                        })
                        seen_header_ids.add(cell_info['id'])
            
            col_headers_map[c_idx] = headers

        llm_payload = []
        
        for r_idx, row_data in enumerate(grid):
            json_row = {
                "row_index": r_idx,
                "is_header_row": r_idx in header_row_indices,
                "cells": []
            }
            
            processed_ids_in_row = set()
            
            for c_idx, cell_info in enumerate(row_data):
                if not cell_info: 
                    continue
                if cell_info['id'] in processed_ids_in_row: 
                    continue
                
                processed_ids_in_row.add(cell_info['id'])
                
                cell_obj = {
                    "id": cell_info['id'],
                    "content": cell_info['text']
                }

                current_colspan = cell_info.get('colspan', 1)
                potential_headers = []
                seen_context_ids = set()
                
                for span_offset in range(current_colspan):
                    target_col = c_idx + span_offset
                    col_headers = col_headers_map.get(target_col, [])
                    
                    for h in col_headers:
                        if h['row_index'] < cell_info['origin_row']:
                            if h['id'] not in seen_context_ids:
                                potential_headers.append({
                                    "id": h['id'],
                                    "content": h['content']
                                })
                                seen_context_ids.add(h['id'])
                
                cell_obj["column_context"] = potential_headers
                cell_obj["role"] = "target" if cell_info['is_real'] else "merged_view"
                
                json_row['cells'].append(cell_obj)
                
            llm_payload.append(json_row)

        return llm_payload, cell_registry, soup
    
    def _augment_batch(self, batch_rows: List[Dict], context_headers: List[Dict], 
                       deviation_level: float = 0.5, is_header_batch: bool = False) -> List[Dict]:
        """
        Sends a batch of rows to the LLM.
        This is the exact logic from html_synthesis.py augment_batch.
        """
        from google.genai import types
        
        dynamic_temperature = 0.3 + (deviation_level * 0.7)

        payload = {
            "context_headers": context_headers, 
            "target_batch": batch_rows
        }

        if deviation_level < 0.3:
            creativity_instruction = "Low Deviation: Keep values very similar. Fix typos, change formatting, or use close synonyms. Keep numbers in the exact same magnitude."
        elif deviation_level < 0.7:
            creativity_instruction = "Medium Deviation: Generate distinct realistic variations. Change specific entity names (e.g., 'Company A' -> 'Company B'). Vary numbers by +/- 20%."
        else:
            creativity_instruction = "High Deviation: Re-imagine the data. You may change the industry or topic slightly if headers allow. Drastically change number magnitudes (e.g., Millions to Billions) if consistent."

        if is_header_batch:
            task_instruction = "Task: Reinvent the Table Structure. Rename headers to similar concepts in the same domain. (e.g., 'Revenue' -> 'Total Sales', '2024' -> '2025')."
        else:
            task_instruction = "Task: Generate Data Content. Ensure new data aligns strictly with the 'context_headers' provided."

        system_instruction = f"""
        You are a Context-Aware Data Augmentation Engine.
        
        ### SETTINGS
        **Deviation Level**: {deviation_level} ({creativity_instruction})
        **Batch Type**: {"HEADERS" if is_header_batch else "DATA ROWS"}
        
        ### INPUT
        You have "target_batch" (cells to edit) and "context_headers" (reference).
        
        ### RULES
        1. **Context Dependency**: 
           - Look at `column_context` for every cell. 
           - If a header changed (in context), the data MUST match the new header.
           
        2. **Handling Empty Cells**:
           - **CRITICAL**: If `original_content` is empty/null, you CAN generate a value if the column context implies data exists. 
              
        3. **{task_instruction}**

        4. **Output Format**: 
           - Return a STRICT JSON List of objects: `[{{"id": "cell_id", "new_content": "value"}}]`
           - Do not wrap in markdown blocks.
        """

        try:
            response = self._client.models.generate_content(
                model=self.config.model_id,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    temperature=dynamic_temperature
                ),
                contents=json.dumps(payload)
            )
            return json.loads(response.text)
        except Exception as e:
            logging.warning(f"Batch failed: {e}")
            return []
    
    def _apply_local_updates(self, rows: List[Dict], updates: List[Dict]) -> int:
        """
        Helper: Updates the in-memory JSON rows with the results from the LLM.
        """
        update_map = {u['id']: u['new_content'] for u in updates}
        count = 0
        for row in rows:
            for cell in row['cells']:
                if cell['id'] in update_map:
                    cell['content'] = update_map[cell['id']]
                    count += 1
        return count
    
    def _update_column_context_refs(self, data_rows: List[Dict], header_rows: List[Dict]) -> None:
        """
        Advanced Helper: After augmenting headers, the 'column_context' list inside 
        data cells is now stale. We must refresh the data rows to reflect the NEW header text.
        """
        header_map = {}
        for r in header_rows:
            for cell in r['cells']:
                header_map[cell['id']] = cell['content']

        for row in data_rows:
            for cell in row['cells']:
                if 'column_context' in cell:
                    for ctx_item in cell['column_context']:
                        if ctx_item['id'] in header_map:
                            ctx_item['content'] = header_map[ctx_item['id']]
    
    def _process_table_with_deviation(self, full_json_table: List[Dict], 
                                       deviation_level: float = 0.5) -> List[Dict]:
        """
        Orchestrates the augmentation with Header-First strategy.
        This is the exact logic from html_synthesis.py process_table_with_deviation.
        """
        logging.info(f"Processing Table (Deviation: {deviation_level})")
        
        header_rows = [r for r in full_json_table if r.get('is_header_row', False)]
        data_rows = [r for r in full_json_table if not r.get('is_header_row', False)]
        
        all_updates = []

        # PHASE 1: AUGMENT HEADERS
        logging.info("  Phase 1: Augmenting Headers...")
        if header_rows:
            header_updates = self._augment_batch(
                header_rows, 
                context_headers=[],
                deviation_level=deviation_level, 
                is_header_batch=True
            )
            
            all_updates.extend(header_updates)
            logging.info(f"    Generated {len(header_updates)} header updates.")

            self._apply_local_updates(header_rows, header_updates)
            self._update_column_context_refs(data_rows, header_rows)

        # PHASE 2: AUGMENT DATA
        logging.info(f"  Phase 2: Augmenting {len(data_rows)} Data Rows...")
        
        batch_size = self.config.batch_size
        total_data_rows = len(data_rows)
        
        for i in range(0, total_data_rows, batch_size):
            batch = data_rows[i : i + batch_size]
            logging.info(f"    Batch {i}-{i+len(batch)}...")
            
            success = False
            retries = 3
            
            while retries > 0 and not success:
                try:
                    batch_updates = self._augment_batch(
                        batch, 
                        header_rows,
                        deviation_level=deviation_level,
                        is_header_batch=False
                    )
                    
                    target_count = sum(1 for row in batch for cell in row['cells'] if cell.get('role') == 'target')
                    if len(batch_updates) < target_count * 0.9:
                        logging.warning(f"Incomplete batch ({len(batch_updates)}/{target_count}). Retrying...")
                        raise ValueError("Low coverage")
                    
                    all_updates.extend(batch_updates)
                    success = True
                    
                except Exception as e:
                    retries -= 1
                    logging.warning(f"Retry {3-retries}: {e}")
                    time.sleep(2)
            
            if not success:
                logging.error("Skipping batch after failures.")

        logging.info(f"Completed. Total Updates: {len(all_updates)}")
        return all_updates
    
    def _run_augmentation_pipeline(self, original_html: str, payload: List[Dict], 
                                    registry: Dict, soup: Any, 
                                    llm_output_list: List[Dict]) -> str:
        """
        Run the full augmentation pipeline.
        This is the exact logic from html_synthesis.py run_augmentation_pipeline.
        """
        target_ids_truth = set()
        for row in payload:
            for cell in row['cells']:
                if cell.get('role') == 'target':
                    target_ids_truth.add(cell['id'])

        reconstructor = HTMLReconstructor(soup, registry)
        valid_updates, report = reconstructor.validate_updates(llm_output_list, target_ids_truth)

        if len(report['missing_ids']) > len(target_ids_truth) * 0.1:
            logging.warning("CRITICAL: LLM missed too many cells. Check your prompt or batch size.")
        
        final_html = reconstructor.reconstruct_html(valid_updates)
        
        return final_html


class HTMLReconstructor:
    """
    Reconstructs HTML from LLM updates.
    This is the exact logic from html_synthesis.py HTMLReconstructor.
    """
    
    def __init__(self, original_soup: Any, cell_registry: Dict):
        """
        Initialize reconstructor.
        
        Args:
            original_soup: The BeautifulSoup object of the original HTML.
            cell_registry: Dict mapping { 'cell_id': BeautifulSoup_Tag_Object }
        """
        self.soup = original_soup
        self.registry = cell_registry

    def validate_updates(self, llm_updates: List[Dict], target_ids: Set[str]) -> Tuple[List[Dict], Dict]:
        """
        Checks for hallucinations and missing updates.
        
        Args:
            llm_updates: List of dicts [{'id': '...', 'new_content': '...'}]
            target_ids: Set of IDs that were sent to LLM with role='target'
            
        Returns:
            Tuple of (valid_updates, error_report)
        """
        valid_updates = []
        error_report = {
            "hallucinated_ids": [],
            "missing_ids": [],
            "empty_content": []
        }

        received_map = {item['id']: item.get('new_content') for item in llm_updates}
        received_ids = set(received_map.keys())

        for uid in received_ids:
            if uid not in self.registry:
                error_report["hallucinated_ids"].append(uid)
            else:
                valid_updates.append({
                    "id": uid, 
                    "new_content": received_map[uid]
                })

        missing = target_ids - received_ids
        if missing:
            error_report["missing_ids"] = list(missing)

        if error_report["hallucinated_ids"]:
            logging.warning(f"IGNORED {len(error_report['hallucinated_ids'])} invalid IDs generated by LLM.")
        
        if error_report["missing_ids"]:
            logging.warning(f"MISSING updates for {len(error_report['missing_ids'])} target cells.")

        return valid_updates, error_report

    def reconstruct_html(self, valid_updates: List[Dict]) -> str:
        """
        Injects the validated text back into the BeautifulSoup object.
        
        Args:
            valid_updates: List of validated update dictionaries
            
        Returns:
            Final HTML string
        """
        success_count = 0
        
        for update in valid_updates:
            cell_id = update['id']
            new_text = update['new_content']
            
            if cell_id in self.registry:
                tag = self.registry[cell_id]
                tag.clear()
                
                if new_text and '\n' in new_text:
                    lines = new_text.split('\n')
                    for i, line in enumerate(lines):
                        tag.append(line)
                        if i < len(lines) - 1:
                            tag.append(self.soup.new_tag('br'))
                else:
                    tag.string = new_text
                
                success_count += 1
        
        logging.info(f"Successfully injected {success_count} cells into HTML.")
        return str(self.soup)
