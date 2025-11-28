from bs4 import BeautifulSoup
import json
import uuid

def parse_html_with_id_reference(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    table = soup.find('table')
    
    if not table:
        raise ValueError("No <table> found in the HTML content")

    # --- SETUP REGISTRY ---
    # This dict will map 'cell_id' -> BeautifulSoup Tag Object
    cell_registry = {} 

    # --- STEP 1: Build Visual Grid ---
    rows = table.find_all('tr')
    grid = [] 
    header_row_indices = set()
    
    for r_idx, tr in enumerate(rows):
        while len(grid) <= r_idx: grid.append([])
        
        # Identify if this is a header row
        if (tr.parent.name == 'thead') or (tr.find('th') is not None):
            header_row_indices.add(r_idx)

        col_idx = 0
        cells = tr.find_all(['td', 'th'])
        
        for cell in cells:
            # Skip occupied slots (from previous rowspans)
            while col_idx < len(grid[r_idx]) and grid[r_idx][col_idx] is not None:
                col_idx += 1
            
            # Generate ID 
            cell_id = f"cell_{uuid.uuid4().hex[:8]}"
            
            # === CRITICAL: Register the tag ===
            cell_registry[cell_id] = cell
            # ==================================

            rowspan = int(cell.get('rowspan', 1))
            colspan = int(cell.get('colspan', 1))
            text_content = cell.get_text(separator=' ', strip=True)
            
            # Fill the grid (Visual representation)
            for r in range(rowspan):
                for c in range(colspan):
                    target_row = r_idx + r
                    while len(grid) <= target_row: grid.append([])
                    while len(grid[target_row]) <= col_idx + c: grid[target_row].append(None)
                    
                    grid[target_row][col_idx + c] = {
                        "id": cell_id,
                        "text": text_content,
                        "type": cell.name,
                        "is_real": (r == 0 and c == 0), # True only for the top-left of a merge
                        "colspan": colspan,
                        "origin_row": r_idx
                    }
            col_idx += colspan

    # --- STEP 2: Pre-calculate Column Headers ---
    max_cols = max(len(r) for r in grid)
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

    # --- STEP 3: Build JSON Payload ---
    llm_payload = []
    
    for r_idx, row_data in enumerate(grid):
        json_row = {
            "row_index": r_idx,
            "is_header_row": r_idx in header_row_indices,
            "cells": []
        }
        
        processed_ids_in_row = set()
        
        for c_idx, cell_info in enumerate(row_data):
            if not cell_info: continue
            if cell_info['id'] in processed_ids_in_row: continue
            
            processed_ids_in_row.add(cell_info['id'])
            
            cell_obj = {
                "id": cell_info['id'],
                "content": cell_info['text']
            }

            # === CONTEXT GENERATION ===
            current_colspan = cell_info.get('colspan', 1)
            potential_headers = []
            seen_context_ids = set()
            
            for span_offset in range(current_colspan):
                target_col = c_idx + span_offset
                col_headers = col_headers_map.get(target_col, [])
                
                for h in col_headers:
                    # Strict Ancestor Check: Only include headers visually above this cell
                    if h['row_index'] < cell_info['origin_row']:
                        if h['id'] not in seen_context_ids:
                            potential_headers.append({
                                "id": h['id'],
                                "content": h['content']
                            })
                            seen_context_ids.add(h['id'])
            
            cell_obj["column_context"] = potential_headers
            # ==========================

            # Determine Role
            # headers are also targets if they are real cells, 
            # merged parts of cells are just views
            cell_obj["role"] = "target" if cell_info['is_real'] else "merged_view"
            
            json_row['cells'].append(cell_obj)
            
        llm_payload.append(json_row)

    # Return all 3 required components
    return llm_payload, cell_registry, soup

import os
import json
import time
from google import genai
from google.genai import types

# --- CONFIGURATION ---
API_KEY = "" # Replace with your actual key
MODEL_ID = "gemini-2.5-flash-preview-09-2025" # 1.5 Pro is often better for complex instruction following than 3-preview
BATCH_SIZE = 15 

client = genai.Client(api_key=API_KEY)

def augment_batch(batch_rows, context_headers, deviation_level=0.5, is_header_batch=False):
    """
    Sends a batch of rows to the LLM.
    
    Args:
        batch_rows: The list of row objects to process.
        context_headers: The header rows (used as reference).
        deviation_level: Float (0.0 - 1.0). 0.1 = distinct synonyms. 0.9 = completely different table content.
        is_header_batch: Boolean. If True, prompts LLM to reinvent the columns.
    """
    
    # Adjust Temperature based on deviation (0.2 is conservative, 1.2 is wild)
    # We map 0.0-1.0 input to a 0.3-1.0 temperature range
    dynamic_temperature = 0.3 + (deviation_level * 0.7)

    payload = {
        "context_headers": context_headers, 
        "target_batch": batch_rows
    }

    # Dynamic instructions based on deviation
    if deviation_level < 0.3:
        creativity_instruction = "Low Deviation: Keep values very similar. Fix typos, change formatting, or use close synonyms. Keep numbers in the exact same magnitude."
    elif deviation_level < 0.7:
        creativity_instruction = "Medium Deviation: Generate distinct realistic variations. Change specific entity names (e.g., 'Company A' -> 'Company B'). Vary numbers by +/- 20%."
    else:
        creativity_instruction = "High Deviation: Re-imagine the data. You may change the industry or topic slightly if headers allow. Drastically change number magnitudes (e.g., Millions to Billions) if consistent."

    # Specific instruction for headers vs data
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
        response = client.models.generate_content(
            model=MODEL_ID,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                temperature=dynamic_temperature
            ),
            contents=json.dumps(payload)
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"  [!] Batch failed: {e}")
        return []

