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
pip install git+https://github.com/osteele/scrollshot2pdf.git
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

OCR uses the Tesseract library, and only works on Latin characters.

Additional dependencies for OCR:

```bash
pip install pytesseract pdf2image
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
3. It analyzes the image to find vertical gaps in content
4. It calculates optimal slice positions based on page height and content gaps
5. Finally, it creates a PDF with one slice per page, adding specified margins

## Example

Converting a tall screenshot into a 3-page PDF with 25mm margins:
```bash
scrollshot2pdf screenshot.png --margin 25mm
```

## Dependencies

- Python 3
- Pillow (PIL)
- reportlab

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgments

Written by Anthropic Claude. Project supervised by [@osteele](https://github.com/osteele).
