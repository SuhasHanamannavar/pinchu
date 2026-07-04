import threading
import queue
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

    def __init__(self):
        super().__init__()
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 1.0
        self.microphone = sr.Microphone()

        self._is_listening = False
        self._is_speaking = False
        self._continuous = False
        self._thread = None
        self._tts_thread = None
        self._tts_engine = None
        self._tts_queue = queue.Queue()
        self._voice_muted = False

        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)

    @property
    def is_listening(self):
        return self._is_listening

    @property
    def is_speaking(self):
        return self._is_speaking

    @property
    def is_continuous(self):
        return self._continuous

    def start_continuous(self):
        if self._is_listening:
            return
        self._continuous = True
        self._is_listening = True
        self.listening_started.emit()
        self.status_changed.emit("Listening...")
        self._thread = threading.Thread(target=self._continuous_loop, daemon=True)
        self._thread.start()

    def stop_continuous(self):
        self._continuous = False
        self._is_listening = False
        self.listening_stopped.emit()
        self.status_changed.emit("Paused")

    def toggle_continuous(self):
        if self._continuous:
            self.stop_continuous()
        else:
            self.start_continuous()

    def listen_once(self):
        if self._is_listening:
            return
        self._is_listening = True
        self.listening_started.emit()
        self.status_changed.emit("Listening...")
        self._thread = threading.Thread(target=self._once_loop, daemon=True)
        self._thread.start()

    def speak(self, text):
        if self._voice_muted:
            return
        self._tts_queue.put(text)

    def stop_speaking(self):
        if self._tts_engine:
            try:
                self._tts_engine.stop()
            except Exception:
                pass
        self._is_speaking = False
        self.speaking_finished.emit()

    def mute_voice(self):
        self._voice_muted = True
        self.stop_speaking()

    def unmute_voice(self):
        self._voice_muted = False

    def _init_tts(self):
        if self._tts_engine is None:
            try:
                self._tts_engine = pyttsx3.init()
                voices = self._tts_engine.getProperty('voices')
                for v in voices:
                    if 'female' in v.name.lower() or 'zira' in v.name.lower():
                        self._tts_engine.setProperty('voice', v.id)
                        break
                self._tts_engine.setProperty('rate', 175)
                self._tts_engine.setProperty('volume', 0.9)
            except Exception:
                self._tts_engine = None

    def _tts_worker(self):
        self._init_tts()
        while True:
            text = self._tts_queue.get()
            if text is None:
                break
            if self._tts_engine is None:
                continue
            self._is_speaking = True
            self.speaking_started.emit()
            try:
                self._tts_engine.say(text)
                self._tts_engine.runAndWait()
            except Exception:
                pass
            self._is_speaking = False
            self.speaking_finished.emit()

    def start_tts_thread(self):
        t = threading.Thread(target=self._tts_worker, daemon=True)
        t.start()

    def _continuous_loop(self):
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=0.3)
        while self._continuous and self._is_listening:
            try:
                with self.microphone as source:
                    self.status_changed.emit("Listening...")
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=30)
                self.status_changed.emit("Processing...")
                try:
                    text = self.recognizer.recognize_google(audio)
                    self.text_recognized.emit(text)
                    self.status_changed.emit("Listening...")
                except sr.UnknownValueError:
                    self.status_changed.emit("Listening...")
                except sr.RequestError as e:
                    self.error_occurred.emit(f"Speech service error: {e}")
                    self.status_changed.emit("Listening...")
            except sr.WaitTimeoutError:
                if self._continuous:
                    self.status_changed.emit("Listening...")
                continue
            except Exception as e:
                if self._continuous:
                    self.status_changed.emit("Listening...")
                continue
        self._is_listening = False
        self.listening_stopped.emit()
        self.status_changed.emit("Paused")

    def _once_loop(self):
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.3)
                self.status_changed.emit("Listening...")
                audio = self.recognizer.listen(source, timeout=10, phrase_time_limit=15)
            self.status_changed.emit("Processing...")
            try:
                text = self.recognizer.recognize_google(audio)
                self.text_recognized.emit(text)
            except sr.UnknownValueError:
                self.error_occurred.emit("Could not understand audio.")
            except sr.RequestError as e:
                self.error_occurred.emit(f"Speech service error: {e}")
        except sr.WaitTimeoutError:
            self.error_occurred.emit("No speech detected.")
        except Exception as e:
            self.error_occurred.emit(str(e))
        finally:
            self._is_listening = False
            self.listening_stopped.emit()
            self.status_changed.emit("Ready")
