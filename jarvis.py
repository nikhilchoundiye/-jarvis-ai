import speech_recognition as sr
import webbrowser
import datetime
import os
import pyautogui
import requests
import tempfile
import json
import pygame
import threading
import edge_tts
import asyncio
from serpapi import GoogleSearch
from dotenv import load_dotenv
import os

load_dotenv()  # Load variables from .env

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_API_URL = "http://openrouter.ai/deepseek/deepseek-chat-v3.1:free/api"
DEEPSEEK_MODEL = "deepseek/deepseek-chat-v3.1:free"

SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")




# At the top of your jarvis.py
SERPAPI_KEY = SERPAPI_API_KEY





# ========== CONFIG ==========


LANGUAGES = {
    'english': 'en', 'hindi': 'hi', 'marathi': 'mr', 'spanish': 'es',
    'japanese': 'ja', 'russian': 'ru', 'chinese': 'zh-cn'
}

# Male voice mapping for Edge TTS
VOICE_MAPPING = {
    'en': 'en-GB-RyanNeural',    # British English male
    'hi': 'hi-IN-MadhurNeural',  # Hindi male
    'mr': 'mr-IN-ManoharNeural', # Marathi male
    'es': 'es-ES-AlvaroNeural',  # Spanish male
    'ja': 'ja-JP-KeitaNeural',   # Japanese male
    'ru': 'ru-RU-DmitryNeural',  # Russian male
    'zh-cn': 'zh-CN-YunxiNeural' # Chinese male
}

# ========== GLOBALS ==========

recognizer = sr.Recognizer()
current_lang = 'en'
stop_speaking_flag = False
speak_thread = None
is_speaking = False
speak_lock = threading.Lock()

# Initialize pygame mixer once
pygame.mixer.init()

# ========== SPEECH OUTPUT ==========

async def generate_voice(text, voice_name, output_file):
    communicate = edge_tts.Communicate(text=text, voice=voice_name)
    await communicate.save(output_file)

def speak(text, lang='en'):
    global stop_speaking_flag, is_speaking, speak_thread

    def speak_worker():
        global is_speaking
        try:
            is_speaking = True
            print(f"🗣️ Jarvis ({lang}): {text}")
            
            voice = VOICE_MAPPING.get(lang, 'en-GB-RyanNeural')
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
                mp3_path = fp.name
            
            # Run async function in a thread
            asyncio.run(generate_voice(text, voice, mp3_path))

            with speak_lock:
                pygame.mixer.music.load(mp3_path)
                pygame.mixer.music.play()

                while pygame.mixer.music.get_busy():
                    pass

                pygame.mixer.music.unload()
                os.remove(mp3_path)
                
        except Exception as e:
            print("❌ TTS Error:", e)
        finally:
            is_speaking = False

    if speak_thread and speak_thread.is_alive():
        pygame.mixer.music.stop()
        speak_thread.join()

    speak_thread = threading.Thread(target=speak_worker)
    speak_thread.start()

# ========== LISTENING ==========

def listen():
    global is_speaking
    if is_speaking:
        return ""

    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        print("🎙️ Listening...")
        try:
            audio = recognizer.listen(source, timeout=4)
            text = recognizer.recognize_google(audio).lower()
            print(f"👂 Heard: {text}")
            return text
        
        except sr.WaitTimeoutError:
             return ""
        except sr.UnknownValueError:
            return ""
        except sr.RequestError as e:
            print(f"❌ Google API Error: {e}")
            return ""







def search_google(query):
    """
    Searches Google using SerpAPI and returns the first result snippet.
    If no results found, returns a fallback message.
    """
    params = {
        "engine": "google",
        "q": query,
        "api_key": SERPAPI_KEY  # <-- Replace this with your SerpAPI key
    }

    try:
        search = GoogleSearch(params)
        results = search.get_dict()

        # Try to get the first organic result snippet
        snippet = results.get("organic_results", [{}])[0].get("snippet")
        if snippet:
            return snippet
        else:
            return "Sorry, I couldn't find anything on Google."
    except Exception as e:
        print("❌ Google Search Error:", e)
        return "Search failed due to an error."


