from core.voice import talk
from core.ai_chat import chat_with_groq, conversation_history

CONTEXT_TRIGGERS = [
    "tell me more", "more about that", "what about that",
    "remind me about that", "set a reminder for that",
    "explain that", "repeat that", "what did you say",
    "can you elaborate", "go deeper", "expand on that",
]

def is_context_command(command):
    return any(trigger in command for trigger in CONTEXT_TRIGGERS)

def command_smart_context(command):
    if not conversation_history:
        talk("We haven't discussed anything yet. Ask me something first!")
        return

    last_topic = None
    for msg in reversed(conversation_history):
        if msg["role"] == "assistant" and len(msg["content"]) > 20:
            last_topic = msg["content"]
            break

    if not last_topic:
        talk("I'm not sure what you're referring to. Could you be more specific?")
        return

    if "remind" in command:
        prompt = (
            f"The user just said: '{command}'. The last topic discussed was: '{last_topic[:200]}'. "
            f"Extract what they want to be reminded about and respond with ONLY a short confirmation "
            f"like 'I'll remind you to [action]'. Keep it under 15 words."
        )
    elif "repeat" in command or "what did you say" in command:
        talk(last_topic)
        return
    else:
        prompt = (
            f"The user said: '{command}'. The previous context was: '{last_topic[:300]}'. "
            f"Provide more detail or elaboration on that topic. Keep it concise (2-3 sentences), "
            f"spoken-aloud friendly. No markdown."
        )

    reply = chat_with_groq(prompt)
    talk(reply)
