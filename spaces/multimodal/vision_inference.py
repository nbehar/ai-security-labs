"""
vision_inference.py — ZeroGPU wrapper for the Multimodal Lab's Vision LLM.

Runs Qwen/Qwen2.5-VL-7B-Instruct (or env-overridden alternate) inside an HF
ZeroGPU `@spaces.GPU` allocation. The first call after a Space wake takes
10–30s for GPU allocation + model load (cached on local disk after first
download). Subsequent calls are ~1–3s.

Per `specs/deployment_spec.md` and platform CLAUDE.md, this space does NOT use
Groq. All inference is local on ZeroGPU.
"""

import io
import logging
import os

import spaces
from PIL import Image

logger = logging.getLogger(__name__)

MODEL_ID = os.environ.get("MULTIMODAL_MODEL", "Qwen/Qwen2.5-VL-7B-Instruct")
MAX_GPU_DURATION = int(os.environ.get("MAX_GPU_DURATION_SECONDS", "60"))

# Lazy module-level globals — the first call to run_vision_inference allocates
# GPU, loads the model, and populates these. They persist across subsequent
# calls within the same Space session.
_model = None
_processor = None


def _ensure_loaded():
    """Lazy-load processor + model. Idempotent."""
    global _model, _processor
    if _model is not None:
        return

    import torch
    from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration

    logger.info(f"Loading multimodal model: {MODEL_ID}")
    _processor = AutoProcessor.from_pretrained(MODEL_ID)
    _model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        MODEL_ID,
        torch_dtype=torch.bfloat16,
        device_map="auto",
    )
    logger.info(f"Model loaded on device: {_model.device}")


@spaces.GPU(duration=MAX_GPU_DURATION)
def run_vision_inference(image_bytes: bytes, prompt: str, max_new_tokens: int = 512) -> str:
    """Run vision inference on (image, prompt) → response text.

    Args:
        image_bytes: raw PNG/JPEG bytes (decoded via PIL.Image.open).
        prompt: text prompt for the model. For the Multimodal Lab, this is
            typically a system-prompt-style description of the DocReceive
            assistant's role concatenated with a generic user request like
            "Process this document."
        max_new_tokens: generation cap. Default 512.

    Returns:
        The model's response text, stripped.

    Cold-start: ~10–30s on first call after Space wake (ZeroGPU allocation
    + model load). Steady-state: ~1–3s per image. On Groq/transformers errors
    the exception propagates — caller is expected to wrap in try/except and
    return a 503.
    """
    _ensure_loaded()

    from qwen_vl_utils import process_vision_info

    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": image},
                {"type": "text", "text": prompt},
            ],
        }
    ]

    text = _processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    image_inputs, video_inputs = process_vision_info(messages)
    inputs = _processor(
        text=[text],
        images=image_inputs,
        videos=video_inputs,
        padding=True,
        return_tensors="pt",
    ).to(_model.device)

    generated_ids = _model.generate(**inputs, max_new_tokens=max_new_tokens)
    generated_ids_trimmed = [
        out_ids[len(in_ids):]
        for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
    ]
    output = _processor.batch_decode(
        generated_ids_trimmed,
        skip_special_tokens=True,
        clean_up_tokenization_spaces=False,
    )[0]
    return output.strip()


def is_loaded() -> bool:
    """True once the first inference has triggered GPU allocation + model load."""
    return _model is not None
