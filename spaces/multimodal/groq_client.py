"""
groq_client.py — Shared Groq API client for all workshops
==========================================================
"""

import os
from typing import Optional
from groq import Groq

GROQ_MODEL = "llama-3.3-70b-versatile"
_client: Optional[Groq] = None


def get_groq_client() -> Groq:
    global _client
    if _client is None:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY environment variable not set")
        _client = Groq(api_key=api_key)
    return _client


def generate_response(messages: list[dict], max_tokens: int = 1024, temperature: float = 0.7) -> str:
    """Call Groq API and return the response text."""
    client = get_groq_client()
    completion = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return completion.choices[0].message.content.strip()