def apply_local_updates(rows, updates):
    """
    Helper: Updates the in-memory JSON rows with the results from the LLM.
    This is crucial so that subsequent batches see the *new* headers.
    """
    update_map = {u['id']: u['new_content'] for u in updates}
    count = 0
    for row in rows:
        for cell in row['cells']:
            if cell['id'] in update_map:
                cell['content'] = update_map[cell['id']]
                count += 1
    return count

def update_column_context_refs(data_rows, header_rows):
    """
    Advanced Helper: After augmenting headers, the 'column_context' list inside 
    data cells (which contains copies of header text) is now stale.
    We must refresh the data rows to reflect the NEW header text.
    """
    # 1. Create a map of {header_id: new_header_text}
    header_map = {}
    for r in header_rows:
        for cell in r['cells']:
            header_map[cell['id']] = cell['content']

    # 2. Walk through data rows and update their context lists
    for row in data_rows:
        for cell in row['cells']:
            if 'column_context' in cell:
                for ctx_item in cell['column_context']:
                    # If this context item refers to a header we just updated
                    if ctx_item['id'] in header_map:
                        ctx_item['content'] = header_map[ctx_item['id']]

def process_table_with_deviation(full_json_table, deviation_level=0.5):
    """
    Orchestrates the augmentation with Header-First strategy.
    """
    print(f"--- Processing Table (Deviation: {deviation_level}) ---")
    
    # 1. Split Headers and Data
    header_rows = [r for r in full_json_table if r.get('is_header_row', False)]
    data_rows = [r for r in full_json_table if not r.get('is_header_row', False)]
    
    all_updates = []

    # --- PHASE 1: AUGMENT HEADERS ---
    print("  > Phase 1: Augmenting Headers...")
    if header_rows:
        # We process all headers in one batch (usually small) or chunk if massive
        header_updates = augment_batch(
            header_rows, 
            context_headers=[], # Headers don't have parents usually, or self-ref
            deviation_level=deviation_level, 
            is_header_batch=True
        )
        
        all_updates.extend(header_updates)
        print(f"    - Generated {len(header_updates)} header updates.")

        # CRITICAL STEP: Update the local header objects immediately.
        # This ensures Phase 2 (Data) sees the NEW headers.
        apply_local_updates(header_rows, header_updates)
        
        # ALSO CRITICAL: Update the 'column_context' inside data_rows 
        # to match the new headers.
        update_column_context_refs(data_rows, header_rows)

    # --- PHASE 2: AUGMENT DATA ---
    print(f"  > Phase 2: Augmenting {len(data_rows)} Data Rows...")
    
    total_data_rows = len(data_rows)
    for i in range(0, total_data_rows, BATCH_SIZE):
        batch = data_rows[i : i + BATCH_SIZE]
        print(f"    - Batch {i}-{i+len(batch)}...")
        
        # Retry logic
        success = False
        retries = 3
        while retries > 0 and not success:
            try:
                # Note: We pass the *mutated* header_rows here
                batch_updates = augment_batch(
                    batch, 
                    header_rows, # passing updated headers
                    deviation_level=deviation_level,
                    is_header_batch=False
                )
                
                # Check for emptiness/laziness
                target_count = sum(1 for row in batch for cell in row['cells'] if cell.get('role') == 'target')
                if len(batch_updates) < target_count * 0.9: # Strict 90% coverage check
                     print(f"      [!] Incomplete batch ({len(batch_updates)}/{target_count}). Retrying...")
                     raise ValueError("Low coverage")
                
                all_updates.extend(batch_updates)
                success = True
                
            except Exception as e:
                retries -= 1
                print(f"      [x] Retry {3-retries}: {e}")
                time.sleep(2)
        
        if not success:
            print("      [!!!] Skipping batch after failures.")

    print(f"--- Completed. Total Updates: {len(all_updates)} ---")
    return all_updates

