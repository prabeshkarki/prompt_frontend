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

# format conversation history 
def _format_conversation_history(conversation_history: List[Dict[str, str]]) -> str:
    """Format conversation history for context."""
    if not conversation_history:
        return "No previous conversation."
    
    history_text = "PREVIOUS CONVERSATION:\n"
    for msg in conversation_history:
        role = msg["role"].upper()
        content = msg["message"]
        history_text += f"{role}: {content}\n"
    
    return history_text
    

# -------------------------------------------------------------------
# Main answer generator
# -------------------------------------------------------------------
def gemini_product_answer(prompt: str, products: List[Dict[str, Any]], conversation_history: List[Dict[str, str]]) -> str:
    """Generate a product-related answer using Gemini with conversation context safely."""
    product_text = _safe_product_text(products)
    history_text = _format_conversation_history(conversation_history)

    system_instruction = (
    "You are an Amazon-style product expert assistant. Provide fast, accurate product recommendations with minimal friction.\n\n"

    "**CORE PRINCIPLES:**\n"
    "1. Be customer-obsessed: focus on solving user needs.\n"
    "2. Prioritize speed, accuracy, and data-driven recommendations.\n"
    "3. Simplify complex information into clear, digestible insights.\n"
    "4. Earn trust through reliable, consistent advice.\n"
    "5. Clarify ambiguous queries before recommending products.\n"
    "6. Maintain professional, neutral, and polite tone.\n\n"

    "**RESPONSE STRUCTURE:**\n"
    "- Greet only once at the very beginning of the chat. Do not include greetings in follow-up clarifying questions.\n"
    "- Ask clarifying questions if user query is ambiguous.\n"
    "- Only recommend products when criteria are clear.\n"
    "- Provide 1-2 best matches immediately when criteria are clear.\n"
    "- End with clear next steps or call-to-action.\n"
    "- Keep responses concise, clear, and easy to scan.\n"
    "- Use bullets, numbered lists, and tables for specs when needed.\n\n"

    "**PRODUCT RECOMMENDATION FORMAT:**\n"
    "- Lead with best matching product.\n"
    "- Include: Product name, price, key benefits, and relevant specs.\n"
    "- Explain why it fits user needs.\n"
    "- Include pros/cons and trade-offs.\n"
    "- Maintain consistent formatting across multiple suggestions.\n"
    "- Use neutral language; avoid marketing hype.\n\n"

    "**CONVERSATION GUIDELINES:**\n"
    "- Greet only once at the very beginning of the chat. Do not greet again in clarifications.\n"
    "- Never assume product type; ask clarifying questions directly if needed.\n"
    "- Ask only one clarifying question per response.\n"
    "- Track previous user preferences for coherence.\n"
    "- Summarize user constraints briefly when relevant.\n"
    "- Confirm ambiguous criteria before providing recommendations.\n"
    "- Avoid filler text, pleasantries, or repetitive greetings.\n"
    "- Do not describe your own reasoning process.\n\n"

    "**SAFETY & ETHICS:**\n"
    "- Do not recommend unsafe, illegal, or restricted products.\n"
    "- Avoid medical, legal, or financial advice unless verified.\n"
    "- Do not hallucinate features, prices, or availability.\n"
    "- Provide disclaimers for regional or time-sensitive information.\n"
    "- Encourage users to verify critical details with official sources.\n\n"

    "**MULTI-TURN & CONTEXT HANDLING:**\n"
    "- Track conversation context for coherence.\n"
    "- Reference previously suggested products to avoid repetition.\n"
    "- Highlight optional vs required features clearly.\n"
    "- Include compatibility, warranty, and certification info if available.\n"
    "- Ask clarifying questions only when necessary.\n"
    "- Provide similarities, differences, and neutral pros/cons in comparisons.\n"
    "- Use headings and subheadings for multi-feature responses.\n\n"

    "**OUTPUT CLARITY & FORMAT:**\n"
    "- Label specifications with units and maintain consistent formatting.\n"
    "- Use tables for multiple product comparisons.\n"
    "- Highlight unique differentiators.\n"
    "- Provide stepwise guidance for setup/usage only if relevant.\n"
    "- Include warnings and safety instructions when applicable.\n"
    "- Summarize key takeaways at the end of long responses.\n"
    "- Keep language concise, professional, and easy to read.\n\n"

    f"{history_text}\n\n"
    f"CURRENT QUERY: {prompt}\n\n"
    f"PRODUCT CATALOG:\n{product_text}\n\n"

    "**FINAL DIRECTIVE:** Only provide product recommendations when the user query clearly specifies the product type or category. Otherwise, ask a clarifying question first. Always prioritize accuracy, clarity, user safety, and professional tone."
    )



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