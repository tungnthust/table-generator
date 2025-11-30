import asyncio
from playwright.async_api import async_playwright
import os
import json

# --- Improved JavaScript Helper Function ---
# This script better detects browser-wrapped lines by using word boundaries
# and more robust line detection logic
JS_GET_LINE_BBOXES = """
async (element) => {
  if (!element) return [];

  // Get all text nodes in the element (handles multiple text nodes)
  const getTextNodes = (node) => {
    const textNodes = [];
    if (node.nodeType === Node.TEXT_NODE) {
      if (node.textContent.trim()) {
        textNodes.push(node);
      }
    } else {
      for (const child of node.childNodes) {
        textNodes.push(...getTextNodes(child));
      }
    }
    return textNodes;
  };

  const textNodes = getTextNodes(element);
  if (textNodes.length === 0) return [];

  const range = document.createRange();
  const lineBboxes = [];
  let currentLine = {
    rects: [],
    text: ''
  };

  // Process each text node
  for (const textNode of textNodes) {
    const text = textNode.textContent;
    
    // Split text into words and spaces to get better boundaries
    const tokens = text.match(/\\S+|\\s+/g) || [];
    let currentOffset = 0;
    
    for (const token of tokens) {
      const startOffset = currentOffset;
      const endOffset = currentOffset + token.length;
      
      // Set range for this token
      try {
        range.setStart(textNode, startOffset);
        range.setEnd(textNode, endOffset);
        const rects = Array.from(range.getClientRects());
        
        if (rects.length > 0) {
          // Check if this token spans multiple lines
          if (rects.length > 1) {
            // Token is split across lines
            for (let i = 0; i < rects.length; i++) {
              const rect = rects[i];
              const isNewLine = currentLine.rects.length === 0 || 
                               Math.abs(rect.top - currentLine.rects[0].top) > 2;
              
              if (isNewLine && currentLine.rects.length > 0) {
                // Save the previous line
                const bbox = calculateBbox(currentLine.rects);
                if (bbox) {
                  lineBboxes.push({
                    ...bbox,
                    text: currentLine.text.trim()
                  });
                }
                currentLine = { rects: [], text: '' };
              }
              
              currentLine.rects.push(rect);
              // Only add the token text once (on first rect)
              if (i === 0) {
                currentLine.text += token;
              }
            }
          } else {
            // Single rect for this token
            const rect = rects[0];
            const isNewLine = currentLine.rects.length === 0 || 
                             Math.abs(rect.top - currentLine.rects[0].top) > 2;
            
            if (isNewLine && currentLine.rects.length > 0) {
              // Save the previous line
              const bbox = calculateBbox(currentLine.rects);
              if (bbox) {
                lineBboxes.push({
                  ...bbox,
                  text: currentLine.text.trim()
                });
              }
              currentLine = { rects: [], text: '' };
            }
            
            currentLine.rects.push(rect);
            currentLine.text += token;
          }
        }
      } catch (e) {
        console.error('Range error:', e);
      }
      
      currentOffset = endOffset;
    }
  }

  // Don't forget the last line
  if (currentLine.rects.length > 0) {
    const bbox = calculateBbox(currentLine.rects);
    if (bbox) {
      lineBboxes.push({
        ...bbox,
        text: currentLine.text.trim()
      });
    }
  }

  range.detach();
  return lineBboxes;

  // Helper function to calculate union bbox from multiple rects
  function calculateBbox(rects) {
    if (rects.length === 0) return null;
    
    let minX = Infinity, minY = Infinity;
    let maxX = -Infinity, maxY = -Infinity;
    
    for (const rect of rects) {
      minX = Math.min(minX, rect.left);
      minY = Math.min(minY, rect.top);
      maxX = Math.max(maxX, rect.right);
      maxY = Math.max(maxY, rect.bottom);
    }
    
    return {
      x: Math.round(minX),
      y: Math.round(minY),
      width: Math.round(maxX - minX),
      height: Math.round(maxY - minY)
    };
  }
}
"""