import logging

# Setup simple logging to see validation warnings
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

class HTMLReconstructor:
    def __init__(self, original_soup, cell_registry):
        """
        :param original_soup: The BeautifulSoup object of the original HTML.
        :param cell_registry: Dict mapping { 'cell_id': BeautifulSoup_Tag_Object }
                              (returned from the parsing function).
        """
        self.soup = original_soup
        self.registry = cell_registry

    def validate_updates(self, llm_updates, target_ids):
        """
        Checks for hallucinations and missing updates.
        
        :param llm_updates: List of dicts [{'id': '...', 'new_content': '...'}]
        :param target_ids: Set of IDs that were sent to LLM with role='target'
        :return: (valid_updates, error_report)
        """
        valid_updates = []
        error_report = {
            "hallucinated_ids": [], # IDs returned by LLM that don't exist in our table
            "missing_ids": [],      # IDs we asked for but LLM didn't return
            "empty_content": []     # IDs where LLM returned null/empty string (might be valid, but worth noting)
        }

        # 1. Create a map of received updates for fast lookup
        received_map = {item['id']: item.get('new_content') for item in llm_updates}
        received_ids = set(received_map.keys())

        # 2. Check for Hallucinations (Security Check)
        for uid in received_ids:
            if uid not in self.registry:
                error_report["hallucinated_ids"].append(uid)
            else:
                # Only add to valid list if ID actually exists in our registry
                valid_updates.append({
                    "id": uid, 
                    "new_content": received_map[uid]
                })

        # 3. Check for Missing Targets (Coverage Check)
        # Note: target_ids comes from your initial parsing logic where role='target'
        missing = target_ids - received_ids
        if missing:
            error_report["missing_ids"] = list(missing)

        # 4. Log the results
        if error_report["hallucinated_ids"]:
            logging.warning(f"IGNORED {len(error_report['hallucinated_ids'])} invalid IDs generated by LLM.")
        
        if error_report["missing_ids"]:
            logging.warning(f"MISSING updates for {len(error_report['missing_ids'])} target cells.")

        return valid_updates, error_report

    def reconstruct_html(self, valid_updates):
        """
        Injects the validated text back into the BeautifulSoup object.
        """
        success_count = 0
        
        for update in valid_updates:
            cell_id = update['id']
            new_text = update['new_content']
            
            # Double check registry existence (redundant if validated, but safe)
            if cell_id in self.registry:
                tag = self.registry[cell_id]
                
                # --- SAFE CONTENT REPLACEMENT ---
                # 1. Clear existing content (removes old text, <b>, <span>, etc.)
                tag.clear()
                
                # 2. Handle Newlines: LLM might return "Row 1\nRow 2"
                # We want to convert \n to <br/> tags to preserve structure visually
                if new_text and '\n' in new_text:
                    lines = new_text.split('\n')
                    for i, line in enumerate(lines):
                        tag.append(line)
                        # Add <br> after every line except the last one
                        if i < len(lines) - 1:
                            tag.append(self.soup.new_tag('br'))
                else:
                    # Simple text injection
                    tag.string = new_text
                
                success_count += 1
        
        logging.info(f"Successfully injected {success_count} cells into HTML.")
        return str(self.soup) # Return the final HTML string

