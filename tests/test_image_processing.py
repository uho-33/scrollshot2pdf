import os
import tempfile

from scrollshot2pdf import create_pdf, find_content_gaps


def test_find_content_gaps_with_sample_image(sample_image):
    # Test the content gaps finder with our fixture
    gaps = find_content_gaps(sample_image, min_gap_size=30)

    # Should find gaps around y=250 and y=650
    assert len(gaps) == 2
    # Allow some tolerance in gap detection
    assert 220 <= gaps[0] <= 280
    assert 620 <= gaps[1] <= 680


def test_pdf_creation_with_temp_files(sample_image):
    # Create a PDF using a temporary file
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = os.path.join(temp_dir, "output.pdf")

        # Use A4 page size
        page_size = (595.2755905511812, 841.8897637795277)  # A4 in points
        margin_points = 28.35  # 10mm in points

        # Create PDF without OCR
        create_pdf(sample_image, output_path, page_size, margin_points, min_gap_size=50, enable_ocr=False)

        # Check if the PDF was created and has content
        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 0
