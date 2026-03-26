"""Heuristic pre-classification of images as decorative vs. relevant."""

import logging
import struct
import zlib
from pathlib import Path

logger = logging.getLogger(__name__)

MIN_FILE_SIZE = 5000      # bytes
MIN_DIMENSION = 50        # pixels
MAX_ASPECT_RATIO = 6.0    # width/height or height/width
MAX_NOISE_COLORS = 8      # unique colors in sampled pixels


def _read_png_dimensions(path: Path) -> tuple[int, int]:
    """Read width and height from a PNG IHDR chunk."""
    data = path.read_bytes()
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("Not a valid PNG file")
    # IHDR is always the first chunk, starting at byte 8
    # 4 bytes length + 4 bytes "IHDR" + 4 bytes width + 4 bytes height
    width, height = struct.unpack(">II", data[16:24])
    return width, height


def _count_unique_colors_png(path: Path, sample_limit: int = 2000) -> int:
    """Count unique RGB colors by decompressing PNG IDAT chunks.

    Samples up to *sample_limit* pixels to keep it fast.
    """
    data = path.read_bytes()
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        return sample_limit  # not PNG, assume complex

    # Parse IHDR
    width, height = struct.unpack(">II", data[16:24])
    bit_depth = data[24]
    color_type = data[25]

    # Only handle 8-bit RGB (color_type 2) and 8-bit RGBA (color_type 6)
    if bit_depth != 8 or color_type not in (2, 6):
        return sample_limit  # can't easily parse, assume complex

    channels = 3 if color_type == 2 else 4

    # Collect all IDAT data
    idat_data = b""
    offset = 8  # after PNG signature
    while offset < len(data):
        chunk_len = struct.unpack(">I", data[offset:offset + 4])[0]
        chunk_type = data[offset + 4:offset + 8]
        chunk_body = data[offset + 8:offset + 8 + chunk_len]
        offset += 12 + chunk_len  # length + type + data + crc
        if chunk_type == b"IDAT":
            idat_data += chunk_body
        elif chunk_type == b"IEND":
            break

    try:
        raw = zlib.decompress(idat_data)
    except zlib.error:
        return sample_limit

    stride = 1 + width * channels  # filter byte + pixel data per row
    colors = set()
    sampled = 0
    for y in range(height):
        row_start = y * stride + 1  # skip filter byte
        for x in range(width):
            px_start = row_start + x * channels
            rgb = raw[px_start:px_start + 3]  # ignore alpha if present
            colors.add(rgb)
            sampled += 1
            if sampled >= sample_limit:
                return len(colors)

    return len(colors)


def classify_image(image_path: Path) -> str:
    """Classify an image as ``decorativa`` or ``genérico`` using heuristics.

    Returns ``"decorativa"`` for images likely to be logos, icons,
    backgrounds, or other non-content visuals. Returns ``"genérico"``
    for anything that might contain meaningful academic content.
    """
    # 1. File size check
    if image_path.stat().st_size < MIN_FILE_SIZE:
        logger.debug("Decorativa (file size): %s", image_path.name)
        return "decorativa"

    # 2. Dimensions check
    try:
        width, height = _read_png_dimensions(image_path)
    except (ValueError, struct.error):
        # Not a valid PNG or can't read — assume relevant
        return "genérico"

    if width < MIN_DIMENSION or height < MIN_DIMENSION:
        logger.debug("Decorativa (small dimension): %s", image_path.name)
        return "decorativa"

    # 3. Aspect ratio check
    if width > 0 and height > 0:
        ratio = max(width / height, height / width)
        if ratio > MAX_ASPECT_RATIO:
            logger.debug("Decorativa (aspect ratio %.1f): %s", ratio, image_path.name)
            return "decorativa"

    # 4. Unique colors check
    unique_colors = _count_unique_colors_png(image_path)
    if unique_colors <= MAX_NOISE_COLORS:
        logger.debug("Decorativa (%d unique colors): %s", unique_colors, image_path.name)
        return "decorativa"

    return "genérico"
