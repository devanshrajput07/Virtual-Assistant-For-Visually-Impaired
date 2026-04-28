import datetime
import logging
import requests
import wikipedia
from core.voice import talk, accept_command_text
from core.ai_chat import chat_with_groq
from config.settings import NEWS_API_KEY

logger = logging.getLogger("aura.commands.information")

def command_get_current_time() -> None:
    t = datetime.datetime.now().strftime("%I:%M %p")
    talk(f"The current time is {t}.")

def command_get_date() -> None:
    d = datetime.datetime.now().strftime("%A, %B %d, %Y")
    talk(f"Today is {d}.")

def command_get_weather(command: str, gps_lat: float = None, gps_lon: float = None) -> None:
    city = ""
    for kw in ["weather in", "weather of", "weather for", "weather at", "temperature in"]:
        if kw in command:
            city = command.split(kw)[-1].strip()
            break

    if not city:
        if gps_lat and gps_lon:
            try:
                headers = {"User-Agent": "AURA-VoiceAssistant/1.0"}
                rev_url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={gps_lat}&lon={gps_lon}"
                rev_data = requests.get(rev_url, headers=headers, timeout=5).json()
                addr = rev_data.get("address", {})
                city = addr.get("city", addr.get("town", addr.get("village", addr.get("county", "your location"))))
            except Exception:
                city = "your location"
        else:
            try:
                ip_data = requests.get("http://ip-api.com/json/", timeout=5).json()
                city = ip_data.get("city", "Delhi")
            except Exception:
                city = "Delhi"

    try:
        from core.db import cache_get, cache_set
        cache_key = f"weather_{city.lower()}"
        cached = cache_get(cache_key)
        if cached:
            talk(cached)
            logger.debug("Weather served from cache for %s.", city)
            return
    except Exception:
        cache_key = None

    try:
        if gps_lat and gps_lon and ("weather in" not in command and "weather of" not in command):
            lat = gps_lat
            lon = gps_lon
            place = city
        else:
            geo = requests.get(
                f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1", timeout=10
            ).json()
            if "results" not in geo or not geo["results"]:
                talk(f"Sorry, I couldn't find the location {city}.")
                return

            lat = geo["results"][0]["latitude"]
            lon = geo["results"][0]["longitude"]
            place = geo["results"][0]["name"]

        weather_data = requests.get(
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}&current_weather=true"
            f"&daily=temperature_2m_max,temperature_2m_min&timezone=auto",
            timeout=10,
        ).json()

        current = weather_data["current_weather"]
        temp = current["temperature"]
        wind = current["windspeed"]
        code = current.get("weathercode", 0)

        WEATHER_CODES = {
            0: "clear sky", 1: "mainly clear", 2: "partly cloudy", 3: "overcast",
            45: "foggy", 48: "foggy", 51: "light drizzle", 53: "drizzle",
            55: "heavy drizzle", 61: "light rain", 63: "moderate rain",
            65: "heavy rain", 71: "light snow", 73: "snow", 75: "heavy snow",
            80: "rain showers", 81: "moderate rain showers", 82: "heavy rain showers",
            95: "thunderstorm", 96: "thunderstorm with hail", 99: "severe thunderstorm",
        }
        condition = WEATHER_CODES.get(code, "varied conditions")

        daily = weather_data.get("daily", {})
        high = daily.get("temperature_2m_max", [None])[0]
        low = daily.get("temperature_2m_min", [None])[0]

        msg = (
            f"Weather in {place}: currently {temp} degrees Celsius with {condition}. "
            f"Wind speed is {wind} kilometres per hour."
        )
        if high and low:
            msg += f" Today's high is {high} and low is {low} degrees."

        talk(msg)

        try:
            if cache_key:
                cache_set(cache_key, msg, ttl_seconds=1800)
        except Exception:
            pass

    except Exception as exc:
        logger.warning("Weather fetch failed: %s", exc)
        talk("Sorry, I couldn't fetch the weather right now.")