# --- WORKFLOW EXAMPLE ---

def run_augmentation_pipeline(original_html,payload, registry, soup, llm_output_list):
    # 1. PARSE (Using the function from previous steps)
    # Ensure your parser returns: payload (for LLM), registry (for ID mapping), and soup
    
    # We tweak the parser to ensure HEADERS are also marked as 'target'
    # (In the previous code, ensure 'is_real': True applies to headers too)
    
    # 2. IDENTIFY TARGETS (The "Truth" list)
    # We collect all IDs that we marked as 'target' in the payload
    target_ids_truth = set()
    for row in payload:
        for cell in row['cells']:
            if cell.get('role') == 'target':
                target_ids_truth.add(cell['id'])

    # 3. VALIDATE
    reconstructor = HTMLReconstructor(soup, registry)
    valid_updates, report = reconstructor.validate_updates(llm_output_list, target_ids_truth)

    # 4. DECISION GATE
    # If missing_ids is too high (e.g. > 10%), you might want to abort or retry
    if len(report['missing_ids']) > len(target_ids_truth) * 0.1:
        print("CRITICAL: LLM missed too many cells. Check your prompt or batch size.")
        # Proceeding anyway for demo purposes, but in prod you might raise Error
    
    # 5. INJECT
    final_html = reconstructor.reconstruct_html(valid_updates)
    
    return final_html



