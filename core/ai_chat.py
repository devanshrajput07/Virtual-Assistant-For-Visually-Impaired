from groq import Groq
from config.settings import GROQ_KEY

client = Groq(api_key=GROQ_KEY)

conversation_history = []
MAX_HISTORY = 12

def chat_with_groq(prompt):
    """Send prompt to Groq with conversation memory"""
    global conversation_history
    conversation_history.append({"role": "user", "content": prompt})
    
    if len(conversation_history) > MAX_HISTORY:
        conversation_history = conversation_history[-MAX_HISTORY:]
        
    try:
        messages = [
            {"role": "system", "content": (
                "You are VAVI, a smart and friendly voice assistant for the visually impaired. "
                "Keep responses concise (2-3 sentences max) since they will be spoken aloud. "
                "Be warm, helpful, and natural. Never use markdown, bullet points, or special formatting."
            )}
        ] + conversation_history
        
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
        )
        
        reply = response.choices[0].message.content.strip()
        conversation_history.append({"role": "assistant", "content": reply})
        return reply
    except Exception as e:
        return f"Sorry, I couldn't reach the AI service. Error: {e}"
