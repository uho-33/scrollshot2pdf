from scrollshot2pdf import calculate_slices


def test_calculate_slices_basic():
    # Test slicing a 1000px image into 300px slices
    image_height = 1000
    page_height = 300
    content_gaps = []  # No content gaps

    slices = calculate_slices(image_height, page_height, content_gaps)

    # Should be split evenly
    expected_slices = [(0, 300), (300, 600), (600, 900), (900, 1000)]
    assert slices == expected_slices


def test_calculate_slices_with_gaps():
    # Test slicing a 1000px image into 300px slices with some content gaps
    image_height = 1000
    page_height = 300
    # Add gap at positions that are near ideal slice points
    content_gaps = [280, 590, 880]

    slices = calculate_slices(image_height, page_height, content_gaps)

    # Check that we get back the right number of slices that span the whole image
    assert len(slices) == 4
    assert slices[0][0] == 0
    assert slices[-1][1] == 1000

    # Check that at least the first gap is used
    assert slices[0][1] == 280


def test_calculate_slices_gap_too_far():
    # Test case where a gap is too far from ideal slice point
    image_height = 1000
    page_height = 300
    # Gap is too far from ideal slice point (would be at 300)
    content_gaps = [200, 500, 800]

    slices = calculate_slices(image_height, page_height, content_gaps)

    # Should ignore gaps that are too far from ideal points
    expected_slices = [(0, 300), (300, 600), (600, 900), (900, 1000)]
    assert slices == expected_slices


def test_calculate_slices_exact_height():
    # Test slicing an image that is exactly divisible by page height
    image_height = 900
    page_height = 300
    content_gaps = []

    slices = calculate_slices(image_height, page_height, content_gaps)

    expected_slices = [(0, 300), (300, 600), (600, 900)]
    assert slices == expected_slices
