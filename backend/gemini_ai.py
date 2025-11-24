# ...existing code...
from google.generativeai.generative_models import GenerativeModel
import google.generativeai as genai
import os
import logging
from dotenv import load_dotenv
from typing import List, Dict, Any

load_dotenv()

# Load API key
GENAI_API_KEY = (
    os.getenv("GEMINI_API_KEY")
    or os.getenv("GOOGLE_API_KEY")
    or os.getenv("GENAI_API_KEY")
)

# Try to configure at import but do not raise — mark configured flag instead
_genai_configured = False
try:
    if GENAI_API_KEY:
        genai.configure(api_key=GENAI_API_KEY)  # type: ignore[attr-defined]
        _genai_configured = True
    else:
        logging.warning("No Gemini/GenAI API key found; gemini_ai will be disabled until configured.")
except Exception as e:
    logging.exception("Failed to configure genai SDK; gemini_ai will be disabled.")
    _genai_configured = False
# -------------------------------------------------------------------
# Lazy Model Loader
# -------------------------------------------------------------------
def _get_model():
    """Lazy-init and cache a GenerativeModel instance. Raises RuntimeError if SDK unavailable."""
    if not _genai_configured:
        raise RuntimeError("GenAI SDK not configured or API key missing.")

    # Import inside function to avoid import-time crash if package missing
    try:
        from google.generativeai.generative_models import GenerativeModel
    except Exception as e:
        raise RuntimeError("GenerativeModel import failed; check google.generativeai installation.") from e

    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
    if not hasattr(_get_model, "instance"):
        _get_model.instance = GenerativeModel(model_name=model_name)
    return _get_model.instance

# -------------------------------------------------------------------
# Safe product text builder
# -------------------------------------------------------------------
def _safe_product_text(products: List[Dict[str, Any]], max_chars: int = 3000) -> str:
    """Generate safe truncated product text for the model."""
    lines = []
    for p in products:
        name = str(p.get("name", ""))[:200]
        desc = str(p.get("description", ""))[:500]
        price = p.get("price", "")
        lines.append(f"- {name}: {desc} (Rs {price})")

    text = "\n".join(lines)

    if len(text) > max_chars:
        text = text[: max_chars - 20] + "\n... (truncated)"

    return text


# -------------------------------------------------------------------
# Main answer generator
# -------------------------------------------------------------------
def gemini_product_answer(prompt: str, products: List[Dict[str, Any]]) -> str:
    """Generate a product-related answer using Gemini safely."""
    product_text = _safe_product_text(products)

    system_instruction = (
        "You are a product information assistant.\n"
        "Only answer questions about the products listed below.\n"
        "If the user asks anything else, reply:\n"
        "'I can only answer questions about products.'\n\n"
        f"Available products:\n{product_text}\n\n"
    )

    # system_instruction = (
    #     "You are a product and website information assistant for our company.\n"
    #     "Your primary role is to answer questions specifically about our products and website content.\n"
    #     "If users ask about anything else, politely redirect them by saying:\n"
    #     "'I'm specialized in helping with product information and website navigation. How can I assist you with our products or website today?'\n\n"
    #     "For product inquiries, focus on:\n"
    #     "- Product features and specifications\n"
    #     "- Pricing and availability\n"
    #     "- Compatibility and use cases\n"
    #     "- Comparisons between products\n"
    #     "- Troubleshooting common issues\n\n"
    #     "For website assistance, help with:\n"
    #     "- Finding specific pages or information\n"
    #     "- Understanding policies (shipping, returns, etc.)\n"
    #     "- Navigation guidance\n"
    #     "- Account and order related questions\n\n"
    #     f"Available Products:\n{product_text}\n\n"
    #     "Always be helpful, accurate, and maintain a friendly professional tone.\n"
    #     "If you don't know something, offer to connect them with human support rather than guessing."
    # )

    # Limit prompt size
    max_prompt = 2000
    if len(prompt) > max_prompt:
        prompt = prompt[: max_prompt - 13] + " ... (truncated)"

    final_input = system_instruction + prompt

    try:
        model = _get_model()
        response = model.generate_content(final_input)

        # Modern SDK → always returns response.text
        text = getattr(response, "text", None)
        if text:
            return text.strip()

        # Compatibility fallback (older SDK)
        if hasattr(response, "candidates") and response.candidates:
            cand = response.candidates[0]

            # Best candidate text
            text = getattr(cand, "text", None)
            if text:
                return text.strip()

            # No iterable content! So no looping cand.content.
            # Just fallback to string.
            return str(cand)

        # Last fallback
        return str(response)

    except Exception as e:
        return f"Error generating response: {e}"