# Alternative approach using a more sophisticated method
JS_GET_LINE_BBOXES_V2 = """
async (element) => {
  if (!element) return [];

  // Clone the element to manipulate without affecting the original
  const clone = element.cloneNode(true);
  clone.style.position = 'absolute';
  clone.style.visibility = 'hidden';
  clone.style.width = element.offsetWidth + 'px';
  document.body.appendChild(clone);

  const lines = [];
  const originalText = element.textContent || '';
  
  // Binary search approach to find line breaks
  const findLineBreaks = () => {
    const lineBreaks = [0]; // Start of first line
    let currentPos = 0;
    
    const testRange = document.createRange();
    const textNode = clone.firstChild || clone;
    
    while (currentPos < originalText.length) {
      // Binary search for the end of current line
      let left = currentPos + 1;
      let right = originalText.length;
      let lineEnd = currentPos;
      
      while (left <= right) {
        const mid = Math.floor((left + right) / 2);
        
        try {
          testRange.setStart(textNode, currentPos);
          testRange.setEnd(textNode, Math.min(mid, originalText.length));
          const rects = testRange.getClientRects();
          
          // Check if text spans multiple lines
          if (rects.length > 1) {
            // Text wraps to next line
            right = mid - 1;
          } else if (rects.length === 1) {
            // Still on same line
            lineEnd = mid;
            left = mid + 1;
          }
        } catch (e) {
          break;
        }
      }
      
      if (lineEnd > currentPos) {
        lineBreaks.push(lineEnd);
        currentPos = lineEnd;
      } else {
        currentPos++;
      }
    }
    
    testRange.detach();
    return lineBreaks;
  };

  // Get line breaks
  const lineBreaks = findLineBreaks();
  
  // Clean up clone
  document.body.removeChild(clone);

  // Now get actual bounding boxes for each line from the original element
  const range = document.createRange();
  const textNode = element.firstChild || element;
  
  for (let i = 0; i < lineBreaks.length - 1; i++) {
    const start = lineBreaks[i];
    const end = lineBreaks[i + 1];
    
    try {
      range.setStart(textNode, start);
      range.setEnd(textNode, end);
      const rects = range.getClientRects();
      
      if (rects.length > 0) {
        // Calculate union of all rects for this line
        let minX = Infinity, minY = Infinity;
        let maxX = -Infinity, maxY = -Infinity;
        
        for (const rect of rects) {
          minX = Math.min(minX, rect.left);
          minY = Math.min(minY, rect.top);
          maxX = Math.max(maxX, rect.right);
          maxY = Math.max(maxY, rect.bottom);
        }
        
        lines.push({
          x: Math.round(minX),
          y: Math.round(minY),
          width: Math.round(maxX - minX),
          height: Math.round(maxY - minY),
          text: originalText.substring(start, end).trim()
        });
      }
    } catch (e) {
      console.error('Range error:', e);
    }
  }
  
  range.detach();
  return lines;
}
"""

async def get_table_cell_positions(table_element, page):
    """
    Analyzes table structure to get cell positions with rowspan/colspan support.
    Returns a dictionary mapping cell elements to their grid positions.
    """
    cell_positions = {}
    
    # JavaScript to analyze table structure and return cell positions
    js_analyze_table = """
    (tableElement) => {
        const cells = [];
        const rows = tableElement.querySelectorAll('tr');
        const grid = []; // Track occupied cells
        
        rows.forEach((row, rowIndex) => {
            if (!grid[rowIndex]) grid[rowIndex] = [];
            
            const rowCells = row.querySelectorAll('td, th');
            let colIndex = 0;
            
            rowCells.forEach((cell) => {
                // Skip already occupied cells (from rowspan)
                while (grid[rowIndex][colIndex]) {
                    colIndex++;
                }
                
                const rowspan = parseInt(cell.getAttribute('rowspan') || '1');
                const colspan = parseInt(cell.getAttribute('colspan') || '1');
                
                // Mark grid cells as occupied
                for (let r = 0; r < rowspan; r++) {
                    for (let c = 0; c < colspan; c++) {
                        if (!grid[rowIndex + r]) grid[rowIndex + r] = [];
                        grid[rowIndex + r][colIndex + c] = true;
                    }
                }
                
                // Store cell position info
                cells.push({
                    rowIndex: rowIndex,
                    colIndex: colIndex,
                    rowspan: rowspan,
                    colspan: colspan,
                    element: cell
                });
                
                colIndex += colspan;
            });
        });
        
        // Convert to serializable format
        return cells.map(cellInfo => ({
            row_start: cellInfo.rowIndex,
            row_end: cellInfo.rowIndex + cellInfo.rowspan - 1,
            column_start: cellInfo.colIndex,
            column_end: cellInfo.colIndex + cellInfo.colspan - 1
        }));
    }
    """
    
    # Get cell positions from JavaScript
    positions = await page.evaluate(js_analyze_table, table_element)
    return positions

