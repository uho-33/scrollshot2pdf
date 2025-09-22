import argparse
import os
import sys

from PIL import Image
from reportlab.lib import pagesizes
from reportlab.pdfgen import canvas

# Try to import pytesseract but make it optional
try:
    import pytesseract

    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

# Get all paper sizes from reportlab
PAGE_SIZES = {
    name.lower(): getattr(pagesizes, name)
    for name in dir(pagesizes)
    if name.isupper() and isinstance(getattr(pagesizes, name), tuple)
}

# Add landscape variants
PAGE_SIZES.update({f"{name}-landscape": (height, width) for name, (width, height) in PAGE_SIZES.items()})


def mm_to_pixels(mm: float, dpi: int = 72) -> int:
    """Convert millimeters to pixels at given DPI."""
    return int(mm * dpi / 25.4)


def mm_to_points(mm: float) -> float:
    """Convert millimeters to points (1/72 inch)."""
    return mm * 72 / 25.4  # 1 inch = 25.4mm, 1 inch = 72 points


def parse_margin(margin_str: str) -> float:
    """Parse margin string (either pixels or mm) to points."""
    if margin_str.endswith("mm"):
        return mm_to_points(float(margin_str[:-2]))
    elif margin_str.endswith("px"):
        return float(margin_str[:-2]) * 72 / 96  # Assuming 96 DPI for pixels
    else:
        try:
            return float(margin_str) * 72 / 96  # Treat bare numbers as pixels
        except ValueError as err:
            raise ValueError("Margin must be specified in px, mm, or as plain pixels") from err


def trim_whitespace(image: Image.Image) -> Image.Image:
    """Trim whitespace from image edges."""
    # Convert to RGB if image is in RGBA mode
    if image.mode == "RGBA":
        background = Image.new("RGBA", image.size, (255, 255, 255, 255))
        background.paste(image, mask=image.split()[3])  # Use alpha channel as mask
        image = background.convert("RGB")
    elif image.mode != "RGB":
        image = image.convert("RGB")

    # Get the bounding box of non-white pixels
    bbox = image.getbbox()
    if bbox:
        return image.crop(bbox)
    return image