def get_deepseek_response(prompt: str, query: str = None) -> str:
    try:
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": DEEPSEEK_MODEL,
            "input": prompt
        }
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        # Adjust depending on DeepSeek output format
        return data.get("output", "").strip()
    
    except Exception as e:
        print("DEBUG [DeepSeek Error]:", e)

        # If GPT fails and this was for intent classification, return fallback intent
        if query:
            # keyword-based fallback
            q = query.lower()
            if "time" in q:
                return "system:time"
            elif "chrome" in q:
                return "system:open:chrome"
            elif "notepad" in q:
                return "system:open:notepad"
            elif "vs code" in q:
                return "system:open:vs code"
            elif "screenshot" in q:
                return "system:screenshot"
            elif "shutdown" in q:
                return "system:shutdown"
            elif any(x in q for x in ["who", "what", "where", "search"]):
                return "search"
            else:
                return "chat"
        return ""  # final fallback


    

def smart_reply(query):
    try:
        # Ask LLM if it's a search query or chat
        intent = get_deepseek_response(
            f"Classify this request strictly as 'search' or 'chat': {query}",
            query=query
        )

        if "search" in intent.lower():
            return search_google(query)
        else:
            return get_deepseek_response(query, query=query)
    except Exception as e:
        print("❌ Smart Reply Error:", e)
        return "I couldn't process that."


def classify_command(query):
    instruction = f"""
    Classify the intent strictly using one label:
    system:time, system:open:chrome, system:open:notepad,
    system:open:vs code, system:screenshot, system:shutdown,
    search, chat
    Input: "{query}"
    Answer with ONLY the label, nothing else.
    """
    intent = get_deepseek_response(instruction, query=query).strip().lower()

    # ---------------- FALLBACK KEYWORD SCAN ----------------
    valid_labels = [
        "system:time", "system:open:chrome", "system:open:notepad",
        "system:open:vs code", "system:screenshot", "system:shutdown",
        "search", "chat"
    ]
    if intent not in valid_labels:
        q = query.lower()
        if "time" in q:
            intent = "system:time"
        elif "chrome" in q:
            intent = "system:open:chrome"
        elif "notepad" in q:
            intent = "system:open:notepad"
        elif "vs code" in q:
            intent = "system:open:vs code"
        elif "screenshot" in q:
            intent = "system:screenshot"
        elif "shutdown" in q:
            intent = "system:shutdown"
        elif any(x in q for x in ["who","what","where","search"]):
            intent = "search"
        else:
            intent = "chat"

    return intent



# ========== COMMAND HANDLER ==========

def execute_command(query, lang='en'):
    intent = classify_command(query).lower()
    print(f"🤖 Intent detected: {intent}")  # DEBUG


    if "system:time" in intent:
        speak(datetime.datetime.now().strftime("It's %I:%M %p"), lang)
        return

    if "system:open" in intent:
        if "chrome" in intent:
            os.system("start chrome")
            speak("Chrome is now open", lang)
        elif "notepad" in intent:
            os.system("start notepad")
            speak("Notepad launched", lang)
        elif "vs code" in intent:
            os.system("code")
            speak("Opening VS Code", lang)
        else:
            speak("I don't know that app", lang)
        return

    if "system:screenshot" in intent:
        pyautogui.screenshot().save("screenshot.png")
        speak("Screenshot taken.", lang)
        return

    if "system:shutdown" in intent:
        speak("Shutting down in 5 seconds!", lang)
        os.system("shutdown /s /t 5")
        return

    if "search" in intent:
        response = search_google(query)
        speak(response, lang)
        return

    if "chat" in intent:
        response = smart_reply(query)
        speak(response, lang)
        return



# ========== MAIN LOOP ==========

if __name__ == "__main__":
    speak("Jarvis is activated.", current_lang)

    while True:
        try:
            query = listen()
            if not query:
                continue

            if "stop" in query or "exit" in query:
                speak("Goodbye!", current_lang)
                break



            for lang in LANGUAGES:
                if f"respond in {lang}" in query:
                    current_lang = LANGUAGES[lang]
                    speak(f"Language switched to {lang}", current_lang)
                    break

            execute_command(query, current_lang)

        except KeyboardInterrupt:
            speak("Emergency shutdown.")
            break
        except Exception as e:
            print("❌ Critical Error:", e)
            speak("Something went wrong.")