async def measure_table_dimensions(
    html_content: str,
    initial_width: int = 4000,
    initial_height: int = 4000,
    margin: int = 100
) -> dict:
    """
    Measure the actual dimensions of the rendered table.
    
    Args:
        html_content: The HTML content to render
        initial_width: Initial viewport width (should be large enough)
        initial_height: Initial viewport height (should be large enough)
        margin: Margin to add around the table (on all sides)
        
    Returns:
        Dictionary with 'width', 'height', and 'bbox' of the table
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        # Use a large viewport to allow table to render at natural size
        await page.set_viewport_size({"width": initial_width, "height": initial_height})
        await page.set_content(html_content, wait_until="networkidle")
        await page.wait_for_timeout(300)
        
        # Find the table element and get its bounding box
        table_element = await page.query_selector(".bbox-content-target")
        if not table_element:
            table_element = await page.query_selector(".annotated-element")
        
        if table_element:
            bbox = await table_element.bounding_box()
            if bbox:
                await browser.close()
                # Calculate final image size:
                # - Table starts at bbox['x'], bbox['y'] (which includes left/top margin from HTML)
                # - Add table width/height
                # - Add additional margin on right/bottom for breathing room
                final_width = int(bbox['x'] + bbox['width'] + margin)
                final_height = int(bbox['y'] + bbox['height'] + margin)
                return {
                    "width": final_width,
                    "height": final_height,
                    "bbox": bbox,
                    "table_width": int(bbox['width']),
                    "table_height": int(bbox['height'])
                }
        
        await browser.close()
        # Fallback to initial dimensions if table not found
        return {
            "width": initial_width,
            "height": initial_height,
            "bbox": None,
            "table_width": None,
            "table_height": None
        }


async def render_html_to_image_and_annotate(
    html_content: str,
    output_image_path: str,
    output_annotation_path: str,
    page_width: int,
    page_height: int,
    draw_bboxes_on_image: bool = True,
    use_v2_detection: bool = False,  # Toggle between detection methods
    dynamic_size: bool = False,  # Enable dynamic sizing based on table dimensions
    size_margin: int = 100,  # Margin to add when using dynamic sizing
    raw_table_html: str = None  # Raw HTML of the table for dynamic sizing
):
    """
    Renders HTML content to an image and extracts bounding box annotations.
    Now with improved line detection for browser-wrapped text.
    
    Args:
        html_content: HTML content to render
        output_image_path: Path for output image
        output_annotation_path: Path for output annotations JSON
        page_width: Page width (used as initial/max width if dynamic_size=True)
        page_height: Page height (used as initial/max height if dynamic_size=True)
        draw_bboxes_on_image: Whether to draw bounding boxes on output image
        use_v2_detection: Toggle between line detection methods
        dynamic_size: If True, adjust page size to fit actual table dimensions
        size_margin: Margin to add around the table when using dynamic sizing
    """
    # If dynamic sizing is enabled, measure the table first
    actual_width = page_width
    actual_height = page_height
    
    if dynamic_size:
        dimensions = await measure_table_dimensions(
            html_content,
            initial_width=max(page_width, 4000),
            initial_height=max(page_height, 4000),
            margin=size_margin
        )
        actual_width = dimensions['width']
        actual_height = dimensions['height']
        table_w = dimensions.get('table_width', 'N/A')
        table_h = dimensions.get('table_height', 'N/A')
        print(f"Dynamic sizing: Table size {table_w}x{table_h}, Image size {actual_width}x{actual_height} (margin: {size_margin}px)")
    
    annotations = {
        "image_path": os.path.basename(output_image_path),
        "image_width": actual_width,
        "image_height": actual_height,
        "html": raw_table_html,
        "elements": []
    }

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.set_viewport_size({"width": actual_width, "height": actual_height})
        await page.set_content(html_content, wait_until="networkidle")
        await page.wait_for_timeout(300)  # Give more time for rendering

        # Choose which detection method to use
        js_function = JS_GET_LINE_BBOXES_V2 if use_v2_detection else JS_GET_LINE_BBOXES

        await page.screenshot(path=output_image_path, full_page=True)

        elements_to_annotate = await page.query_selector_all(".annotated-element")

        for element_handle in elements_to_annotate:
            element_class = await element_handle.get_attribute("data-element-type")

            bbox_targets = await element_handle.query_selector_all(".bbox-content-target")
            if not bbox_targets:
                bbox_targets = [element_handle]

            for bbox_target_handle in bbox_targets:
                bbox = await bbox_target_handle.bounding_box()
                
                if bbox and bbox['width'] > 0 and bbox['height'] > 0:
                    print(f"Processing element of type '{element_class}' with bbox {bbox}")
                    element_content = await bbox_target_handle.text_content()

                    if element_class == "table":
                      # Get cell positions first
                      cell_positions = await get_table_cell_positions(bbox_target_handle, page)
                      
                      cell_elements = await bbox_target_handle.query_selector_all("td, th")
                      cell_annotations = []
                      
                      for idx, cell_handle in enumerate(cell_elements):
                          cell_bbox = await cell_handle.bounding_box()
                          if cell_bbox and cell_bbox['width'] > 0 and cell_bbox['height'] > 0:
                              cell_text = await cell_handle.text_content()
                              
                              content_spans = await cell_handle.query_selector_all(".annotated-cell-text")
                              content_annotations = []
                              
                              for content_handle in content_spans:
                                  try:
                                      # Call the improved line detection function
                                      line_bboxes = await page.evaluate(js_function, content_handle)
                                      
                                      if line_bboxes and len(line_bboxes) > 0:
                                          for i, line_data in enumerate(line_bboxes):
                                              # Extract text if included in the result
                                              line_text = line_data.get('text', f"Line {i+1}")
                                              line_bbox = {k: v for k, v in line_data.items() if k != 'text'}
                                              
                                              content_annotations.append({
                                                  "type": "cell_content_line",
                                                  "bbox": {k: int(v) for k, v in line_bbox.items()},
                                                  "text_content": line_text,
                                                  "line_number": i + 1
                                              })
                                      else:
                                          # Fallback to full cell content
                                          content_bbox = await content_handle.bounding_box()
                                          if content_bbox and content_bbox['width'] > 0 and content_bbox['height'] > 0:
                                              content_annotations.append({
                                                  "type": "cell_content_line",
                                                  "bbox": {k: int(v) for k, v in content_bbox.items()},
                                                  "text_content": (await content_handle.text_content()).strip()
                                              })
                                          
                                  except Exception as e:
                                      print(f"Error getting line bboxes: {e}")
                                      # Fallback
                                      content_bbox = await content_handle.bounding_box()
                                      if content_bbox and content_bbox['width'] > 0 and content_bbox['height'] > 0:
                                          content_annotations.append({
                                              "type": "cell_content_line",
                                              "bbox": {k: int(v) for k, v in content_bbox.items()},
                                              "text_content": (await content_handle.text_content()).strip()
                                          })
                              
                              # Create cell annotation with grid position
                              cell_annotation = {
                                  "type": "table_cell",
                                  "bbox": {k: int(v) for k, v in cell_bbox.items()},
                                  "text_content": cell_text.strip(),
                                  "children": content_annotations
                              }
                              
                              # Add grid position if available
                              if idx < len(cell_positions):
                                  cell_annotation.update({
                                      "row_start": cell_positions[idx]["row_start"],
                                      "row_end": cell_positions[idx]["row_end"],
                                      "column_start": cell_positions[idx]["column_start"],
                                      "column_end": cell_positions[idx]["column_end"]
                                  })
                              
                              cell_annotations.append(cell_annotation)
                      
                      annotations["elements"].append({
                          "type": element_class,
                          "bbox": {k: int(v) for k, v in bbox.items()},
                          "text_content": "<table>",
                          "children": cell_annotations
                      })
                    else:
                        # For regular text elements, also try to get line bboxes
                        if element_class == "text":
                            try:
                                line_bboxes = await page.evaluate(js_function, bbox_target_handle)
                                if line_bboxes and len(line_bboxes) > 1:
                                    # Multiple lines detected
                                    line_annotations = []
                                    for i, line_data in enumerate(line_bboxes):
                                        line_text = line_data.get('text', f"Line {i+1}")
                                        line_bbox = {k: v for k, v in line_data.items() if k != 'text'}
                                        line_annotations.append({
                                            "type": "text_line",
                                            "bbox": {k: int(v) for k, v in line_bbox.items()},
                                            "text_content": line_text,
                                            "line_number": i + 1
                                        })
                                    
                                    annotations["elements"].append({
                                        "type": element_class,
                                        "bbox": {k: int(v) for k, v in bbox.items()},
                                        "text_content": element_content.strip(),
                                        "children": line_annotations
                                    })
                                else:
                                    # Single line or detection failed
                                    annotations["elements"].append({
                                        "type": element_class,
                                        "bbox": {k: int(v) for k, v in bbox.items()},
                                        "text_content": element_content.strip()
                                    })
                            except Exception as e:
                                print(f"Error detecting lines in text element: {e}")
                                annotations["elements"].append({
                                    "type": element_class,
                                    "bbox": {k: int(v) for k, v in bbox.items()},
                                    "text_content": element_content.strip()
                                })
                        else:
                            annotations["elements"].append({
                                "type": element_class,
                                "bbox": {k: int(v) for k, v in bbox.items()},
                                "text_content": element_content.strip()
                            })

        await browser.close()

    with open(output_annotation_path, "w", encoding="utf-8") as f:
        json.dump(annotations, f, indent=4, ensure_ascii=False)

    print(f"Annotations saved to {output_annotation_path}")

    if draw_bboxes_on_image:
        try:
            from PIL import Image, ImageDraw, ImageFont
            img = Image.open(output_image_path)
            draw = ImageDraw.Draw(img)
            
            color_map = {
                "text": "red",
                "text_line": "magenta",  # Individual lines in text elements
                "table": "blue",
                "table_cell": "orange",
                "cell_content_line": "green",
                "image": "purple"
            }

            def draw_recursive(elements_list, depth=0):
                for element in elements_list:
                    bbox = element["bbox"]
                    element_type = element["type"]
                    color = color_map.get(element_type, "black")
                    
                    line_width = max(1, 3 - depth)
                    
                    draw.rectangle([
                        bbox['x'], bbox['y'],
                        bbox['x'] + bbox['width'], bbox['y'] + bbox['height']
                    ], outline=color, width=line_width)
                    
                    # Add line number labels for debugging
                    if element_type in ["text_line", "cell_content_line"] and "line_number" in element:
                        try:
                            # Try to load a font, fall back to default if not available
                            font = ImageFont.load_default()
                            draw.text((bbox['x'] - 20, bbox['y']), 
                                    f"L{element['line_number']}", 
                                    fill=color, font=font)
                        except:
                            pass
                    
                    if "children" in element:
                        draw_recursive(element["children"], depth + 1)

            draw_recursive(annotations["elements"])

            validated_image_path = output_image_path.replace(".png", "_validated.png")
            img.save(validated_image_path)
            print(f"Validation image with bboxes saved to {validated_image_path}")
        except ImportError:
            print("Pillow not installed. Skipping bbox drawing. 'pip install Pillow'")
        except Exception as e:
            print(f"Error drawing bboxes: {e}")


# Example usage for testing
if __name__ == "__main__":
    # Test HTML with text that will wrap
    test_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body { 
                font-family: Arial, sans-serif; 
                margin: 20px;
                font-size: 14px;
            }
            .text-block {
                width: 300px;
                border: 1px solid #ccc;
                padding: 10px;
                margin-bottom: 20px;
            }
            table {
                border-collapse: collapse;
                width: 400px;
            }
            td, th {
                border: 1px solid #ddd;
                padding: 8px;
                width: 100px;
            }
        </style>
    </head>
    <body>
        <div class="annotated-element text-block" data-element-type="text">
            <div class="bbox-content-target">
                This is a long piece of text that will definitely wrap to multiple lines when rendered in a narrow container. Each line should get its own bounding box.
            </div>
        </div>
        
        <table class="annotated-element" data-element-type="table">
            <tbody class="bbox-content-target">
                <tr>
                    <td><span class="annotated-cell-text">Short text</span></td>
                    <td><span class="annotated-cell-text">This cell contains much longer text that will wrap to multiple lines within the table cell</span></td>
                </tr>
                <tr>
                    <td><span class="annotated-cell-text">Another cell with medium length text content</span></td>
                    <td><span class="annotated-cell-text">Final cell</span></td>
                </tr>
            </tbody>
        </table>
    </body>
    </html>
    """
    
    asyncio.run(render_html_to_image_and_annotate(
        html_content=test_html,
        output_image_path="test_output.png",
        output_annotation_path="test_annotations.json",
        page_width=800,
        page_height=600,
        draw_bboxes_on_image=True,
        use_v2_detection=False  # Try both False and True to see which works better
    ))
