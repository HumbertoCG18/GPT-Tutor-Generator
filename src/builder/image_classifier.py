"""Heuristic pre-classification and page mapping for extracted images."""

import logging
import re
import struct
import zlib
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

MIN_FILE_SIZE = 5000      # bytes
MIN_DIMENSION = 50        # pixels
MAX_ASPECT_RATIO = 6.0    # largura/altura or altura/largura
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

    Retorna ``"decorativa"`` para possiveis imagnes que são logos, icones,
    plano de fundo, ou qualquer conteudo não visual. Retorna ``"genérico"``
    para qualquer coisa que possa conter conteúdo acadêmico significativo.
    """
    # 1. Checa o tamanho do arquivo  
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


# ---------------------------------------------------------------------------
# Page extraction patterns
# ---------------------------------------------------------------------------

_PAGE_PATTERNS = [
    re.compile(r"page-(\d{3})-img-\d+", re.IGNORECASE),  # page-006-img-01
    re.compile(r"_page_(\d+)_", re.IGNORECASE),            # _page_6_Figure_1
    re.compile(r"page[_-]?(\d+)", re.IGNORECASE),          # page6, page_6, page-6
]


def extract_page_number(filename: str) -> Optional[int]:
    """Extract page number from an image filename.

    Returns None if no known pattern matches.
    """
    for pattern in _PAGE_PATTERNS:
        m = pattern.search(filename)
        if m:
            return int(m.group(1))
    return None


def group_images_by_page(
    images_dir: Path, entry_prefix: str
) -> Dict[Optional[int], List[Path]]:
    """Group images in a directory by page number.

    Only includes images whose filename starts with *entry_prefix*.
    Images with unrecognized patterns go under key ``None``.
    """
    groups: Dict[Optional[int], List[Path]] = {}
    if not images_dir.exists():
        return groups

    for img_path in sorted(images_dir.iterdir()):
        if not img_path.is_file():
            continue
        if img_path.suffix.lower() not in (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"):
            continue
        if not img_path.name.lower().startswith(entry_prefix.lower()):
            continue

        page = extract_page_number(img_path.name)
        groups.setdefault(page, []).append(img_path)

    return groups
