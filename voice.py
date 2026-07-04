import sys
import platform
import queue
import tempfile
import threading
import os
import speech_recognition as sr
import pyttsx3


class VoiceAssistant:
    def __init__(self):
        self._is_windows = platform.system() == "Windows"
        self._is_macos = platform.system() == "Darwin"
        self._is_linux = platform.system() == "Linux"
        self._recording = False
        self._engine = None
        self._audio_queue = queue.Queue()
        self._recognizer = sr.Recognizer()
        self._mic = None

        if self._is_windows or self._is_linux:
            try:
                self._engine = pyttsx3.init()
            except Exception:
                self._engine = None
        elif self._is_macos:
            try:
                self._engine = pyttsx3.init()
            except Exception:
                self._engine = None

        if self._engine:
            voices = self._engine.getProperty("voices")
            for voice in voices:
                if "female" in voice.name.lower() or "zira" in voice.name.lower() or "samantha" in voice.name.lower():
                    self._engine.setProperty("voice", voice.id)
                    break

    def toggle_record(self) -> bool:
        self._recording = not self._recording
        if self._recording:
            threading.Thread(target=self._record, daemon=True).start()
        return self._recording

    def _record(self):
        try:
            with sr.Microphone() as source:
                self._recognizer.adjust_for_ambient_noise(source, duration=0.3)
                while self._recording:
                    try:
                        audio = self._recognizer.listen(source, timeout=2, phrase_time_limit=5)
                        text = self._recognizer.recognize_google(audio)
                        self._audio_queue.put(("final", text))
                    except sr.WaitTimeoutError:
                        pass
                    except sr.UnknownValueError:
                        pass
                    except Exception as e:
                        print(f"[Voice] Error: {e}")
                        self._recording = False
                        break
        except Exception as e:
            print(f"[Voice] Microphone error: {e}")
            self._recording = False

    def listen(self) -> str:
        try:
            with sr.Microphone() as source:
                self._recognizer.adjust_for_ambient_noise(source, duration=0.3)
                audio = self._recognizer.listen(source, timeout=10, phrase_time_limit=30)
                text = self._recognizer.recognize_google(audio)
                return text.lower()
        except Exception:
            return ""

    def speak(self, text: str):
        if not self._engine:
            return
        try:
            self._engine.say(text)
            self._engine.runAndWait()
        except Exception:
            pass

    def stop(self):
        self._recording = False
        if self._engine:
            try:
                self._engine.stop()
            except Exception:
                pass
