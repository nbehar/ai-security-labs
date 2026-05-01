"""
ocr_pipeline.py — Tesseract wrapper used by Phase 3 defenses.

Three functions:
  extract_text(image_bytes)                -> str
  extract_with_confidence(image_bytes)     -> (text, mean_confidence_0_to_100)
  extract_low_contrast_ratio(image_bytes)  -> float (0.0–1.0)

Graceful degradation: any Tesseract / Pillow error returns ('', 0.0) and
logs at WARNING. Per api_spec.md, OCR errors must NOT propagate as 5xx;
they degrade so OCR-dependent defenses skip rather than fail the request.

Per `defenses.py`:
  - ocr_prescan           consumes extract_text
  - confidence_threshold  consumes extract_with_confidence + extract_low_contrast_ratio
"""

import io
import logging
from typing import Tuple

from PIL import Image

logger = logging.getLogger(__name__)


def _open_image(image_bytes: bytes) -> Image.Image:
    return Image.open(io.BytesIO(image_bytes))


def extract_text(image_bytes: bytes) -> str:
    """Return all OCR text from the image, joined by spaces. Empty on error."""
    try:
        import pytesseract  # imported lazily so unit tests can stub
        img = _open_image(image_bytes)
        return pytesseract.image_to_string(img).strip()
    except Exception as e:
        logger.warning("ocr_pipeline.extract_text failed: %s: %s", type(e).__name__, e)
        return ""


def extract_with_confidence(image_bytes: bytes) -> Tuple[str, float]:
    """Return (text, mean_word_confidence) from the image.

    Tesseract reports per-word confidence 0-100; words with no text get -1
    which we exclude from the mean. Empty image / no recognizable text → 0.0.
    """
    try:
        import pytesseract
        from pytesseract import Output
        img = _open_image(image_bytes)
        data = pytesseract.image_to_data(img, output_type=Output.DICT)
        words = []
        confs = []
        for i, word in enumerate(data.get("text", [])):
            if word and word.strip():
                try:
                    c = float(data["conf"][i])
                except (ValueError, TypeError, KeyError):
                    continue
                if c >= 0:
                    words.append(word)
                    confs.append(c)
        text = " ".join(words)
        mean_conf = sum(confs) / len(confs) if confs else 0.0
        return text, mean_conf
    except Exception as e:
        logger.warning(
            "ocr_pipeline.extract_with_confidence failed: %s: %s",
            type(e).__name__, e,
        )
        return "", 0.0


def extract_low_contrast_ratio(image_bytes: bytes) -> float:
    """Detect near-white hidden text via histogram spike analysis.

    Hidden near-white text (e.g., fill=252 on a 255 background) creates a
    cluster of pixels at a specific luminance value that is absent in normal
    white-background documents. We find the largest such spike in the
    241–253 luminance range (above this = pure white; below = visible gray).

    Method:
      1. Build a per-value pixel count for luminance 241–253.
      2. Return (max_spike_count / total_pixels).

    A ratio ≥ 0.001 (0.1%) indicates likely hidden text:
      - P5.1 NEAR_WHITE (252 on 255): ~1–2% ratio — caught
      - P5.3 PALE_YELLOW grayscale 248 (on 255): ~1–2% ratio — caught
      - Legit documents (anti-aliased dark text): typically < 0.04% for any
        specific value in 241–253 — not caught

    Returns 0.0 on any Pillow error (graceful degradation).
    """
    try:
        img = _open_image(image_bytes).convert("L")
        pixels = list(img.getdata())
        total = len(pixels)
        if not total:
            return 0.0

        # Count pixels per exact value in near-white range 241–253
        counts: dict[int, int] = {}
        for p in pixels:
            if 241 <= p <= 253:
                counts[p] = counts.get(p, 0) + 1

        max_spike = max(counts.values(), default=0)
        return max_spike / total
    except Exception as e:
        logger.warning(
            "ocr_pipeline.extract_low_contrast_ratio failed: %s: %s", type(e).__name__, e
        )
        return 0.0
