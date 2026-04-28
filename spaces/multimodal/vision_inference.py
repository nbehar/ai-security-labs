"""
vision_inference.py — Multimodal Lab vision inference via HF Inference Providers.

Routes inference to a hosted Qwen2.5-VL-7B-Instruct (or env-overridden alternate)
via the HuggingFace Inference Providers API (Together AI by default; configurable
via `HF_INFERENCE_PROVIDER`). The Space itself runs on `cpu-basic` — no GPU, no
local model load.

This was a deliberate pivot from ZeroGPU + local model load: ZeroGPU on HF Spaces
requires the Gradio SDK, which is incompatible with the platform's
Docker/FastAPI architecture. Routing through Inference Providers keeps the
existing architecture, eliminates cold-start, and uses HF Pro inference credit.

Per `specs/deployment_spec.md`. Requires `HF_TOKEN` env var (set as a Space
secret) to authorize Inference Provider calls.
"""

import base64
import logging
import os
from typing import Optional

from huggingface_hub import InferenceClient

logger = logging.getLogger(__name__)

MODEL_ID = os.environ.get("MULTIMODAL_MODEL", "Qwen/Qwen2.5-VL-7B-Instruct")
INFERENCE_PROVIDER = os.environ.get("HF_INFERENCE_PROVIDER", "together")

_client: Optional[InferenceClient] = None


def _get_client() -> InferenceClient:
    """Lazy-initialize the InferenceClient. Idempotent."""
    global _client
    if _client is None:
        token = os.environ.get("HF_TOKEN")
        if not token:
            raise RuntimeError("HF_TOKEN environment variable not set")
        _client = InferenceClient(provider=INFERENCE_PROVIDER, token=token)
        logger.info(
            f"Initialized HF InferenceClient (provider={INFERENCE_PROVIDER}, "
            f"model={MODEL_ID})"
        )
    return _client


def run_vision_inference(image_bytes: bytes, prompt: str, max_new_tokens: int = 512) -> str:
    """Run vision inference on (image, prompt) → response text.

    Args:
        image_bytes: raw PNG/JPEG bytes.
        prompt: text prompt for the model.
        max_new_tokens: generation cap. Default 512.

    Returns:
        Model response text, stripped.

    Latency: typically 1–3s. No cold-start: HF's hosted model is warm-served.
    On HF API errors the exception propagates — caller wraps in try/except.

    Cost: per-call via HF Inference Providers (cheap; HF Pro accounts include
    monthly inference credit that covers workshop volume).
    """
    img_b64 = base64.b64encode(image_bytes).decode("ascii")
    data_url = f"data:image/png;base64,{img_b64}"

    client = _get_client()
    response = client.chat_completion(
        model=MODEL_ID,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": data_url}},
                    {"type": "text", "text": prompt},
                ],
            }
        ],
        max_tokens=max_new_tokens,
    )
    return response.choices[0].message.content.strip()


def is_ready() -> bool:
    """True if HF_TOKEN is set (the inference layer is configured).

    There is no local model load to gate on — every call hits the hosted API.
    This flag mainly drives the /health endpoint.
    """
    return bool(os.environ.get("HF_TOKEN"))


# Backwards-compatible alias — earlier Phase 1 code referenced is_loaded()
is_loaded = is_ready
