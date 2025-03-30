import pytest
from PIL import Image


@pytest.fixture
def sample_image():
    """Create a sample image for testing with blank areas."""
    width, height = 500, 1000
    image = Image.new("RGB", (width, height), "white")

    # Create some content areas (non-white)
    # Area 1: top area
    for y in range(0, 200):
        for x in range(50, 450):
            image.putpixel((x, y), (0, 0, 0))

    # Area 2: middle area (after a gap)
    for y in range(300, 600):
        for x in range(100, 400):
            image.putpixel((x, y), (0, 0, 0))

    # Area 3: bottom area (after another gap)
    for y in range(700, 950):
        for x in range(200, 450):
            image.putpixel((x, y), (0, 0, 0))

    return image
