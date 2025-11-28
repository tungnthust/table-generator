"""
Image Renderer Module
=====================
Handles rendering HTML to images and extracting annotations using Playwright.
"""

import json
import asyncio
from typing import Dict, Any, Optional
from pathlib import Path

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("Warning: Playwright not installed. Run: pip install playwright && playwright install chromium")
    async_playwright = None


async def render_html_to_image_and_annotate(
    html_content: str,
    output_image_path: str,
    output_annotation_path: str,
    page_width: int = 2480,
    page_height: int = 3508,
    draw_bboxes: bool = True
) -> Dict[str, Any]:
    """
    Render HTML content to an image and extract annotations.
    
    Args:
        html_content: Complete HTML document as a string
        output_image_path: Path to save the rendered PNG image
        output_annotation_path: Path to save the JSON annotations
        page_width: Width of the page in pixels (default: A4 at 300 DPI)
        page_height: Height of the page in pixels (default: A4 at 300 DPI)
        draw_bboxes: Whether to draw bounding boxes on the image
        
    Returns:
        Dictionary containing annotation data
    """
    if async_playwright is None:
        raise ImportError("Playwright is not installed. Run: pip install playwright && playwright install chromium")
    
    annotations = {
        "page_width": page_width,
        "page_height": page_height,
        "elements": []
    }
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Set viewport size
        await page.set_viewport_size({
            "width": page_width,
            "height": page_height
        })
        
        # Load HTML content
        await page.set_content(html_content, wait_until="networkidle")
        
        # Wait for any fonts to load
        await page.wait_for_timeout(500)
        
        # Extract annotations from annotated elements
        elements = await page.query_selector_all('.annotated-element, .annotated-cell-text')
        
        for element in elements:
            try:
                bbox = await element.bounding_box()
                if bbox:
                    element_type = await element.get_attribute('data-element-type') or 'cell'
                    text_content = await element.text_content()
                    
                    annotations["elements"].append({
                        "type": element_type,
                        "text": text_content.strip() if text_content else "",
                        "bbox": {
                            "x": bbox["x"],
                            "y": bbox["y"],
                            "width": bbox["width"],
                            "height": bbox["height"]
                        }
                    })
            except Exception as e:
                print(f"Warning: Could not extract annotation for element: {e}")
                continue
        
        # Draw bounding boxes if requested
        if draw_bboxes and annotations["elements"]:
            await page.evaluate("""
                () => {
                    const elements = document.querySelectorAll('.annotated-element, .annotated-cell-text');
                    elements.forEach((el, idx) => {
                        const rect = el.getBoundingClientRect();
                        const overlay = document.createElement('div');
                        overlay.style.position = 'absolute';
                        overlay.style.left = rect.left + 'px';
                        overlay.style.top = rect.top + 'px';
                        overlay.style.width = rect.width + 'px';
                        overlay.style.height = rect.height + 'px';
                        overlay.style.border = '2px solid red';
                        overlay.style.pointerEvents = 'none';
                        overlay.style.boxSizing = 'border-box';
                        document.body.appendChild(overlay);
                    });
                }
            """)
        
        # Take screenshot
        await page.screenshot(path=output_image_path, full_page=False)
        
        # Close browser
        await browser.close()
    
    # Save annotations
    Path(output_annotation_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_annotation_path, 'w', encoding='utf-8') as f:
        json.dump(annotations, f, indent=2, ensure_ascii=False)
    
    return annotations


async def render_html_file_to_image(
    html_path: str,
    output_image_path: str,
    output_annotation_path: str,
    page_width: int = 2480,
    page_height: int = 3508,
    draw_bboxes: bool = True
) -> Dict[str, Any]:
    """
    Render an HTML file to an image and extract annotations.
    
    Args:
        html_path: Path to the HTML file to render
        output_image_path: Path to save the rendered PNG image
        output_annotation_path: Path to save the JSON annotations
        page_width: Width of the page in pixels
        page_height: Height of the page in pixels
        draw_bboxes: Whether to draw bounding boxes on the image
        
    Returns:
        Dictionary containing annotation data
    """
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    return await render_html_to_image_and_annotate(
        html_content,
        output_image_path,
        output_annotation_path,
        page_width,
        page_height,
        draw_bboxes
    )


if __name__ == "__main__":
    # Test rendering
    test_html = """
    <!DOCTYPE html>
    <html>
    <head><title>Test</title></head>
    <body style="margin: 0; padding: 20px;">
        <div class="annotated-element" data-element-type="table">
            <table style="border-collapse: collapse; width: 100%;">
                <tr>
                    <td style="border: 1px solid black; padding: 10px;">
                        <span class="annotated-cell-text">Cell 1</span>
                    </td>
                    <td style="border: 1px solid black; padding: 10px;">
                        <span class="annotated-cell-text">Cell 2</span>
                    </td>
                </tr>
            </table>
        </div>
    </body>
    </html>
    """
    
    asyncio.run(render_html_to_image_and_annotate(
        test_html,
        "test_output.png",
        "test_output.json",
        page_width=800,
        page_height=600,
        draw_bboxes=True
    ))
    print("Test rendering complete!")
