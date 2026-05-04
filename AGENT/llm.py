# llm.py
"""
Centralized LLM interface.
Supports Gemini (google-genai) and DeepSeek (OpenAI-compatible).

Provider is selected via LLM_PROVIDER env var: "gemini" (default) or "deepseek".
"""

from __future__ import annotations

import os
import time


# ---------------------------------------------------------------------------
# Gemini backend
# ---------------------------------------------------------------------------
_GEMINI_CLIENT = None

def _gemini_call(prompt: str, retries: int, backoff: float) -> str:
    from google import genai
    from google.genai import types
    from google.api_core.exceptions import DeadlineExceeded, ServiceUnavailable

    global _GEMINI_CLIENT
    if _GEMINI_CLIENT is None:
        api_key = os.environ.get("GEMINI_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not set.")
        _GEMINI_CLIENT = genai.Client(api_key=api_key)

    model       = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    temperature = float(os.environ.get("GEMINI_TEMPERATURE", "0.2"))
    max_tokens  = int(os.environ.get("GEMINI_MAX_TOKENS", "8192"))

    config = types.GenerateContentConfig(
        temperature=temperature,
        max_output_tokens=max_tokens,
    )

    last_exc: Exception | None = None
    for attempt in range(retries):
        try:
            response = _GEMINI_CLIENT.models.generate_content(
                model=model, contents=prompt, config=config,
            )
            return response.text
        except (DeadlineExceeded, ServiceUnavailable) as e:
            last_exc = e
            wait = backoff * (2 ** attempt)
            print(f"[llm/gemini] Attempt {attempt+1}/{retries} failed, retrying in {wait:.0f}s...")
            time.sleep(wait)
    raise last_exc


# ---------------------------------------------------------------------------
# DeepSeek backend (OpenAI-compatible)
# ---------------------------------------------------------------------------
def _deepseek_call(prompt: str, retries: int, backoff: float) -> str:
    from openai import OpenAI

    api_key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("DEEPSEEK_API_KEY is not set.")

    model       = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
    temperature = float(os.environ.get("DEEPSEEK_TEMPERATURE", "0.2"))
    max_tokens  = int(os.environ.get("DEEPSEEK_MAX_TOKENS", "8192"))

    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

    last_exc: Exception | None = None
    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content
        except Exception as e:
            last_exc = e
            wait = backoff * (2 ** attempt)
            print(f"[llm/deepseek] Attempt {attempt+1}/{retries} failed, retrying in {wait:.0f}s...")
            time.sleep(wait)
    raise last_exc


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------
def call_llm(prompt: str, retries: int = 3, backoff: float = 5.0) -> str:
    """Call the active LLM provider and return raw text output."""
    provider = os.environ.get("LLM_PROVIDER", "gemini").strip().lower()
    if provider == "deepseek":
        return _deepseek_call(prompt, retries, backoff)
    return _gemini_call(prompt, retries, backoff)
