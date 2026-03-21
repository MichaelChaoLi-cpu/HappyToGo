# llm.py
"""
Centralized LLM interface for the Jiazi project.
Currently backed by Google Gemini (google-genai SDK).
"""

from __future__ import annotations

import os
import time
from google import genai
from google.genai import types
from google.api_core.exceptions import DeadlineExceeded, ServiceUnavailable

_CLIENT: genai.Client | None = None


def _get_client() -> genai.Client:
    global _CLIENT
    if _CLIENT is not None:
        return _CLIENT

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Please `source .env` or export it before running."
        )

    _CLIENT = genai.Client(api_key=api_key)
    return _CLIENT


def call_llm(prompt: str, retries: int = 3, backoff: float = 5.0) -> str:
    """
    Call Gemini LLM and return raw text output.

    Environment variables:
      - GEMINI_API_KEY (required)
      - GEMINI_MODEL (optional, default: gemini-2.5-flash) 
      - GEMINI_TEMPERATURE (optional, default: 0.2)
      - GEMINI_MAX_TOKENS (optional, default: 8192)
    """
    client = _get_client()
    model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    temperature = float(os.environ.get("GEMINI_TEMPERATURE", "0.2"))
    max_tokens = int(os.environ.get("GEMINI_MAX_TOKENS", "8192"))

    config = types.GenerateContentConfig(
        temperature=temperature,
        max_output_tokens=max_tokens,
    )

    last_exc: Exception | None = None
    for attempt in range(retries):
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=config,
            )
            return response.text
        except (DeadlineExceeded, ServiceUnavailable) as e:
            last_exc = e
            wait = backoff * (2 ** attempt)
            print(f"[llm] Attempt {attempt + 1}/{retries} failed ({e.__class__.__name__}), retrying in {wait:.0f}s...")
            time.sleep(wait)

    raise last_exc