def find_content_gaps(image: Image.Image, min_gap_size: int = 50, blank_ratio: float = 0.0) -> list[int]:
    """
    Find vertical positions where there are gaps in content.
    Returns a list of y-coordinates where gaps occur.
    
    Args:
        image: Image to analyze
        min_gap_size: Minimum gap size in pixels to consider for page breaks
        blank_ratio: Ratio of non-blank to total pixels allowed in blank lines 
                    (0.0=strict, 0.1=10% non-blank allowed)
    """
    # Convert to grayscale for analysis
    gray = image.convert("L")
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

        # Check if row is empty based on blank_ratio
        if blank_ratio == 0.0:
            # Strict mode: all pixels must be > 250 (nearly white)
            is_empty = all(p > 250 for p in row)
        else:
            # Ratio mode: allow some non-blank pixels
            non_blank_pixels = sum(1 for p in row if p <= 250)
            non_blank_ratio = non_blank_pixels / len(row)
            is_empty = non_blank_ratio <= blank_ratio

        if is_empty and current_gap_start is None:
            current_gap_start = y
        elif not is_empty and current_gap_start is not None:
            gap_size = y - current_gap_start
            if gap_size >= min_gap_size:
                gaps.append(current_gap_start + gap_size // 2)  # Add middle of gap
            current_gap_start = None

    return gaps


def calculate_slices(
    image_height: int, page_height: int, content_gaps: list[int], no_split_content: bool = False
) -> list[tuple[int, int]]:
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

        # Find the last content gap before the ideal split point.
        best_gap = None
        for gap in content_gaps:
            if current_pos < gap < ideal_next_pos:
                best_gap = gap

        min_distance = page_height // 4  # Don't look for gaps too far from ideal position when split in content is allowed.
        if not no_split_content:
            if best_gap is None:
                best_gap = ideal_next_pos
            else:
                distance = abs(best_gap - ideal_next_pos)
                if distance > min_distance:
                    best_gap = ideal_next_pos
        
        if best_gap is None: # No gap found between current and ideal position, and split in content is not allowed.
            print(
                "Error: A content block is too tall to fit on a single page, and --no-split-content is enabled.",
                file=sys.stderr,
            )
            print("To resolve this, you can:", file=sys.stderr)
            print(
                "  1. Remove the --no-split-content flag to allow the content to be split across pages.",
                file=sys.stderr,
            )
            print(
                "  2. Increase the page height by selecting a larger --page-size (e.g., 'legal' or 'a3-landscape').",
                file=sys.stderr,
            )
            print(
                "  3. If your image has small whitespace breaks, try a smaller --min-gap value to detect them as split points.",
                file=sys.stderr,
            )
            print(
                "  4. If your image's blank areas have noise, try --blank-ratio to allow for imperfectly blank lines.",
                file=sys.stderr,
            )
            sys.exit(1)

                
        next_pos = best_gap

        slices.append((current_pos, next_pos))
        current_pos = next_pos

    return slices


def title_from_filename(filename: str) -> str:
    """Convert filename to title, without extension and titlecased if all lowercase."""
    # Remove extension and directory path
    base = os.path.splitext(os.path.basename(filename))[0]
    # Only titlecase if the string is all lowercase
    if base.islower():
        return base.replace("_", " ").replace("-", " ").title()
    return base.replace("_", " ").replace("-", " ")


def parse_page_range(range_str: str, total_pages: int) -> tuple[int, int]:
    """Parse page range string into start and end page numbers (1-based)."""
    if not range_str:
        return 1, total_pages

    try:
        if "-" in range_str:
            start_str, end_str = range_str.split("-", 1)
            start = int(start_str) if start_str else 1
            end = int(end_str) if end_str else total_pages
        else:
            start = end = int(range_str)

        # Validate range
        if start < 1 or end > total_pages or start > end:
            raise ValueError

        return start, end

    except ValueError as err:
        raise ValueError(f"Invalid page range. Format: N, N-M, N-, -M (1 to {total_pages})") from err


def calculate_optimal_columns(image_width: float, usable_width: float, image: Image.Image, debug: bool = False) -> int:
    """
    Calculate optimal number of columns to minimize scaling while fitting page width.
    Accounts for DPI differences between image and PDF output.
    """
    # Get image DPI from metadata, default to 72 if not specified
    try:
        image_dpi = image.info.get("dpi", (72, 72))[0]  # Get horizontal DPI
    except (AttributeError, TypeError):
        image_dpi = 72

    output_dpi = 300  # PDF target DPI

    # Convert image width to points at output DPI
    image_width_at_output_dpi = (image_width * 72) / image_dpi  # Convert to points

    if debug:
        print("\nColumn calculation:")
        print(f"Image width: {image_width:.1f}px")
        print(f"Image DPI: {image_dpi}")
        print(f"Image width at {output_dpi} DPI: {image_width_at_output_dpi:.1f}pt")
        print(f"Usable page width: {usable_width:.1f}pt")

    # Start with 1 column and increase until we find a solution
    for columns in range(1, 11):  # Limit to 10 columns max
        # Calculate column width with gaps
        total_gap_width = 20.0 * (columns - 1)  # Using default column gap
        column_width = (usable_width - total_gap_width) / columns

        # Calculate scale factor based on output DPI
        scale_factor = column_width / image_width_at_output_dpi
        inverse_scale = 1 / scale_factor

        if debug:
            print(f"\nTrying {columns} column{'s' if columns > 1 else ''}:")
            print(f"  Column width: {column_width:.1f}pt")
            print(f"  Scale factor: {scale_factor:.3f} (1/{inverse_scale:.1f})")

        # If scale factor is >= 1, we can use 1 column
        if scale_factor >= 1:
            if debug:
                print("  ✓ Image fits at original size")
            return 1

        # If inverse of scale factor is close to an integer, we found our solution
        if abs(round(inverse_scale) - inverse_scale) < 0.01:
            if debug:
                print(f"  ✓ Clean scaling factor found: 1/{round(inverse_scale)}")
            return columns
        elif debug:
            print("  ✗ No clean scaling factor")

    # If no good solution found, default to minimum scaling
    if debug:
        print("\nNo optimal solution found, defaulting to 1 column")
    return 1


def add_ocr_layer(
    image: Image.Image,
    canvas_obj: canvas.Canvas,
    x: float,
    y: float,
    width: float,
    height: float,
    lang: str = "eng+jpn",
) -> None:
    """Add searchable text layer using OCR while preserving original image."""
    # Configure OCR parameters for better mixed-language detection
    custom_config = r"--oem 3 --psm 3"  # Use LSTM OCR Engine Mode and Auto-page segmentation

    # Get OCR data with bounding boxes
    data = pytesseract.image_to_data(image, lang=lang, config=custom_config, output_type=pytesseract.Output.DICT)

    # Save canvas state
    canvas_obj.saveState()

    # Set text color to transparent
    canvas_obj.setFillColorRGB(0, 0, 0, 0)

    # Calculate scale factors
    scale_x = width / image.size[0]
    scale_y = height / image.size[1]

    # Group text by block_num to maintain text flow
    blocks = {}
    for i in range(len(data["text"])):
        if data["conf"][i] > 0:  # Only process text with confidence
            block_num = data["block_num"][i]
            if block_num not in blocks:
                blocks[block_num] = []
            blocks[block_num].append(i)

    # Process each block
    for block_indices in blocks.values():
        for i in block_indices:
            text = data["text"][i]
            if not text.strip():
                continue

            # Get text dimensions and position
            left = data["left"][i]
            top = data["top"][i]
            height_text = data["height"][i]

            # Convert coordinates to PDF space
            box_x = x + (left * scale_x)
            # Adjust y position to align with text baseline
            baseline_offset = height_text * 0.2
            box_y = y + height - ((top + height_text - baseline_offset) * scale_y)

            # Set font size based on the OCR'd text height
            font_size = height_text * scale_y
            canvas_obj.setFont("Helvetica", font_size)

            # Add invisible text
            canvas_obj.drawString(box_x, box_y, text)

    # Restore state
    canvas_obj.restoreState()

    # Note: We don't draw the image here anymore, as it's handled by the calling function


def create_pdf(
    image: Image.Image,
    output_path: str,
    page_size: tuple[float, float],
    margin_points: float,
    min_gap_size: int = 50,
    *,
    blank_ratio: float = 0.0,
    columns: int | None = None,
    column_gap: float = 20.0,
    add_page_numbers: bool = True,
    number_position: str = "bottom-left",
    number_font: str = "Helvetica",
    number_size: int = 10,
    skip_first_number: bool = True,
    title: str | None = None,
    title_position: str = "center",
    title_font: str = "Helvetica-Bold",
    title_size: int = 14,
    page_range: str | None = None,
    enable_ocr: bool = False,
    ocr_lang: str = "eng",
    debug: bool = False,
    no_split_content: bool = False,
) -> None:
    """Create PDF from image with optional OCR layer."""

    # Check if tesseract executable is available when OCR is enabled
    if enable_ocr and not TESSERACT_AVAILABLE:
        print(
            "Error: OCR was requested but pytesseract is not installed.",
            file=sys.stderr,
        )
        print("To use OCR, install scrollshot2pdf with OCR support:", file=sys.stderr)
        print(
            '  pip install "git+https://github.com/osteele/scrollshot2pdf.git[ocr]"',
            file=sys.stderr,
        )
        sys.exit(1)

    # Check if tesseract executable is available when OCR is enabled
    if enable_ocr:
        try:
            pytesseract.get_tesseract_version()
        except pytesseract.TesseractNotFoundError:
            print(
                "Error: Tesseract is not installed. Please install tesseract-ocr first:",
                file=sys.stderr,
            )
            print("Ubuntu/Debian: sudo apt-get install tesseract-ocr", file=sys.stderr)
            print("macOS: brew install tesseract", file=sys.stderr)
            sys.exit(1)

    print("Analyzing image dimensions and calculating layout...")
    page_width, page_height = page_size
    usable_width = page_width - 2 * margin_points
    usable_height = page_height - 2 * margin_points

    # Calculate optimal columns if not specified
    if columns is None:
        columns = calculate_optimal_columns(image.size[0], usable_width, image, debug)
        print(f"Automatically selected {columns} column{'s' if columns > 1 else ''}")

    # Calculate column width
    total_gap_width = column_gap * (columns - 1)
    column_width = (usable_width - total_gap_width) / columns

    # Calculate scale factor to fit column width while preserving aspect ratio
    scale_factor = column_width / image.size[0]

    # Find content gaps in original image (no scaling)
    print("Finding content gaps for optimal page breaks...")
    content_gaps = find_content_gaps(image, min_gap_size, blank_ratio)

    # Calculate slice positions using scaled height
    scaled_usable_height = int(usable_height / scale_factor)
    slices = calculate_slices(image.size[1], scaled_usable_height, content_gaps, no_split_content)

    # Calculate total pages needed based on columns
    total_slices = len(slices)
    total_pages = (total_slices + columns - 1) // columns  # Ceiling division
    print(f"Image will be split into {total_slices} slices across {total_pages} pages")

    # Parse page range
    if page_range:
        try:
            start_page, end_page = parse_page_range(page_range, total_pages)
        except ValueError as e:
            print(f"Error: {e!s}", file=sys.stderr)
            sys.exit(1)

        # Filter slices based on page range
        start_slice = (start_page - 1) * columns
        end_slice = min(end_page * columns, total_slices)
        slices = slices[start_slice:end_slice]

    def add_page_number(canvas, page_num):
        if skip_first_number and page_num == 1:
            return

        # Calculate position based on margins and position choice
        if "bottom" in number_position:
            y = margin_points + number_size / 2
        else:  # top
            y = page_height - margin_points - number_size / 2

        if "left" in number_position:
            x = margin_points
        else:  # right
            x = page_width - margin_points
            canvas.setRightMargin(margin_points)

        canvas.setFont(number_font, number_size)
        text = str(page_num)
        if "right" in number_position:
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
        if title_position == "left":
            x = margin_points
        elif title_position == "right":
            x = page_width - margin_points - text_width
        else:  # center
            x = (page_width - text_width) / 2

        canvas.drawString(x, y, title)

    # Create PDF
    print(f"Creating PDF: {output_path}")
    c = canvas.Canvas(output_path, pagesize=page_size)

    # Add title to first page only
    add_title(c)

    current_page = 1
    for i in range(0, len(slices), columns):
        print(f"Processing page {current_page}/{total_pages}...")

        # Process each column in the current page
        for col in range(columns):
            if i + col >= len(slices):
                break

            start_y, end_y = slices[i + col]
            slice_height = end_y - start_y
            scaled_slice_height = slice_height * scale_factor

            slice_img = image.crop((0, start_y, image.size[0], end_y))

            # Save temporary slice
            temp_slice_path = f"temp_slice_{i + col}.png"
            slice_img.save(temp_slice_path)

            # Calculate position for this column
            x_pos = margin_points + (column_width + column_gap) * col

            if enable_ocr:
                # Add OCR layer before drawing image
                add_ocr_layer(
                    slice_img,
                    c,
                    x_pos,
                    page_height - scaled_slice_height - margin_points,
                    column_width,
                    scaled_slice_height,
                    lang=ocr_lang,
                )

            # Draw the image (OCR layer will be underneath)
            c.drawImage(
                temp_slice_path,
                x_pos,
                page_height - scaled_slice_height - margin_points,
                width=column_width,
                height=scaled_slice_height,
            )

            # Remove temporary file
            os.remove(temp_slice_path)

        # Add page number if enabled
        if add_page_numbers:
            add_page_number(c, current_page)

        # Add new page if not last page
        if i + columns < len(slices):
            c.showPage()
            current_page += 1

    c.save()
    print("PDF creation complete!")


def main():
    parser = argparse.ArgumentParser(description="Convert tall image to multi-page PDF")
    parser.add_argument("input_file", help="Input image file")
    parser.add_argument("--output", "-o", help="Output PDF file (default: input_name.pdf)")
    parser.add_argument(
        "--page-size",
        "-p",
        choices=sorted(PAGE_SIZES.keys()),
        default="a4",
        help="Page size (default: a4)",
    )
    parser.add_argument("--margin", "-m", default="10mm", help="Margin size in px or mm (default: 10mm)")
    parser.add_argument(
        "--min-gap",
        "-g",
        type=int,
        default=50,
        help="Minimum gap size in pixels to consider for page breaks (default: 50)",
    )
    parser.add_argument(
        "--blank-ratio",
        "-b",
        type=float,
        default=0.0,
        help="Ratio of non-blank to blank pixels allowed in blank lines (0.0=strict, 0.1=10%% non-blank allowed, default: 0.0)",
    )
    parser.add_argument(
        "--no-split-content",
        action="store_true",
        help="Prevents content blocks from being split. Will error if a block is too tall to fit on a single page.",
    )

    # Add page numbering arguments
    parser.add_argument(
        "--page-numbers",
        action="store_true",
        default=True,
        help="Add page numbers (default)",
    )
    parser.add_argument(
        "--no-page-numbers",
        action="store_false",
        dest="page_numbers",
        help="Disable page numbers",
    )
    parser.add_argument(
        "--number-position",
        choices=["bottom-left", "bottom-right", "top-left", "top-right"],
        default="bottom-left",
        help="Position of page numbers",
    )
    parser.add_argument("--number-font", default="Helvetica", help="Font for page numbers")
    parser.add_argument(
        "--number-size",
        type=int,
        default=10,
        help="Font size for page numbers in points",
    )
    parser.add_argument(
        "--skip-first-number",
        action="store_true",
        default=True,
        help="Skip page number on first page",
    )

    # Add title arguments
    parser.add_argument(
        "--title",
        help='Add title to first page. Use "from-filename" to use input filename',
    )
    parser.add_argument(
        "--title-position",
        choices=["left", "center", "right"],
        default="center",
        help="Position of title",
    )
    parser.add_argument("--title-font", default="Helvetica-Bold", help="Font for title")
    parser.add_argument("--title-size", type=int, default=14, help="Font size for title in points")

    # Add page range option
    parser.add_argument("--page-range", help="Page range to output (e.g., 5, 5-10)")

    # Add column arguments
    parser.add_argument(
        "--columns",
        "-c",
        type=int,
        help="Number of columns per page (default: auto-calculated)",
    )
    parser.add_argument(
        "--column-gap",
        type=float,
        default=20.0,
        help="Gap between columns in points (default: 20.0)",
    )

    # Add debug flag
    parser.add_argument("--debug", action="store_true", help="Show detailed debug information")

    # Add OCR arguments
    parser.add_argument("--ocr", action="store_true", help="Enable OCR text layer (requires tesseract)")
    parser.add_argument("--ocr-lang", default="eng", help="OCR language (default: eng)")
    parser.add_argument("--no-ocr", action="store_false", dest="ocr", help="Disable OCR (default)")

    args = parser.parse_args()

    # Set output filename if not specified
    if not args.output:
        base_name = os.path.splitext(args.input_file)[0]
        args.output = f"{base_name}.pdf"

    # Convert margin to pixels
    margin_points = parse_margin(args.margin)

    # Process title if specified
    title: str | None = None
    if args.title:
        title = title_from_filename(args.input_file) if args.title == "from-filename" else args.title

    try:
        print(f"Opening image: {args.input_file}")
        # Open and trim image
        with Image.open(args.input_file) as img:
            print("Trimming whitespace from image edges...")
            trimmed_img = trim_whitespace(img)

            # Create PDF
            create_pdf(
                trimmed_img,
                args.output,
                PAGE_SIZES[args.page_size.lower()],
                margin_points,
                args.min_gap,
                blank_ratio=args.blank_ratio,
                columns=args.columns,
                column_gap=args.column_gap,
                add_page_numbers=args.page_numbers,
                number_position=args.number_position,
                number_font=args.number_font,
                number_size=args.number_size,
                skip_first_number=args.skip_first_number,
                title=title,
                title_position=args.title_position,
                title_font=args.title_font,
                title_size=args.title_size,
                page_range=args.page_range,
                enable_ocr=args.ocr,
                ocr_lang=args.ocr_lang,
                debug=args.debug,
                no_split_content=args.no_split_content,
            )

        print(f"Successfully created PDF: {args.output}")

    except Exception as e:
        print(f"Error: {e!s}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
