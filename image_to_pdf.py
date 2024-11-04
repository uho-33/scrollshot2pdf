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
from reportlab.lib import pagesizes
import os
import sys
from typing import Tuple, List

# Get all paper sizes from reportlab
PAGE_SIZES = {name.lower(): getattr(pagesizes, name)
              for name in dir(pagesizes)
              if name.isupper() and isinstance(getattr(pagesizes, name), tuple)}

# Add landscape variants
PAGE_SIZES.update({
    f'{name}-landscape': (height, width)
    for name, (width, height) in PAGE_SIZES.items()
})

def mm_to_pixels(mm: float, dpi: int = 72) -> int:
    """Convert millimeters to pixels at given DPI."""
    return int(mm * dpi / 25.4)

def mm_to_points(mm: float) -> float:
    """Convert millimeters to points (1/72 inch)."""
    return mm * 72 / 25.4  # 1 inch = 25.4mm, 1 inch = 72 points

def parse_margin(margin_str: str) -> float:
    """Parse margin string (either pixels or mm) to points."""
    if margin_str.endswith('mm'):
        return mm_to_points(float(margin_str[:-2]))
    elif margin_str.endswith('px'):
        return float(margin_str[:-2]) * 72 / 96  # Assuming 96 DPI for pixels
    else:
        try:
            return float(margin_str) * 72 / 96  # Treat bare numbers as pixels
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

def title_from_filename(filename: str) -> str:
    """Convert filename to title, without extension and titlecased if all lowercase."""
    # Remove extension and directory path
    base = os.path.splitext(os.path.basename(filename))[0]
    # Only titlecase if the string is all lowercase
    if base.islower():
        return base.replace('_', ' ').replace('-', ' ').title()
    return base.replace('_', ' ').replace('-', ' ')

def parse_page_range(range_str: str, total_pages: int) -> Tuple[int, int]:
    """Parse page range string into start and end page numbers (1-based)."""
    if not range_str:
        return 1, total_pages

    try:
        if '-' in range_str:
            start_str, end_str = range_str.split('-', 1)
            start = int(start_str) if start_str else 1
            end = int(end_str) if end_str else total_pages
        else:
            start = end = int(range_str)

        # Validate range
        if start < 1 or end > total_pages or start > end:
            raise ValueError

        return start, end

    except ValueError:
        raise ValueError(f"Invalid page range. Format: N, N-M, N-, -M (1 to {total_pages})")

def create_pdf(image: Image.Image, output_path: str, page_size: Tuple[float, float],
               margin_points: float, min_gap_size: int = 50, *,
               add_page_numbers: bool = True,
               number_position: str = 'bottom-left',
               number_font: str = 'Helvetica',
               number_size: int = 10,
               skip_first_number: bool = True,
               title: str = None,
               title_position: str = 'center',
               title_font: str = 'Helvetica-Bold',
               title_size: int = 14,
               page_range: str = None) -> None:
    """Create PDF from image, splitting it into pages."""
    print("Analyzing image dimensions and calculating layout...")
    page_width, page_height = page_size
    usable_width = page_width - 2 * margin_points
    usable_height = page_height - 2 * margin_points

    # Calculate scale factor to fit width while preserving aspect ratio
    scale_factor = usable_width / image.size[0]

    # Find content gaps in original image (no scaling)
    print("Finding content gaps for optimal page breaks...")
    content_gaps = find_content_gaps(image, min_gap_size)

    # Calculate slice positions using scaled height
    scaled_usable_height = int(usable_height / scale_factor)  # Convert page height to original image scale
    slices = calculate_slices(image.size[1], scaled_usable_height, content_gaps)
    total_pages = len(slices)
    print(f"Image will be split into {total_pages} pages")

    # Parse page range
    try:
        start_page, end_page = parse_page_range(page_range, total_pages)
    except ValueError as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

    # Filter slices based on page range
    slices = slices[start_page-1:end_page]
    print(f"Processing pages {start_page} to {end_page} of {total_pages}")

    def add_page_number(canvas, page_num):
        if skip_first_number and page_num == 1:
            return

        # Calculate position based on margins and position choice
        if 'bottom' in number_position:
            y = margin_points + number_size/2
        else:  # top
            y = page_height - margin_points - number_size/2

        if 'left' in number_position:
            x = margin_points
        else:  # right
            x = page_width - margin_points
            canvas.setRightMargin(margin_points)

        canvas.setFont(number_font, number_size)
        text = str(page_num)
        if 'right' in number_position:
            text_width = canvas.stringWidth(text, number_font, number_size)
            x -= text_width
        canvas.drawString(x, y, text)

    def add_title(canvas):
        if not title:
            return

        canvas.setFont(title_font, title_size)
        text_width = canvas.stringWidth(title, title_font, title_size)

        # Calculate y position (at top of page)
        y = page_height - margin_points - title_size

        # Calculate x position based on alignment
        if title_position == 'left':
            x = margin_points
        elif title_position == 'right':
            x = page_width - margin_points - text_width
        else:  # center
            x = (page_width - text_width) / 2

        canvas.drawString(x, y, title)

    # Create PDF
    print(f"Creating PDF: {output_path}")
    c = canvas.Canvas(output_path, pagesize=page_size)

    # Add title to first page only
    add_title(c)

    for i, (start_y, end_y) in enumerate(slices, 1):
        print(f"Processing page {i}/{total_pages}...")

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
                   margin_points,
                   page_height - scaled_slice_height - margin_points,
                   width=scaled_width,
                   height=scaled_slice_height)

        # Remove temporary file
        os.remove(temp_slice_path)

        # Add page number if enabled
        if add_page_numbers:
            add_page_number(c, i)

        # Add new page if not last slice
        if i < total_pages:
            c.showPage()

    c.save()
    print("PDF creation complete!")

