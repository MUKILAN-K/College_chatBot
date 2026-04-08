import speech_recognition as sr
from groq import Groq
import subprocess
import pygame
import time
import asyncio
import edge_tts

# Initialize pygame mixer
pygame.mixer.init()

# Initialize pygame mixer
pygame.mixer.init()

# 🔑 ADD YOUR API KEY HERE
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Load college data
with open("college_data.txt", "r", encoding="utf-8") as f:
    college_data = f.read()

recognizer = sr.Recognizer()
mic = sr.Microphone()

cooldown_until = 0
last_answer = ""

print("🤖 Campus Thozhan (FAST AI) READY")
print("Say 'exit' to stop\n")


def speak(text):
    global cooldown_until

    print("🔊 Speaking...\n")

    # Generate speech using edge-tts library (Faster than subprocess)
    async def generate_speech():
        communicate = edge_tts.Communicate(text, "en-US-EmmaMultilingualNeural")
        await communicate.save("voice.mp3")

    try:
        asyncio.run(generate_speech())
    except Exception as e:
        print(f"❌ Voice generation failed: {e}")
        return

    # Play using pygame
    try:
        pygame.mixer.music.load("voice.mp3")
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        pygame.mixer.music.unload()
    except Exception as e:
        print(f"❌ Playback failed: {e}")

    cooldown_until = time.time() + 3


while True:

    if time.time() < cooldown_until:
        continue

    try:
        print("🎤 Listening...")

        with mic as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.listen(
                source,
                timeout=5,              # wait max 5 sec to start speaking
                phrase_time_limit=5     # max speaking duration
            )

        text = recognizer.recognize_google(audio).lower()

        print("🗣️ You:", text)

        # prevent self-loop
        if last_answer != "" and last_answer.lower() in text:
            print("⚠️ Ignored self voice")
            continue

        if "exit" in text:
            speak("Goodbye")
            break

        print("🧠 Thinking...\n")

        prompt = f"""
You are Campus Thozhan, a college assistant.

STRICT RULES:
- Answer ONLY from given data
- Answer in ONE short sentence
- No explanation
- No extra content
- If not found, say "Please say the question again" or "I don't know"

DATA:
{college_data}

QUESTION:
{text}

ANSWER:
"""

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        answer = response.choices[0].message.content.strip()

        # clean output
        answer = answer.split("\n")[0]

        # validation
        # Check if ANY important word exists in data
        valid = False

        for word in answer.lower().split():
            if word in college_data.lower():
                valid = True
                break

        if not valid:
            answer = "I don't know"

        print("🤖 Robot:", answer)

        last_answer = answer

        speak(answer)

    except sr.UnknownValueError:
        print("❌ Could not understand")

    except Exception as e:
        print("Error:", e)