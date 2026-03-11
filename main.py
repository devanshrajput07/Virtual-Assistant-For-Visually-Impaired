"""
AURA — Voice-Controlled AI Assistant for Visually Impaired Navigation
Enhanced with 40+ Siri/Alexa-like voice commands
Refactored into a clean, modular architecture.
"""

from core.voice import talk, accept_command, greeting_message
from core.ai_chat import chat_with_groq
from commands.dispatcher import process_command

# ═══════════════════════════════
# MAIN LOOP
# ═══════════════════════════════
def run_voice_assistant():
    greeting_message()
    while True:
        cmd = accept_command()
        if not cmd:
            continue
        if any(word in cmd for word in ["exit", "quit", "stop", "shutdown"]):
            talk("Goodbye! Stay safe and have a wonderful day!")
            break
        
        process_command(cmd)

# ═══════════════════════════════
# WEB UI INTEGRATION
# ═══════════════════════════════
def handle_single_command():
    """Record one command and process intent"""
    cmd = accept_command()
    if not cmd:
        return {"command": None, "response": "I didn't hear anything."}
    
    # Capture talk output
    captured_text = []
    
    import core.voice as voice_module
    
    def mock_talk(text):
        captured_text.append(text)
    
    voice_module.set_talk_handler(mock_talk)
    
    try:
        process_command(cmd)
    finally:
        voice_module.set_talk_handler(None)
        
    return {
        "command": cmd,
        "lang_code": "en-US",
        "response": " ".join(captured_text) if captured_text else "Command processed."
    }

if __name__ == "__main__":
    run_voice_assistant()