def main():
    parser = argparse.ArgumentParser(description='Convert tall image to multi-page PDF')
    parser.add_argument('input_file', help='Input image file')
    parser.add_argument('--output', '-o', help='Output PDF file (default: input_name.pdf)')
    parser.add_argument('--page-size', '-p', choices=sorted(PAGE_SIZES.keys()),
                       default='a4', help='Page size (default: a4)')
    parser.add_argument('--margin', '-m', default='10mm',
                       help='Margin size in px or mm (default: 10mm)')
    parser.add_argument('--min-gap', '-g', type=int, default=50,
                       help='Minimum gap size in pixels to consider for page breaks (default: 50)')

    # Add page numbering arguments
    parser.add_argument('--page-numbers', action='store_true', default=True,
                       help='Add page numbers (default)')
    parser.add_argument('--no-page-numbers', action='store_false', dest='page_numbers',
                       help='Disable page numbers')
    parser.add_argument('--number-position', choices=['bottom-left', 'bottom-right',
                                                    'top-left', 'top-right'],
                       default='bottom-left', help='Position of page numbers')
    parser.add_argument('--number-font', default='Helvetica',
                       help='Font for page numbers')
    parser.add_argument('--number-size', type=int, default=10,
                       help='Font size for page numbers in points')
    parser.add_argument('--skip-first-number', action='store_true', default=True,
                       help='Skip page number on first page')

    # Add title arguments
    parser.add_argument('--title',
                       help='Add title to first page. Use "from-filename" to use input filename')
    parser.add_argument('--title-position', choices=['left', 'center', 'right'],
                       default='center', help='Position of title')
    parser.add_argument('--title-font', default='Helvetica-Bold',
                       help='Font for title')
    parser.add_argument('--title-size', type=int, default=14,
                       help='Font size for title in points')

    # Add page range option
    parser.add_argument('--page-range',
                       help='Page range to output (e.g., 5, 5-10)')

    args = parser.parse_args()

    # Set output filename if not specified
    if not args.output:
        base_name = os.path.splitext(args.input_file)[0]
        args.output = f'{base_name}.pdf'

    # Convert margin to pixels
    margin_points = parse_margin(args.margin)

    # Process title if specified
    title = None
    if args.title:
        if args.title == 'from-filename':
            title = title_from_filename(args.input_file)
        else:
            title = args.title

    try:
        print(f"Opening image: {args.input_file}")
        # Open and trim image
        with Image.open(args.input_file) as img:
            print("Trimming whitespace from image edges...")
            trimmed_img = trim_whitespace(img)

            # Create PDF
            create_pdf(trimmed_img, args.output, PAGE_SIZES[args.page_size.lower()],
                      margin_points, args.min_gap,
                      add_page_numbers=args.page_numbers,
                      number_position=args.number_position,
                      number_font=args.number_font,
                      number_size=args.number_size,
                      skip_first_number=args.skip_first_number,
                      title=title,
                      title_position=args.title_position,
                      title_font=args.title_font,
                      title_size=args.title_size,
                      page_range=args.page_range)

        print(f"Successfully created PDF: {args.output}")

    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
