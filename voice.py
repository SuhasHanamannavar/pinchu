import sys
import platform
import queue
import tempfile
import threading
import os
import speech_recognition as sr
import pyttsx3
from PyQt5.QtCore import QObject, pyqtSignal


class VoiceEngine(QObject):
    text_recognized = pyqtSignal(str)
    listening_started = pyqtSignal()
    listening_stopped = pyqtSignal()
    speaking_started = pyqtSignal()
    speaking_finished = pyqtSignal()
    error_occurred = pyqtSignal(str)
    status_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_windows = platform.system() == "Windows"
        self._is_macos = platform.system() == "Darwin"
        self._continuous = False
        self._listening = False
        self._speaking = False
        self._engine = None
        self._recognizer = sr.Recognizer()
        self._listen_thread = None
        self._tts_thread = None
        self._tts_queue = queue.Queue()

        try:
            self._engine = pyttsx3.init()
            voices = self._engine.getProperty("voices")
            for voice in voices:
                if "female" in voice.name.lower() or "zira" in voice.name.lower() or "samantha" in voice.name.lower():
                    self._engine.setProperty("voice", voice.id)
                    break
        except Exception:
            self._engine = None

    @property
    def is_continuous(self):
        return self._continuous

    @property
    def is_listening(self):
        return self._listening

    @property
    def is_speaking(self):
        return self._speaking

    def start_continuous(self):
        if self._continuous:
            return
        self._continuous = True
        self._listen_thread = threading.Thread(target=self._continuous_listen, daemon=True)
        self._listen_thread.start()
        self.status_changed.emit("Listening...")

    def stop_continuous(self):
        self._continuous = False
        self._listening = False
        self.listening_stopped.emit()
        self.status_changed.emit("Stopped")

    def listen_once(self):
        threading.Thread(target=self._listen_once, daemon=True).start()

    def start_tts_thread(self):
        self._tts_thread = threading.Thread(target=self._tts_worker, daemon=True)
        self._tts_thread.start()

    def speak(self, text):
        self._tts_queue.put(text)

    def _continuous_listen(self):
        try:
            with sr.Microphone() as source:
                self._recognizer.adjust_for_ambient_noise(source, duration=0.3)
                self._listening = True
                self.listening_started.emit()
                while self._continuous:
                    try:
                        audio = self._recognizer.listen(source, timeout=2, phrase_time_limit=5)
                        text = self._recognizer.recognize_google(audio)
                        self.text_recognized.emit(text)
                    except sr.WaitTimeoutError:
                        pass
                    except sr.UnknownValueError:
                        pass
                    except Exception as e:
                        self.error_occurred.emit(str(e))
                        break
                self._listening = False
                self.listening_stopped.emit()
        except Exception as e:
            self._listening = False
            self.error_occurred.emit(f"Microphone error: {e}")
            self.listening_stopped.emit()

    def _listen_once(self):
        try:
            with sr.Microphone() as source:
                self._recognizer.adjust_for_ambient_noise(source, duration=0.3)
                self._listening = True
                self.listening_started.emit()
                audio = self._recognizer.listen(source, timeout=10, phrase_time_limit=30)
                text = self._recognizer.recognize_google(audio)
                self._listening = False
                self.listening_stopped.emit()
                self.text_recognized.emit(text)
        except Exception as e:
            self._listening = False
            self.error_occurred.emit(str(e))
            self.listening_stopped.emit()

    def _tts_worker(self):
        while True:
            try:
                text = self._tts_queue.get()
                if self._engine:
                    self._speaking = True
                    self.speaking_started.emit()
                    self._engine.say(text)
                    self._engine.runAndWait()
                    self._speaking = False
                    self.speaking_finished.emit()
            except Exception:
                self._speaking = False

    def stop(self):
        self._continuous = False
        self._listening = False
        if self._engine:
            try:
                self._engine.stop()
            except Exception:
                pass
