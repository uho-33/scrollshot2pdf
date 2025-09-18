# scrollshot2pdf

A command-line to convert tall screenshots and images into multi-page PDFs.
Intelligently splits the image across pages by detecting content gaps, avoiding
awkward breaks in the middle of content.

## What is a Scrollshot?

A scrollshot (also called a scrolling screenshot or full-page screenshot) captures an entire scrollable area - like a long webpage, chat conversation, or social media feed - into a single tall image. While normal screenshots only capture what's visible on screen, scrollshots stitch together multiple screens worth of content.

### Common Uses

- Capturing entire web articles or documentation
- Preserving full chat/message histories
- Recording social media threads or discussions
- Documenting long forms or user interfaces
- Archiving entire product pages or listings

### Creating Scrollshots

Third-party capture apps record a scrolling screen element into a tall image.
Third-party stitching apps combine a series of overlapped screenshots, or a
video capture of the screen, into a single scrollshot. These are my favorites:

**Capture Apps:**
- CleanShot X (macOS)

**Stitching Apps:***
- PicSew (iOS)
- Tailor (iOS)

### When to Use scrollshot2pdf

This tool is particularly useful when you need to:
- Convert long scrollshots into a printable format
- Break up tall images into properly paginated documents
- Create multi-column layouts from single-column content
- Add page numbers and titles to scrollshot content
- Share scrollshots in a standardized document format
- Archive long-form content in a print-friendly way

### When Not to Use scrollshot2pdf

Consider using direct PDF export when available. A natively-generated PDF is usually superior to a converted scrollshot because it:

- Preserves searchable and copyable text (vs. image-only content requiring OCR)
- Maintains proper document structure and accessibility
- Includes proper pagination, headers, and footers
- Preserves the original design intent and formatting
- Often produces smaller file sizes

Use scrollshot2pdf as a fallback solution when:
- The app/site doesn't offer PDF export
- The PDF export is missing visible content
- The print/export layout differs significantly from the screen view
- You need to preserve exact visual fidelity of what you see on screen

## Features

- Intelligent page breaks at natural content gaps
- Configurable page size and margins
- Multi-column layout support
- Page numbers with customizable position and style
- Title page support
- Whitespace trimming
- Selective page range output
- Optional OCR text layer for searchable PDFs

## Installation

In the terminal, enter one of these:

```bash
# Install using pip
pip install git+https://github.com/osteele/scrollshot2pdf.git
```

```bash
# Install using uv
uv tool install git+https://github.com/osteele/scrollshot2pdf.git
```

## Usage

Basic usage:
```bash
scrollshot2pdf input_image.png
```

With options:
```bash
scrollshot2pdf input_image.png -o output.pdf --page-size a4 --margin 25mm --min-gap 100
```

With customized page numbers:
```bash
scrollshot2pdf input.png --page-numbers --number-position top-right --number-size 12 --number-font "Times-Roman" --skip-first false
```

With page range selection:
```bash
scrollshot2pdf input.png --page-range 5 --page-numbers --number-position top-right --number-size 12 --number-font "Times-Roman" --skip-first false
```

With columns:
```bash
scrollshot2pdf input.png --columns 2 --column-gap 30
```

Advanced options:
```bash
scrollshot2pdf input.png \
--output output.pdf \
--page-size a4 \
--margin 20mm \
--columns 2 \
--column-gap 25 \
--min-gap 50 \
--title "My Document" \
--page-numbers \
--number-position bottom-right
```


## Options

### Layout Options
- `--page-size`, `-p`: Page size (default: a4)
- `--margin`, `-m`: Margin size in px or mm (default: 10mm)
- `--columns`, `-c`: Number of columns per page (default: 1)
- `--column-gap`: Gap between columns in points (default: 20.0)
- `--min-gap`, `-g`: Minimum gap size in pixels for page breaks (default: 50)
- `--blank-ratio`, `-b`: Ratio of non-blank to blank pixels allowed in blank lines (default: 0.0)
- `--no-split-content`: Prevents content blocks from being split across pages. Will error if a block is too tall for one page.

### Page Numbers
- `--page-numbers`: Add page numbers (default: enabled)
- `--no-page-numbers`: Disable page numbers
- `--number-position`: Position of page numbers (bottom-left, bottom-right, top-left, top-right)
- `--number-font`: Font for page numbers
- `--number-size`: Font size for page numbers
- `--skip-first-number`: Skip page number on first page (default: enabled)

### Title Options
- `--title`: Add title to first page (use "from-filename" to use input filename)
- `--title-position`: Position of title (left, center, right)
- `--title-font`: Font for title
- `--title-size`: Font size for title

