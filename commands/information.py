import datetime
import requests
import wikipedia
import urllib.parse
from core.voice import talk, accept_command_text
from core.ai_chat import chat_with_groq
from config.settings import NEWS_API_KEY

def command_get_current_time():
    time_now = datetime.datetime.now().strftime("%I:%M %p")
    talk(f"The time is {time_now}")

def command_get_date():
    today = datetime.datetime.now()
    date_str = today.strftime("%A, %B %d, %Y")
    talk(f"Today is {date_str}")

def command_get_weather(command):
    """Get weather using Open-Meteo API"""
    city = ""
    for keyword in ["weather in", "weather of", "weather for", "weather at"]:
        if keyword in command:
            city = command.split(keyword)[-1].strip()
            break
    if not city:
        try:
            ip_data = requests.get("http://ip-api.com/json/", timeout=5).json()
            city = ip_data.get("city", "Delhi")
        except:
            city = "Delhi"

    try:
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1"
        geo_data = requests.get(geo_url, timeout=10).json()
        if "results" not in geo_data:
            talk(f"Sorry, I couldn't find the location {city}.")
            return
            
        lat = geo_data["results"][0]["latitude"]
        lon = geo_data["results"][0]["longitude"]
        place = geo_data["results"][0]["name"]

        weather_url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}"
            f"&current_weather=true"
            f"&daily=temperature_2m_max,temperature_2m_min"
            f"&timezone=auto"
        )
        weather_data = requests.get(weather_url, timeout=10).json()
        current = weather_data["current_weather"]
        temp = current["temperature"]
        windspeed = current["windspeed"]

        weather_codes = {
            0: "clear sky", 1: "mainly clear", 2: "partly cloudy", 3: "overcast",
            45: "foggy", 48: "foggy", 51: "light drizzle", 53: "drizzle",
            55: "heavy drizzle", 61: "light rain", 63: "moderate rain",
            65: "heavy rain", 71: "light snow", 73: "snow", 75: "heavy snow",
            80: "rain showers", 81: "moderate rain showers", 82: "heavy rain showers",
            95: "thunderstorm", 96: "thunderstorm with hail", 99: "severe thunderstorm",
        }
        condition = weather_codes.get(current.get("weathercode", 0), "unknown conditions")

        daily = weather_data.get("daily", {})
        high = daily.get("temperature_2m_max", [None])[0]
        low = daily.get("temperature_2m_min", [None])[0]

        msg = f"Weather in {place}: Currently {temp} degrees Celsius with {condition}. Wind speed is {windspeed} kilometers per hour."
        if high and low:
            msg += f" Today's high is {high} and low is {low} degrees."
        talk(msg)
    except Exception as e:
        talk(f"Sorry, I couldn't fetch the weather. {e}")

def command_search_wikipedia(command):
    for prefix in ["who is", "what is", "tell me about", "wikipedia"]:
        if prefix in command:
            query = command.split(prefix)[-1].strip()
            break
    else:
        query = command
    try:
        info = wikipedia.summary(query, sentences=2)
        talk(info)
    except Exception as e:
        talk(f"Error searching Wikipedia. {e}")

def command_tell_news():
    url = "https://newsapi.org/v2/top-headlines"
    params = {"country": "in", "apiKey": NEWS_API_KEY}
    try:
        res = requests.get(url, params=params, timeout=10)
        data = res.json()
        if "articles" not in data or not data["articles"]:
            talk("No news available at the moment.")
            return
        articles = data["articles"][:5]
        talk(f"Here are the top {len(articles)} headlines:")
        for idx, article in enumerate(articles, start=1):
            title = article.get("title", "No title available")
            talk(title)
    except Exception:
        talk("Sorry, I could not fetch the news.")

def command_translate(command):
    """Translate text using Groq AI"""
    prompt = f"Translate the following and give ONLY the translation, nothing else: {command}"
    reply = chat_with_groq(prompt)
    talk(reply)

def command_define_word(command):
    """Define a word using Groq AI"""
    word = command
    for keyword in ["define", "meaning of", "what does", "mean", "definition of", "the word"]:
        word = word.replace(keyword, "")
    word = word.strip()
    if not word:
        talk("What word should I define?")
        word = accept_command_text()
        if not word: return
    prompt = f"Define the word '{word}' in 1-2 simple sentences. Include pronunciation guide."
    reply = chat_with_groq(prompt)
    talk(reply)

def command_daily_briefing():
    """Morning briefing: time, weather, and top 3 news"""
    talk("Here's your daily briefing.")
    
    time_now = datetime.datetime.now().strftime("%I:%M %p")
    today = datetime.datetime.now().strftime("%A, %B %d")
    talk(f"It's {time_now} on {today}.")
    
    try:
        ip_data = requests.get("http://ip-api.com/json/", timeout=5).json()
        city = ip_data.get("city", "Delhi")
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1"
        geo_data = requests.get(geo_url, timeout=5).json()
        if "results" in geo_data:
            lat = geo_data["results"][0]["latitude"]
            lon = geo_data["results"][0]["longitude"]
            weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&timezone=auto"
            weather = requests.get(weather_url, timeout=5).json()["current_weather"]
            talk(f"Weather in {city}: {weather['temperature']} degrees with wind at {weather['windspeed']} km/h.")
    except:
        talk("Couldn't fetch weather right now.")
    
    try:
        res = requests.get("https://newsapi.org/v2/top-headlines", params={"country": "in", "apiKey": NEWS_API_KEY}, timeout=10)
        articles = res.json().get("articles", [])[:3]
        if articles:
            talk("Top headlines:")
            for a in articles:
                talk(a.get("title", ""))
    except:
        talk("Couldn't fetch news right now.")
    
    talk("That's your briefing. Have a great day!")
