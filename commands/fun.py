import requests
import random
from core.voice import talk, accept_command_text

QUOTES = [
    "Believe you can and you're halfway there.",
    "The only way to do great work is to love what you do.",
    "It does not matter how slowly you go as long as you do not stop.",
    "Success is not final, failure is not fatal, it is the courage to continue that counts.",
    "The future belongs to those who believe in the beauty of their dreams.",
    "You are never too old to set another goal or to dream a new dream.",
    "In the middle of every difficulty lies opportunity.",
    "Don't watch the clock, do what it does. Keep going.",
    "Everything you've ever wanted is on the other side of fear.",
    "Hardships often prepare ordinary people for an extraordinary destiny.",
]

def command_tell_joke():
    try:
        res = requests.get("https://icanhazdadjoke.com/", headers={"Accept": "application/json"}, timeout=5)
        joke = res.json()["joke"]
        talk(joke)
    except:
        jokes = [
            "Why don't scientists trust atoms? Because they make up everything!",
            "What do you call a fake noodle? An impasta!",
            "Why did the scarecrow win an award? He was outstanding in his field!",
        ]
        talk(random.choice(jokes))

def command_motivational_quote():
    talk(random.choice(QUOTES))

def command_flip_coin():
    result = random.choice(["heads", "tails"])
    talk(f"I flipped a coin and got {result}!")

def command_roll_dice():
    result = random.randint(1, 6)
    talk(f"I rolled a {result}!")

def command_spell_word(command):
    word = command.replace("spell", "").replace("how do you spell", "").strip()
    if not word:
        talk("What word should I spell?")
        word = accept_command_text()
        if not word: return
    talk(f"{word} is spelled:")
    spelled = ", ".join(letter for letter in word.upper() if letter != " ")
    talk(spelled)
