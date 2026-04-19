import fitz  # PyMuPDF
import os
import json

def extract_text_with_coordinates(page):
    """Extract text with bounding box coordinates from a PDF page."""
    text_elements = []
    text_instances = page.get_text("dict")
    
    for block in text_instances.get("blocks", []):
        if "lines" in block:  # Text block
            for line in block["lines"]:
                for span in line["spans"]:
                    text = span["text"].strip()
                    if text:
                        bbox = span["bbox"]  # [x0, y0, x1, y1]
                        coords = [int(round(c)) for c in bbox]
                        text_elements.append({
                            "type": "text",
                            "content": text,
                            "coordinates": coords
                        })
    return text_elements

def extract_images(page):
    """Extract image information from a PDF page."""
    image_elements = []
    
    # Get images from blocks
    text_instances = page.get_text("dict")
    for block in text_instances.get("blocks", []):
        if "image" in block:
            bbox = block.get("bbox", [0, 0, 0, 0])
            coords = [int(round(c)) for c in bbox]
            image_elements.append({
                "type": "image",
                "content": None,
                "coordinates": coords
            })
    
    # Get images via get_images()
    image_list = page.get_images()
    if image_list and not image_elements:
        for _ in image_list:
            image_elements.append({
                "type": "image",
                "content": None,
                "coordinates": [0, 0, 0, 0]  # Unknown position
            })
    
    return image_elements

def pdf_to_json(pdf_path, title=None):
    """
    Convert a PDF file to JSON format.
    Returns a dictionary with book metadata and pages.
    """
    doc = fitz.open(pdf_path)
    if title is None:
        title = os.path.splitext(os.path.basename(pdf_path))[0]

    # Get metadata
    meta = doc.metadata
    author = meta.get('author', 'Unknown')
    
    book_data = {
        "title": title,
        "author": author,
        "total_pages": len(doc),
        "pages": []
    }

    for page_num in range(len(doc)):
        page = doc[page_num]
        
        # Extract text and images
        text_elements = extract_text_with_coordinates(page)
        image_elements = extract_images(page)
        
        # Combine all elements in order (text first, then images)
        all_elements = text_elements + image_elements
        
        page_dict = {
            "page_number": page_num + 1,
            "elements": all_elements,
            "text_count": len(text_elements),
            "image_count": len(image_elements)
        }
        
        book_data["pages"].append(page_dict)

    doc.close()
    return book_data

def merge_books(books_list):
    """Merge multiple book dictionaries into one."""
    return {
        "total_books": len(books_list),
        "books": books_list,
        "merged_date": __import__("datetime").datetime.now().isoformat()
    }