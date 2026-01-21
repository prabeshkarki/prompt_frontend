from __future__ import annotations

from google import genai
from google.genai import types
from google.genai.errors import ClientError

from app.config import get_settings
from app.logger import logger

settings = get_settings()
client = genai.Client(api_key=settings.gemini_api_key)

def generate_text(prompt: str) -> str:
    try:
        res = client.models.generate_content(
            model=settings.gemini_model,
            contents=[prompt],
            config=types.GenerateContentConfig(
                response_mime_type="text/plain",
                temperature=0.4,
                max_output_tokens=600,
            ),
        )
        text = (res.text or "").strip()
        return text if text else "LLM returned empty output."
    except ClientError as e:
        msg = str(e)
        if getattr(e, "status_code", None) == 429 or "RESOURCE_EXHAUSTED" in msg:
            logger.error("Gemini quota exhausted: %s", msg)
            return "LLM unavailable due to quota limits."
        logger.error("Gemini ClientError: %s", msg)
        return "LLM unavailable due to Gemini error."
    except Exception:
        logger.exception("Gemini generate failed")
        return "LLM unavailable due to internal error."