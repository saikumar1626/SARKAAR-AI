import speech_recognition as sr
import pyttsx3
import datetime
import webbrowser
import os
import time
import re
from openai import OpenAI


class JarvisAssistant:
    def __init__(self):
        """Initialize JARVIS-style AI assistant (OpenAI-powered)"""

        # ===============================
        # Speech Recognition
        # ===============================
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()

        # ===============================
        # Text-to-Speech (JARVIS voice)
        # ===============================
        self.engine = pyttsx3.init()
        voices = self.engine.getProperty("voices")
        self.engine.setProperty("voice", voices[0].id)  # male voice
        self.engine.setProperty("rate", 175)
        self.engine.setProperty("volume", 1.0)

        # ===============================
        # OpenAI Client (NO API KEY HERE)
        # ===============================
        self.client = OpenAI()

        # ===============================
        # Conversation Memory
        # ===============================
        self.conversation_history = []

        # ===============================
        # JARVIS Personality
        # ===============================
        self.system_prompt = (
            "You are JARVIS, an advanced AI assistant inspired by Tony Stark's AI.\n"
            "Always address the user as 'Sir'.\n"
            "Be professional, confident, slightly witty, and efficient.\n"
            "Use clear, concise responses.\n"
            "Acknowledge commands with phrases like 'Certainly, Sir' or 'Right away, Sir'."
        )

        print("🤖 JARVIS initialized")
        self.speak("Good day, Sir. JARVIS is online and ready.")

    # =====================================================

    def speak(self, text: str):
        """Convert text to speech"""
        print(f"\n🤖 JARVIS: {text}\n")
        clean = re.sub(r"[`*_#]", "", text)
        self.engine.say(clean)
        self.engine.runAndWait()

    # =====================================================

    def listen(self):
        """Listen for voice input"""
        with self.microphone as source:
            print("🎤 Listening, Sir...")
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)

            try:
                audio = self.recognizer.listen(
                    source, timeout=5, phrase_time_limit=15
                )
                print("⚙️ Processing...")
                text = self.recognizer.recognize_google(audio)
                print(f"📝 You said: {text}")
                return text

            except sr.WaitTimeoutError:
                return None
            except sr.UnknownValueError:
                self.speak("I did not catch that, Sir. Please repeat.")
                return None
            except sr.RequestError:
                self.speak("Speech service is unavailable, Sir.")
                return None

    # =====================================================

    def call_openai(self, user_message: str) -> str:
        """Call OpenAI for intelligent response"""

        self.conversation_history.append(
            {"role": "user", "content": user_message}
        )

        messages = [
            {"role": "system", "content": self.system_prompt},
            *self.conversation_history[-10:],  # keep memory small
        ]

        try:
            print("🧠 Thinking...")
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=messages,
                temperature=0.4,
            )

            answer = response.choices[0].message.content

            self.conversation_history.append(
                {"role": "assistant", "content": answer}
            )

            return answer

        except Exception as e:
            print(f"❌ OpenAI error: {e}")
            return "I am experiencing a systems issue, Sir."

    # =====================================================

    def execute_command(self, command: str, ai_response: str):
        """Execute system or browser commands"""

        cmd = command.lower()

        if "open notepad" in cmd:
            os.system("notepad")

        elif "open calculator" in cmd:
            os.system("calc")

        elif "open command prompt" in cmd or "open cmd" in cmd:
            os.system("start cmd")

        elif "search for" in cmd or "google" in cmd:
            query = cmd.replace("search for", "").replace("google", "").strip()
            if query:
                webbrowser.open(
                    f"https://www.google.com/search?q={query}"
                )

        elif "show images of" in cmd or "images of" in cmd:
            query = cmd.replace("images of", "").replace("show images of", "").strip()
            if query:
                webbrowser.open(
                    f"https://www.google.com/search?q={query}&tbm=isch"
                )

        # Open first URL mentioned by AI
        urls = re.findall(r"https?://\S+", ai_response)
        if urls:
            webbrowser.open(urls[0])

    # =====================================================

    def process_command(self, command: str) -> bool:
        """Main decision logic"""

        if command is None:
            return True

        cmd = command.lower()

        if any(x in cmd for x in ["exit", "quit", "goodbye jarvis", "shut down"]):
            self.speak("It has been a pleasure serving you, Sir.")
            return False

        if "time" in cmd:
            now = datetime.datetime.now().strftime("%I:%M %p")
            self.speak(f"The time is {now}, Sir.")
            return True

        if "date" in cmd:
            today = datetime.datetime.now().strftime("%A, %B %d, %Y")
            self.speak(f"Today is {today}, Sir.")
            return True

        # AI-powered response
        ai_response = self.call_openai(command)
        self.speak(ai_response)
        self.execute_command(command, ai_response)
        return True

    # =====================================================

    def run(self):
        """Main loop"""
        while True:
            try:
                command = self.listen()
                if command:
                    if not self.process_command(command):
                        break
                time.sleep(0.3)

            except KeyboardInterrupt:
                self.speak("Shutting down. Until next time, Sir.")
                break
            except Exception as e:
                print(f"❌ System error: {e}")
                time.sleep(1)


# =========================================================
# ENTRY POINT
# =========================================================

def main():
    print("=" * 70)
    print("           J.A.R.V.I.S  –  Voice AI Assistant")
    print("=" * 70)

    try:
        jarvis = JarvisAssistant()
        jarvis.run()
    except Exception as e:
        print(f"❌ Critical error: {e}")


if __name__ == "__main__":
    main()
