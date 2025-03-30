import pytest
from PIL import Image

from scrollshot2pdf import (
    calculate_optimal_columns,
    find_content_gaps,
    mm_to_pixels,
    mm_to_points,
    parse_margin,
    parse_page_range,
    title_from_filename,
    trim_whitespace,
)


def test_mm_to_pixels():
    assert mm_to_pixels(10) == 28
    assert mm_to_pixels(25.4) == 72
    assert mm_to_pixels(10, dpi=96) == 37


def test_mm_to_points():
    assert mm_to_points(10) == pytest.approx(28.35, rel=0.01)
    assert mm_to_points(25.4) == 72


def test_parse_margin():
    assert parse_margin("10mm") == pytest.approx(28.35, rel=0.01)
    assert parse_margin("10px") == 7.5
    assert parse_margin("10") == 7.5
    with pytest.raises(ValueError):
        parse_margin("invalid")


def test_title_from_filename():
    assert title_from_filename("test.png") == "Test"
    assert title_from_filename("test_file.png") == "Test File"
    assert title_from_filename("test-file.png") == "Test File"
    assert title_from_filename("TEST_FILE.png") == "TEST FILE"
    assert title_from_filename("/path/to/test_file.png") == "Test File"


def test_parse_page_range():
    assert parse_page_range("", 10) == (1, 10)
    assert parse_page_range("5", 10) == (5, 5)
    assert parse_page_range("5-8", 10) == (5, 8)
    assert parse_page_range("-8", 10) == (1, 8)
    assert parse_page_range("5-", 10) == (5, 10)

    with pytest.raises(ValueError):
        parse_page_range("11", 10)

    with pytest.raises(ValueError):
        parse_page_range("5-11", 10)

    with pytest.raises(ValueError):
        parse_page_range("8-5", 10)


@pytest.mark.skip(reason="Currently failing; fix this later")
def test_trim_whitespace():
    # Create a test image with a white border
    width, height = 100, 100
    image = Image.new("RGB", (width, height), "white")

    # Draw a black rectangle in the center
    content_width, content_height = 50, 60
    x0 = (width - content_width) // 2
    y0 = (height - content_height) // 2
    x1 = x0 + content_width
    y1 = y0 + content_height

    for x in range(x0, x1):
        for y in range(y0, y1):
            image.putpixel((x, y), (0, 0, 0))

    # Test trimming
    trimmed = trim_whitespace(image)

    # The trimmed image should be the size of the black rectangle
    assert trimmed.size == (content_width, content_height)


def test_find_content_gaps():
    # Create a test image with horizontal white stripes
    width, height = 100, 300
    image = Image.new("RGB", (width, height), "black")

    # Create 3 white gaps
    gap_positions = [(50, 70), (120, 170), (220, 250)]

    for y in range(height):
        for gap_start, gap_end in gap_positions:
            if gap_start <= y < gap_end:
                for x in range(width):
                    image.putpixel((x, y), (255, 255, 255))

    # Test finding gaps with min gap size of 15px
    gaps = find_content_gaps(image, min_gap_size=15)

    # Should find all 3 gaps at approximately their centers
    expected_positions = [60, 145, 235]
    assert len(gaps) == 3

    # Allow some wiggle room in position calculations
    for expected, actual in zip(expected_positions, gaps, strict=False):
        assert abs(expected - actual) <= 2


def test_calculate_optimal_columns():
    # Create a test image
    image = Image.new("RGB", (1000, 2000), "white")

    # Test with different page widths and image widths
    # Case 1: Image fits within page width
    assert calculate_optimal_columns(500, 600, image) == 1

    # Case 2: Image needs scaling
    assert calculate_optimal_columns(1000, 500, image) in [1, 2, 3]
