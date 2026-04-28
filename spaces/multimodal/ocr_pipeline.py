"""
ocr_pipeline.py — Tesseract wrapper used by Phase 3 defenses.

Two functions:
  extract_text(image_bytes)               -> str
  extract_with_confidence(image_bytes)    -> (text, mean_confidence_0_to_100)

Graceful degradation: any Tesseract / Pillow error returns ('', 0.0) and
logs at WARNING. Per api_spec.md, OCR errors must NOT propagate as 5xx;
they degrade so OCR-dependent defenses skip rather than fail the request.

Per `defenses.py`:
  - ocr_prescan        consumes extract_text
  - confidence_threshold consumes extract_with_confidence
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
