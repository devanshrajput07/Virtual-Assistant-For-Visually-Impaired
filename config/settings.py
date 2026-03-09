import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
GROQ_KEY = os.getenv("GROQ_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

if not GROQ_KEY:
    raise EnvironmentError("GROQ_API_KEY missing in .env file!")

# Maps & Dictionaries
APP_MAP = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "paint": "mspaint.exe",
    "file explorer": "explorer.exe",
    "task manager": "taskmgr.exe",
    "command prompt": "cmd.exe",
    "settings": "ms-settings:",
    "word": "winword.exe",
    "excel": "excel.exe",
    "powerpoint": "powerpnt.exe",
    "snipping tool": "snippingtool.exe",
}

WEBSITE_MAP = {
    "youtube": "https://www.youtube.com",
    "google": "https://www.google.com",
    "gmail": "https://mail.google.com",
    "github": "https://www.github.com",
    "whatsapp": "https://web.whatsapp.com",
    "instagram": "https://www.instagram.com",
    "facebook": "https://www.facebook.com",
    "twitter": "https://www.twitter.com",
    "x": "https://www.x.com",
    "linkedin": "https://www.linkedin.com",
    "reddit": "https://www.reddit.com",
    "amazon": "https://www.amazon.in",
    "flipkart": "https://www.flipkart.com",
    "netflix": "https://www.netflix.com",
    "spotify": "https://open.spotify.com",
    "chatgpt": "https://chat.openai.com",
    "stack overflow": "https://stackoverflow.com",
    "wikipedia": "https://www.wikipedia.org",
    "maps": "https://maps.google.com",
    "google maps": "https://maps.google.com",
    "drive": "https://drive.google.com",
    "google drive": "https://drive.google.com",
}

SMALL_TALK = {
    "how are you": "I'm doing great, thank you for asking! How can I help you?",
    "what is your name": "I am VAVI, your voice assistant for visually impaired navigation.",
    "who made you": "I was created as a final year project to help visually impaired people navigate the world.",
    "who created you": "I was created as a final year project to help visually impaired people navigate the world.",
    "thank you": "You're welcome! Glad I could help.",
    "thanks": "You're welcome! Let me know if you need anything else.",
    "good morning": "Good morning! Hope you have a wonderful day ahead.",
    "good afternoon": "Good afternoon! How can I help you?",
    "good evening": "Good evening! What can I do for you?",
    "good night": "Good night! Sleep well and stay safe.",
    "i love you": "That's sweet! I'm here to help you anytime.",
    "hello": "Hello! How can I assist you today?",
    "hi": "Hi there! What can I do for you?",
    "bye": "Goodbye! Have a nice day!",
    "you are amazing": "Thank you! You're pretty amazing too!",
    "you are smart": "Thank you! I try my best to help.",
}