def command_search_wikipedia(command: str) -> None:
    query = command
    prefixes = ["search on wikipedia", "search for", "who is", "what is", "tell me about", "wikipedia"]
    for prefix in prefixes:
        if prefix in command:
            query = command.split(prefix)[-1].strip()
            break
    
    if not query:
        talk("What would you like me to search for on Wikipedia?")
        query = accept_command_text()
        if not query:
            return

    if len(query.split()) > 3:
        try:
            prompt = (
                f"Extract the most relevant single Wikipedia search term from this phrase: '{query}'. "
            )
            refined = chat_with_groq(prompt).strip().strip('"').strip("'")
            if refined:
                logger.debug("Refined Wikipedia query: '%s' -> '%s'", query, refined)
                query = refined
        except Exception:
            pass

    try:
        info = wikipedia.summary(query, sentences=2, auto_suggest=True)
        talk(info)
    except wikipedia.exceptions.DisambiguationError as e:
        talk(f"That term is ambiguous. Did you mean {e.options[0]}?")
    except wikipedia.exceptions.PageError:
        talk(f"I couldn't find a Wikipedia page for {query}.")
    except Exception as exc:
        logger.warning("Wikipedia search failed for '%s': %s", query, exc)
        talk("Sorry, I'm having trouble connecting to Wikipedia right now.")

def command_tell_news() -> None:
    if not NEWS_API_KEY:
        talk("News is not available because the news API key is not configured.")
        return

    try:
        from core.db import cache_get, cache_set
        cached = cache_get("news_headlines")
        if cached:
            talk("Here are today's top headlines.")
            for h in cached:
                talk(h)
            return
    except Exception:
        pass

    try:
        res = requests.get(
            "https://newsapi.org/v2/top-headlines",
            params={"country": "in", "apiKey": NEWS_API_KEY, "pageSize": 5},
            timeout=10,
        )
        articles = res.json().get("articles", [])
        
        if not articles:
            logger.debug("Indian country feed empty, searching within top Indian domains instead.")
            indian_domains = "ndtv.com,indiatimes.com,thehindu.com,indianexpress.com,hindustantimes.com"
            res = requests.get(
                "https://newsapi.org/v2/everything",
                params={"domains": indian_domains, "language": "en", "sortBy": "publishedAt", "apiKey": NEWS_API_KEY, "pageSize": 5},
                timeout=10,
            )
            articles = res.json().get("articles", [])

        if not articles:
            talk("No news available at the moment.")
            return

        headlines = [a.get("title", "") for a in articles if a.get("title")][:5]
        talk(f"Here are today's top {len(headlines)} headlines.")
        for h in headlines:
            talk(h)

        try:
            cache_set("news_headlines", headlines, ttl_seconds=1800)
        except Exception:
            pass

    except Exception as exc:
        logger.warning("News fetch failed: %s", exc)
        talk("Sorry, I couldn't fetch the news right now.")

def command_translate(command: str) -> None:
    prompt = f"Translate the following phrase and give ONLY the translation, no explanation: {command}"
    reply = chat_with_groq(prompt)
    talk(reply)

def command_define_word(command: str) -> None:
    word = command
    for kw in ["define", "meaning of", "what does", "mean", "definition of", "the word"]:
        word = word.replace(kw, "")
    word = word.strip()

    if not word:
        talk("Please specify the word you would like me to define. For example, say: define apple.")
        return

    prompt = f"Define the word '{word}' in one or two simple sentences suitable for being spoken aloud. Include pronunciation if helpful."
    reply = chat_with_groq(prompt)
    talk(reply)

def command_daily_briefing(gps_lat: float = None, gps_lon: float = None) -> None:
    talk("Good morning! Here is your daily briefing.")
    time_now = datetime.datetime.now().strftime("%I:%M %p")
    today = datetime.datetime.now().strftime("%A, %B %d")
    talk(f"It is {time_now} on {today}.")

    try:
        command_get_weather("weather", gps_lat=gps_lat, gps_lon=gps_lon)
    except Exception as exc:
        logger.debug("Briefing weather skipped: %s", exc)
        talk("Couldn't fetch weather for the briefing.")

    if NEWS_API_KEY:
        try:
            res = requests.get(
                "https://newsapi.org/v2/top-headlines",
                params={"country": "in", "apiKey": NEWS_API_KEY, "pageSize": 3},
                timeout=10,
            )
            articles = res.json().get("articles", [])
            
            if not articles:
                logger.debug("Indian briefing feed empty, searching top Indian domains.")
                indian_domains = "ndtv.com,indiatimes.com,thehindu.com,indianexpress.com,hindustantimes.com"
                res = requests.get(
                    "https://newsapi.org/v2/everything",
                    params={"domains": indian_domains, "language": "en", "sortBy": "publishedAt", "apiKey": NEWS_API_KEY, "pageSize": 3},
                    timeout=10,
                )
                articles = res.json().get("articles", [])

            if articles:
                talk("Top three headlines:")
                for a in articles:
                    talk(a.get("title", ""))
        except Exception as exc:
            logger.debug("Briefing news skipped: %s", exc)
            talk("News is unavailable at the moment.")

    talk("That's your briefing. Have a wonderful and safe day!")