# --- USAGE EXAMPLE ---
html_input = """
<table>
  <thead>
    <tr>
      <th rowspan="2">CHỈ TIÊU<br>(ITEMS)</th>
      <th rowspan="2">Mã số<br>(Code)</th>
      <th rowspan="2">Thuyết minh<br>(Notes)</th>
      <th colspan="2">Quý II (Quarter II)</th>
      <th colspan="2">Lũy kế từ đầu năm đến cuối quý này<br>(Accumulated from the beginning of the year to the end of this quarter)</th>
    </tr>
    <tr>
      <th>2025</th>
      <th>2024</th>
      <th>2025</th>
      <th>2024</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>1. Doanh thu bán hàng và cung cấp dịch vụ<br>Sales and service revenue</strong></td>
      <td><strong>01</strong></td>
      <td><strong>VII.1</strong></td>
      <td><strong>5.348.435.292.083</strong></td>
      <td><strong>8.505.975.540.213</strong></td>
      <td><strong>24.095.612.757.093</strong></td>
      <td><strong>32.141.655.308.511</strong></td>
    </tr>
    <tr>
      <td>2. Các khoản giảm trừ<br>Deductions</td>
      <td>02</td>
      <td><strong>VII.2</strong></td>
      <td>-</td>
      <td>-</td>
      <td></td>
      <td></td>
    </tr>
    <tr>
      <td><strong>3. Doanh thu thuần về bán hàng và cung cấp dịch vụ</strong></td>
      <td><strong>10</strong></td>
      <td></td>
      <td><strong>5.348.435.292.083</strong></td>
      <td><strong>8.505.975.540.213</strong></td>
      <td><strong>24.095.612.757.093</strong></td>
      <td><strong>32.141.655.308.511</strong></td>
    </tr>
    <tr>
      <td colspan="3"><strong>(10=01-03)</strong></td>
      <td><strong>-</strong></td>
      <td><strong>-</strong></td>
      <td></td>
      <td></td>
    </tr>
    <tr>
      <td><strong>4. Giá vốn hàng bán<br>Cost of goods sold</strong></td>
      <td><strong>11</strong></td>
      <td><strong>VII.3</strong></td>
      <td><strong>5.121.280.464.106</strong></td>
      <td><strong>8.236.916.626.478</strong></td>
      <td><strong>23.132.724.351.662</strong></td>
      <td><strong>30.988.160.399.412</strong></td>
    </tr>
    <tr>
      <td><strong>5. Lợi nhuận gộp về bán hàng và cung cấp dịch vụ<br>Gross profit from sales and service provision</strong></td>
      <td><strong>20</strong></td>
      <td></td>
      <td><strong>227.154.827.977</strong></td>
      <td><strong>269.058.913.735</strong></td>
      <td><strong>962.888.405.431</strong></td>
      <td><strong>1.153.494.909.099</strong></td>
    </tr>
    <tr>
      <td><strong>(20=10-11)</strong></td>
      <td></td>
      <td></td>
      <td><strong>-</strong></td>
      <td><strong>-</strong></td>
      <td></td>
      <td></td>
    </tr>
    <tr>
      <td>6. Doanh thu hoạt động tài chính<br>Financial income</td>
      <td>21</td>
      <td><strong>VII.4</strong></td>
      <td>7.228.119.766</td>
      <td>38.556.786.514</td>
      <td>43.099.195.505</td>
      <td>38.743.856.226</td>
    </tr>
    <tr>
      <td>7. Chi phí tài chính<br>Financial expenses</td>
      <td>22</td>
      <td><strong>VII.5</strong></td>
      <td>37.368.341.025</td>
      <td>34.430.111.882</td>
      <td>111.484.630.011</td>
      <td>130.676.317.172</td>
    </tr>
    <tr>
      <td>- Trong đó: Chi phí lãi vay<br>(-Including: Interest expense)</td>
      <td>23</td>
      <td></td>
      <td>37.313.274.261</td>
      <td>50.434.140.041</td>
      <td>103.562.415.031</td>
      <td>130.676.317.172</td>
    </tr>
    <tr>
      <td>8. Chi phí bán hàng<br>Selling expenses</td>
      <td>24</td>
      <td><strong>VII.8</strong></td>
      <td>212.557.831.892</td>
      <td>250.271.078.260</td>
      <td>815.098.280.204</td>
      <td>918.933.757.518</td>
    </tr>
    <tr>
      <td>9. Chi phí quản lý doanh nghiệp<br>General and administration costs</td>
      <td>25</td>
      <td><strong>VII.9</strong></td>
      <td>11.637.292.329</td>
      <td>11.370.497.646</td>
      <td>44.834.633.149</td>
      <td>38.979.448.711</td>
    </tr>
    <tr>
      <td><strong>10. Lợi nhuận thuần từ hoạt động kinh doanh<br>Net operating profit</strong></td>
      <td><strong>30</strong></td>
      <td></td>
      <td><strong>(27.180.517.503)</strong></td>
      <td><strong>11.544.012.461</strong></td>
      <td><strong>34.570.057.572</strong></td>
      <td><strong>103.649.241.924</strong></td>
    </tr>
    <tr>
      <td><strong>{30=20+(21-22)-(24+25)}</strong></td>
      <td></td>
      <td></td>
      <td><strong>-</strong></td>
      <td><strong>-</strong></td>
      <td><strong>-</strong></td>
      <td><strong>-</strong></td>
    </tr>
    <tr>
      <td>11. Thu nhập khác<br>Other income</td>
      <td>31</td>
      <td><strong>VII.6</strong></td>
      <td>33.025.225.198</td>
      <td>29.555.113.674</td>
      <td>74.210.564.259</td>
      <td>58.380.282.906</td>
    </tr>
    <tr>
      <td>12. Chi phí khác<br>Other expenses</td>
      <td>32</td>
      <td><strong>VII.7</strong></td>
      <td>906.372.050</td>
      <td>258.374.611</td>
      <td>1.467.237.858</td>
      <td>1.434.162.769</td>
    </tr>
    <tr>
      <td><strong>13. Lợi nhuận khác (40=31-32)<br>Results of other activities (40=31-32)</strong></td>
      <td><strong>40</strong></td>
      <td></td>
      <td><strong>32.118.853.148</strong></td>
      <td><strong>29.296.739.063</strong></td>
      <td><strong>72.743.326.401</strong></td>
      <td><strong>56.946.120.137</strong></td>
    </tr>
  </tbody>
</table>
"""

payload, registry, soup = parse_html_with_id_reference(html_input)

print(json.dumps(payload, indent=2, ensure_ascii=False))

print(f"Sending data to {MODEL_ID}...")
updates = process_table_with_deviation(payload, deviation_level=0.8)
synthesis_html = run_augmentation_pipeline(original_html=html_input, payload=payload, registry=registry, soup=soup, llm_output_list=updates)
file_path = 'table.html'
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(synthesis_html)

# Confirm file creation by printing the path and size
print(f"Saved HTML to {file_path}")