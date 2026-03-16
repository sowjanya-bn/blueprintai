from __future__ import annotations

import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")


def is_available() -> bool:
    """Return True if a Gemini API key is configured."""
    return bool(os.getenv("GEMINI_API_KEY"))


def generate_json(prompt: str) -> Optional[str]:
    """Call Gemini and return the raw JSON string, or None if unavailable/failed."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,
                response_mime_type="application/json",
            ),
        )
        text = (response.text or "").strip()
        return text if text else None
    except Exception:
        return None