### Other Options
- `--page-range`: Output specific pages (e.g., "1-5" or "3")
- `--output`, `-o`: Output PDF file name (default: input_name.pdf)

### OCR Options
- `--ocr`: Enable OCR text layer (requires tesseract)
- `--ocr-lang`: OCR language (default: eng)
- `--no-ocr`: Disable OCR (default)

The OCR feature makes your PDFs searchable by adding an invisible text layer over the image. This is the only feature that requires the Tesseract library. Without OCR, the PDFs will still be created, but text won't be searchable.

OCR uses the Tesseract library and supports multiple languages including non-Latin scripts when appropriate language packs are installed.

To use OCR features, install with OCR support:

```bash
# Install with OCR support using pip
pip install "git+https://github.com/osteele/scrollshot2pdf.git[ocr]"

# Or with uv tool
uv tool install --with ocr git+https://github.com/osteele/scrollshot2pdf.git

# Or add OCR dependency separately
pip install pytesseract
```

On Ubuntu/Debian:

```bash
sudo apt-get install tesseract-ocr
```

On macOS:

```bash
brew install tesseract
```


## Examples

Two-column layout with custom gap:

### Page Sizes

All standard paper sizes from ReportLab are supported, including:
- ISO A series (A0-A6)
- ISO B series (B0-B6)
- North American sizes (Letter, Legal, Tabloid, etc.)

Each size is also available in landscape orientation by adding "-landscape" to the name. For example:
- a4
- a4-landscape
- letter
- letter-landscape

Run `scrollshot2pdf --help` to see the complete list of available page sizes.

### Margin Format

Margins can be specified in:
- Millimeters: e.g., "20mm"
- Pixels: e.g., "50px" or just "50"

## How It Works

1. The script first trims any whitespace borders from the input image
2. It scales the image to fit the page width while maintaining aspect ratio
3. It analyzes the image to find vertical gaps in content using configurable blank line detection
4. It calculates optimal slice positions based on page height and content gaps
5. Finally, it creates a PDF with one slice per page, adding specified margins

### Blank Line Detection

The tool detects content gaps by analyzing each horizontal row of pixels. By default, a row is considered "blank" only if all pixels are nearly white (> 250 on a 0-255 scale). This strict detection can be relaxed using the `--blank-ratio` option:

- `--blank-ratio 0.0` (default): Strict mode - all pixels must be nearly white
- `--blank-ratio 0.1`: Allow up to 10% of pixels to be non-blank and still consider the row "blank"
- `--blank-ratio 0.2`: Allow up to 20% of pixels to be non-blank, and so on

This is particularly useful for images with:
- Slightly noisy or imperfect blank areas
- Compression artifacts in white space
- Subtle background patterns or textures

### Content Splitting Control

The tool's main goal is to slice the image at ideal page breaks. By default, it prioritizes splitting at natural content gaps to avoid awkward breaks. The `--no-split-content` flag changes the fallback behavior when a content block is too long to fit on one page.

- **Default Behavior:** The tool first looks for a content gap within the page's height. If no gap is found, it will split the content directly at the page boundary, which can cut through text or images.
- **With `--no-split-content`:** The tool also looks for a content gap within the page's height. However, if no gap is found, it will **not** split the content. Instead, it extends the slice downwards until it finds the next available gap.

This is useful for ensuring that logical blocks of content (like paragraphs, code blocks, or images) are never cut in half.

**Important**: Because this can create slices taller than the specified page, the tool will exit with an error if a resulting slice cannot fit on the page. To resolve this, you can:

1.  Remove the `--no-split-content` flag to allow content splitting.
2.  Use a larger page size (e.g., `--page-size legal` or `--page-size a3-landscape`).
3.  Use a smaller `--min-gap` value to help the tool detect more potential split points in your image.
4. If your image's blank areas have noise, try `--blank-ratio` to allow for imperfectly blank lines.

## Examples

Converting a tall screenshot into a 3-page PDF with 25mm margins:
```bash
scrollshot2pdf screenshot.png --margin 25mm
```

Handling images with noisy blank areas by allowing 15% non-blank pixels in "blank" lines:
```bash
scrollshot2pdf noisy_image.png --blank-ratio 0.15
```

Preventing content from being split across pages (may require a larger page size):
```bash
scrollshot2pdf long_content.png --no-split-content --page-size legal
```

## Dependencies

- Python 3
- Pillow (PIL)
- reportlab

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgments

Written by Anthropic Claude. Project supervised by [@osteele](https://github.com/osteele).
