# Image to Multi-Page PDF Converter

A command-line tool that converts tall images into multi-page PDFs. It
intelligently splits the image across pages by detecting content gaps, avoiding
awkward breaks in the middle of content.

## Features

- Automatically trims whitespace from image borders
- Intelligently splits pages at content gaps
- Supports multiple page sizes (A4, A3, A5, Letter)
- Configurable margins in millimeters or pixels
- Maintains aspect ratio while scaling to fit page width
- Adds consistent margins to all pages

## Prerequisites

Install uv from [uv.dev](https://docs.astral.sh/uv/getting-started/installation/)

## Usage

Basic usage:
```bash
./image_to_pdf.py input_image.png
```

With options:
```bash
./image_to_pdf.py input_image.png -o output.pdf --page-size a4 --margin 25mm --min-gap 100
```

### Command-line Arguments

- `input_file`: Path to input image (required)
- `--output`, `-o`: Output PDF file (default: input_name.pdf)
- `--page-size`, `-p`: Page size (default: a4)
- `--margin`, `-m`: Margin size (default: 20mm)
- `--min-gap`, `-g`: Minimum gap size in pixels to consider for page breaks (default: 50)

### Page Sizes
Available page sizes:
- A4 (default)
- A3
- A5
- Letter

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
python image_to_pdf.py screenshot.png --margin 25mm
```

## Dependencies

- Python 3
- Pillow (PIL)
- reportlab

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgments

Written by Anthropic Claude. Project supervised by [@osteele](https://github.com/osteele).
