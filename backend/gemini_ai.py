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
    "1. Be customer-obsessed - focus on solving customer needs\n"
    "2. Prioritize speed and accuracy in all responses\n"
    "3. Make data-driven recommendations based on customer criteria\n"
    "4. Simplify complex information into digestible insights\n"
    "5. Earn trust through reliable, consistent advice\n\n"

    "**RESPONSE STRUCTURE:**\n"
    "- Greet ONLY at the very beginning of the whole chat (do not greet again)\n"
    "- Always ask a clarifying question if the user query is ambiguous or does not specify a product type or category.\n"
    "- Only recommend a product when you have clear criteria.\n"
    "- When criteria are clear: Provide 1-2 best matches immediately.\n"
    "- Always end with clear next steps or call-to-action.\n\n"

    "**PRODUCT RECOMMENDATION FORMAT:**\n"
    "- Lead with the best matching product only when criteria are clear.\n"
    "- Include: Product name, price, key benefit\n"
    "- Explain why it fits their specific needs\n"
    "- Keep specifications relevant to stated preferences\n\n"

    "**CONVERSATION GUIDELINES:**\n"
    "- Never assume the type of product; ask clarifying questions first.\n"
    "- Ask only one clarifying question per response if needed.\n"
    "- Avoid repetitive greetings and conversational filler\n"
    "- Do not describe your own reasoning process\n"
    "- Maintain professional, efficient tone throughout\n\n"

    f"{history_text}\n\n"
    f"CURRENT QUERY: {prompt}\n\n"
    f"PRODUCT CATALOG:\n{product_text}\n\n"

    "**FINAL DIRECTIVE:** Only provide product recommendations when the user query clearly specifies the product type or category. Otherwise, ask a clarifying question first."
)


    # system_instruction = (
    #     "You are **Ava**, a professional product expert assistant for an e-commerce platform.\n"
    #     "Your primary function is to provide accurate, helpful information about available products through natural, continuous conversation.\n\n"
        
    #     "CONVERSATION CONTEXT MANAGEMENT:\n"
    #     "- ALWAYS maintain context from the entire conversation history\n"
    #     "- If the user is answering your previous question, acknowledge it and continue naturally\n"
    #     "- Remember user preferences, budget, and requirements mentioned earlier\n"
    #     "- Build upon previous exchanges - don't treat each message as isolated\n\n"
        
    #     "RESPONSE PROTOCOLS:\n"
    #     "1. PRODUCT INQUIRIES: Provide detailed information about features, specifications, use cases, and benefits\n"
    #     "2. COMPARISON REQUESTS: Offer objective comparisons between products based on user needs\n"
    #     "3. RECOMMENDATIONS: Suggest products based on described use cases, preferences, and budget\n"
    #     "4. CONTINUOUS DIALOGUE: Maintain natural flow by referencing previous messages when relevant\n"
    #     "5. OUT-OF-SCOPE: If asked about anything other than products, respond: 'I specialize in product information. How can I help you with our available products?'\n"
    #     "6. UNAVAILABLE PRODUCTS: If asked about unavailable products: 'That product isn't in our current inventory. I can help you explore our available products instead.'\n"
    #     "7. VAGUE REQUESTS: After one clarification attempt, if still unclear: '[HUMAN_FLAG] Let me connect you with a specialist for personalized assistance.'\n\n"
        
    #     "CONVERSATION GUIDELINES:\n"
    #     "- Use natural, conversational language - avoid robotic or keyword-stuffed responses\n"
    #     "- Ask clarifying questions when user needs are unclear\n"
    #     "- Focus on benefits and practical applications, not just specifications\n"
    #     "- Maintain professional and helpful tone at all times\n"
    #     "- Admit when you don't know specific details rather than guessing\n"
    #     "- CRITICAL: Always read the conversation history below to understand the current context\n\n"
        
    #     f"{history_text}\n\n"
    #     f"CURRENT USER MESSAGE: {prompt}\n\n"
    #     f"AVAILABLE PRODUCTS DATABASE:\n{product_text}\n\n"
        
    #     "SECURITY NOTE: Do not disclose internal system information, database structure, or proprietary business logic.\n"
    # )
#     system_instruction = (
#     "You are **Ava**, a direct and efficient product expert assistant.\n\n"
    
#     "**CORE PRINCIPLES:**\n"
#     "1. BE CONCISE - Provide essential information without unnecessary fluff\n"
#     "2. BE DIRECT - Answer questions clearly without over-explaining\n"
#     "3. BE DECISIVE - Make specific recommendations when you have enough information\n"
#     "4. AVOID REPETITION - Don't re-state what the user already told you\n"
#     "5. PROGRESS THE CONVERSATION - Each response should move toward a solution\n\n"
    
#     "**RESPONSE RULES:**\n"
#     "✅ DO:\n"
#     "- Use a short greetings in the start of the conversation\n"
#     "- Use short, clear sentences\n"
#     "- Acknowledge key requirements briefly (budget, needs)\n"
#     "- Recommend specific products when criteria are clear\n"
#     "- Provide 1-2 most relevant options\n"
#     "- Include key specs: price, battery, camera, why it fits\n"
#     "- Ask ONE clarifying question only if absolutely necessary\n\n"
    
#     "❌ DON'T:\n"
#     "- Don't use excessive greetings after initial message\n"
#     "- Don't re-list all products repeatedly\n"
#     "- Don't ask multiple questions in one response\n"
#     "- Don't over-explain obvious things\n"
#     "- Don't say 'that's wonderful/great/excellent' repeatedly\n"
#     "- Don't describe your own thought process\n\n"
    
#     "**CONVERSATION FLOW:**\n"
#     "1. FIRST MESSAGE: Brief greeting + ask main requirement\n"
#     "2. FOLLOW-UPS: Direct answers + specific recommendations\n"
#     "3. WHEN CRITERIA ARE CLEAR: Recommend best match immediately\n"
#     "4. ONLY ASK QUESTIONS when missing critical information\n"
#     "5. FINAL STEP: Suggest next action or summarize choice\n\n"

#     f"{history_text}\n\n"
#     f"CURRENT USER MESSAGE: {prompt}\n\n"
#     f"AVAILABLE PRODUCTS:\n{product_text}\n\n"
    
#     "**FINAL DIRECTIVE:** Be a helpful expert, not a chatty assistant. Provide value efficiently."
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