#!/usr/bin/env uv run
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pillow",
#     "reportlab",
# ]
# ///
import argparse
from PIL import Image, ImageOps
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, A3, A5, LETTER
import os
import sys
from typing import Tuple, List

# Standard page sizes in pixels at 72 DPI
PAGE_SIZES = {
    'a4': A4,
    'a3': A3,
    'a5': A5,
    'letter': LETTER
}

def mm_to_pixels(mm: float, dpi: int = 72) -> int:
    """Convert millimeters to pixels at given DPI."""
    return int(mm * dpi / 25.4)

def parse_margin(margin_str: str) -> int:
    """Parse margin string (either pixels or mm) to pixels."""
    if margin_str.endswith('mm'):
        return mm_to_pixels(float(margin_str[:-2]))
    elif margin_str.endswith('px'):
        return int(margin_str[:-2])
    else:
        try:
            return int(margin_str)
        except ValueError:
            raise ValueError("Margin must be specified in px, mm, or as plain pixels")

def trim_whitespace(image: Image.Image) -> Image.Image:
    """Trim whitespace from image edges."""
    # Convert to RGB if image is in RGBA mode
    if image.mode == 'RGBA':
        background = Image.new('RGBA', image.size, (255, 255, 255, 255))
        background.paste(image, mask=image.split()[3])  # Use alpha channel as mask
        image = background.convert('RGB')
    elif image.mode != 'RGB':
        image = image.convert('RGB')

    # Get the bounding box of non-white pixels
    bbox = image.getbbox()
    if bbox:
        return image.crop(bbox)
    return image

def find_content_gaps(image: Image.Image, min_gap_size: int = 50) -> List[int]:
    """
    Find vertical positions where there are gaps in content.
    Returns a list of y-coordinates where gaps occur.
    """
    # Convert to grayscale for analysis
    gray = image.convert('L')
    width, height = gray.size

    # Get image data
    pixels = list(gray.getdata())

    # Check each row for content
    gaps = []
    current_gap_start = None

    for y in range(height):
        row_start = y * width
        row_end = row_start + width
        row = pixels[row_start:row_end]

        # Check if row is empty (all white or nearly white pixels)
        is_empty = all(p > 250 for p in row)

        if is_empty and current_gap_start is None:
            current_gap_start = y
        elif not is_empty and current_gap_start is not None:
            gap_size = y - current_gap_start
            if gap_size >= min_gap_size:
                gaps.append(current_gap_start + gap_size // 2)  # Add middle of gap
            current_gap_start = None

    return gaps

def calculate_slices(image_height: int, page_height: int, content_gaps: List[int]) -> List[Tuple[int, int]]:
    """
    Calculate optimal slice positions based on page height and content gaps.
    Returns list of (start_y, end_y) tuples.
    """
    slices = []
    current_pos = 0

    while current_pos < image_height:
        # Calculate ideal next slice position
        ideal_next_pos = min(current_pos + page_height, image_height)

        # If we're at the end, add the final slice
        if ideal_next_pos >= image_height:
            slices.append((current_pos, image_height))
            break

        # Find nearest content gap
        nearest_gap = None
        min_distance = page_height // 4  # Don't look for gaps too far from ideal position

        for gap in content_gaps:
            if gap > current_pos and gap < ideal_next_pos:
                distance = abs(gap - ideal_next_pos)
                if distance < min_distance:
                    nearest_gap = gap
                    min_distance = distance

        # Use gap position if found, otherwise use ideal position
        next_pos = nearest_gap if nearest_gap is not None else ideal_next_pos
        slices.append((current_pos, next_pos))
        current_pos = next_pos

    return slices

def create_pdf(image: Image.Image, output_path: str, page_size: Tuple[float, float],
               margin_pixels: int, min_gap_size: int = 50) -> None:
    """Create PDF from image, splitting it into pages."""
    page_width, page_height = page_size
    usable_width = page_width - 2 * margin_pixels
    usable_height = page_height - 2 * margin_pixels

    # Calculate scale factor to fit width while preserving aspect ratio
    scale_factor = usable_width / image.size[0]

    # Find content gaps in original image (no scaling)
    content_gaps = find_content_gaps(image, min_gap_size)

    # Calculate slice positions using scaled height
    scaled_usable_height = int(usable_height / scale_factor)  # Convert page height to original image scale
    slices = calculate_slices(image.size[1], scaled_usable_height, content_gaps)

    # Create PDF
    c = canvas.Canvas(output_path, pagesize=page_size)

    for i, (start_y, end_y) in enumerate(slices):
        # Create temporary image for this slice
        slice_height = end_y - start_y
        slice_img = image.crop((0, start_y, image.size[0], end_y))

        # Save temporary slice
        temp_slice_path = f'temp_slice_{i}.png'
        slice_img.save(temp_slice_path)

        # Add to PDF with margins, scaling both dimensions
        scaled_width = image.size[0] * scale_factor
        scaled_slice_height = slice_height * scale_factor
        c.drawImage(temp_slice_path,
                   margin_pixels,
                   page_height - scaled_slice_height - margin_pixels,
                   width=scaled_width,
                   height=scaled_slice_height)

        # Remove temporary file
        os.remove(temp_slice_path)

        # Add new page if not last slice
        if i < len(slices) - 1:
            c.showPage()

    c.save()

def main():
    parser = argparse.ArgumentParser(description='Convert tall image to multi-page PDF')
    parser.add_argument('input_file', help='Input image file')
    parser.add_argument('--output', '-o', help='Output PDF file (default: input_name.pdf)')
    parser.add_argument('--page-size', '-p', choices=PAGE_SIZES.keys(),
                       default='a4', help='Page size (default: a4)')
    parser.add_argument('--margin', '-m', default='20mm',
                       help='Margin size in px or mm (default: 20mm)')
    parser.add_argument('--min-gap', '-g', type=int, default=50,
                       help='Minimum gap size in pixels to consider for page breaks (default: 50)')

    args = parser.parse_args()

    # Set output filename if not specified
    if not args.output:
        base_name = os.path.splitext(args.input_file)[0]
        args.output = f'{base_name}.pdf'

    # Convert margin to pixels
    margin_pixels = parse_margin(args.margin)

    try:
        # Open and trim image
        with Image.open(args.input_file) as img:
            trimmed_img = trim_whitespace(img)

            # Create PDF
            create_pdf(trimmed_img, args.output, PAGE_SIZES[args.page_size],
                      margin_pixels, args.min_gap)

        print(f"Successfully created PDF: {args.output}")

    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
