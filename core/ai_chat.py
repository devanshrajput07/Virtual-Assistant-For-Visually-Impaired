"""
core/ai_chat.py
Groq LLM interface with conversation memory stored in MongoDB Atlas.
Includes retry logic with exponential back-off.
"""

import logging
import time
import uuid
from groq import Groq
from config.settings import GROQ_KEY

logger = logging.getLogger("aura.ai_chat")

client = Groq(api_key=GROQ_KEY)

# In-memory conversation history (also persisted to MongoDB per session)
conversation_history: list[dict] = []
MAX_HISTORY = 12
SESSION_ID = str(uuid.uuid4())   # unique per process run

SYSTEM_PROMPT = (
    "You are AURA, a warm, friendly, and highly capable voice assistant designed "
    "specifically for visually impaired users. Keep all responses concise (2-3 sentences) "
    "since they will be spoken aloud. Be clear, natural, and never use markdown, "
    "bullet points, emojis, or special formatting. Always be calm and reassuring."
)


def _persist_history() -> None:
    """Save current conversation to MongoDB (best-effort)."""
    try:
        from core.db import save_conversation
        save_conversation(SESSION_ID, conversation_history)
    except Exception as exc:
        logger.debug("Could not persist conversation: %s", exc)


def chat_with_groq(prompt: str, retries: int = 3) -> str:
    """Send prompt to Groq with conversation memory and retry logic."""
    global conversation_history

    conversation_history.append({"role": "user", "content": prompt})

    # Trim history to prevent context overflow
    if len(conversation_history) > MAX_HISTORY:
        conversation_history = conversation_history[-MAX_HISTORY:]

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + conversation_history

    last_error = None
    for attempt in range(1, retries + 1):
        try:
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=messages,
                max_tokens=256,
                temperature=0.7,
            )
            reply = response.choices[0].message.content.strip()
            conversation_history.append({"role": "assistant", "content": reply})
            _persist_history()
            return reply
        except Exception as exc:
            last_error = exc
            wait = 2 ** (attempt - 1)  # exponential back-off: 1s, 2s, 4s
            logger.warning("Groq attempt %d/%d failed: %s — retrying in %ds", attempt, retries, exc, wait)
            time.sleep(wait)

    logger.error("All Groq retries exhausted. Last error: %s", last_error)
    return "Sorry, I couldn't reach the AI service right now. Please try again in a moment."


def get_conversation_history() -> list[dict]:
    return list(conversation_history)


def clear_conversation() -> None:
    global conversation_history
    conversation_history = []
    logger.info("Conversation history cleared.")
