from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QLineEdit
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QColor, QPainter, QRadialGradient
from ui.design import COLORS, SIZES, FONTS, make_card
from ai_client import _get_or_create_loop
from voice import VoiceEngine


class VoicePulseIndicator(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(56, 56)
        self._active = False
        self._pulse = 0.0
        self._color = QColor(COLORS['accent_primary'])
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(50)

    def set_active(self, active):
        self._active = active
        if not active:
            self._pulse = 0.0
        self.update()

    def set_color(self, color):
        self._color = color
        self.update()

    def _tick(self):
        if self._active:
            import math
            self._pulse = (self._pulse + 0.08) % (2 * math.pi)
        self.update()

    def paintEvent(self, event):
        import math
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        cx, cy = self.width() / 2, self.height() / 2
        if self._active:
            pulse_val = (math.sin(self._pulse) + 1) / 2
            for i in range(3):
                r = 18 + i * 6 + pulse_val * 4
                alpha = int(60 - i * 18)
                grad = QRadialGradient(cx, cy, r)
                grad.setColorAt(0, QColor(self._color.red(), self._color.green(), self._color.blue(), alpha))
                grad.setColorAt(1, QColor(self._color.red(), self._color.green(), self._color.blue(), 0))
                p.setBrush(grad)
                p.setPen(Qt.NoPen)
                p.drawEllipse(int(cx - r), int(cy - r), int(r * 2), int(r * 2))
        grad2 = QRadialGradient(cx, cy, 18)
        if self._active:
            grad2.setColorAt(0, QColor(self._color.red(), self._color.green(), self._color.blue(), 220))
            grad2.setColorAt(1, QColor(self._color.red(), self._color.green(), self._color.blue(), 120))
        else:
            grad2.setColorAt(0, QColor(COLORS['bg_card']))
            grad2.setColorAt(1, QColor(COLORS['bg_card_hover']))
        p.setBrush(grad2)
        p.setPen(Qt.NoPen)
        p.drawEllipse(int(cx - 18), int(cy - 18), 36, 36)
        icon_color = QColor("white") if self._active else QColor(COLORS['text_secondary'])
        p.setPen(icon_color)
        font = p.font()
        font.setPointSize(14)
        p.setFont(font)
        p.drawText(self.rect(), Qt.AlignCenter, "\U0001f3a4")
        p.end()


class ChatView(QWidget):
    back_clicked = pyqtSignal()

    def __init__(self, ai_client, parent=None):
        super().__init__(parent)
        self.ai_client = ai_client
        self.messages = []
        self.setStyleSheet("background: transparent;")
        self.voice = VoiceEngine()
        self.voice.text_recognized.connect(self._on_voice_text)
        self.voice.listening_started.connect(self._on_listening_start)
        self.voice.listening_stopped.connect(self._on_listening_stop)
        self.voice.speaking_started.connect(self._on_speaking_start)
        self.voice.speaking_finished.connect(self._on_speaking_finish)
        self.voice.error_occurred.connect(self._on_voice_error)
        self.voice.status_changed.connect(self._on_status_change)
        self.voice.start_tts_thread()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        header = QHBoxLayout()
        back_btn = QPushButton("\u2190 Back")
        back_btn.setStyleSheet(f"QPushButton {{ color: {COLORS['text_secondary']}; background: transparent; border: none; font-size: {SIZES['body_size']}px; padding: 8px; }} QPushButton:hover {{ color: {COLORS['accent_secondary']}; }}")
        back_btn.clicked.connect(self._on_back)
        header.addWidget(back_btn)
        header.addStretch()
        title = QLabel("Chat with Pinchu")
        title.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 20px; font-weight: 600; background: transparent; border: none;")
        header.addWidget(title)
        header.addStretch()

        self.voice_mode_btn = QPushButton("\U0001f3a4 Voice Mode")
        self.voice_mode_btn.setCheckable(True)
        self.voice_mode_btn.setStyleSheet(f"""
            QPushButton {{
                color: {COLORS['text_secondary']};
                background: transparent;
                border: 1px solid {COLORS['border_light']};
                border-radius: 20px;
                padding: 8px 18px;
                font-size: {SIZES['small_size']}px;
            }}
            QPushButton:hover {{
                border-color: {COLORS['accent_primary']};
                color: {COLORS['accent_secondary']};
            }}
            QPushButton:checked {{
                background-color: {COLORS['accent_primary']};
                color: white;
                border-color: {COLORS['accent_primary']};
            }}
        """)
        self.voice_mode_btn.clicked.connect(self._toggle_voice_mode)
        header.addWidget(self.voice_mode_btn)
        layout.addLayout(header)

        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self.chat_content = QWidget()
        self.chat_content.setStyleSheet("background: transparent;")
        self.chat_layout = QVBoxLayout(self.chat_content)
        self.chat_layout.setContentsMargins(0, 0, 0, 0)
        self.chat_layout.setSpacing(12)
        self.chat_layout.addStretch()
        self.chat_scroll.setWidget(self.chat_content)
        layout.addWidget(self.chat_scroll, 1)

        self._add_system_message("Hey! I'm Pinchu, your productivity buddy. Ask me anything about your tasks or just chat!")

        self.voice_panel = QFrame()
        self.voice_panel.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 16px;
                padding: 16px;
            }}
        """)
        vp_layout = QVBoxLayout(self.voice_panel)
        vp_layout.setContentsMargins(20, 16, 20, 16)
        vp_layout.setSpacing(12)

        vp_title = QLabel("Voice Chat")
        vp_title.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: {SIZES['heading_size']}px; font-weight: 600; background: transparent; border: none;")
        vp_layout.addWidget(vp_title)

        self.pulse_indicator = VoicePulseIndicator()
        vp_layout.addWidget(self.pulse_indicator, alignment=Qt.AlignCenter)

        self.voice_status_label = QLabel("Click the mic or press space to talk")
        self.voice_status_label.setAlignment(Qt.AlignCenter)
        self.voice_status_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: {SIZES['small_size']}px; background: transparent; border: none;")
        vp_layout.addWidget(self.voice_status_label)

        self.transcript_label = QLabel("")
        self.transcript_label.setAlignment(Qt.AlignCenter)
        self.transcript_label.setWordWrap(True)
        self.transcript_label.setStyleSheet(f"color: {COLORS['accent_secondary']}; font-size: {SIZES['body_size']}px; font-style: italic; background: transparent; border: none;")
        vp_layout.addWidget(self.transcript_label)

        mic_row = QHBoxLayout()
        mic_row.addStretch()

        self.big_mic_btn = QPushButton("\U0001f3a4")
        self.big_mic_btn.setFixedSize(64, 64)
        self.big_mic_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {COLORS['accent_primary']}, stop:1 {COLORS['accent_secondary']});
                color: white;
                border: none;
                border-radius: 32px;
                font-size: 24px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {COLORS['accent_secondary']}, stop:1 {COLORS['accent_primary']});
            }}
        """)
        self.big_mic_btn.clicked.connect(self._toggle_voice)
        mic_row.addWidget(self.big_mic_btn)

        mic_row.addStretch()
        vp_layout.addLayout(mic_row)

        self.voice_panel.hide()
        layout.addWidget(self.voice_panel)

        input_row = QHBoxLayout()
        input_row.setSpacing(10)

        self.mic_btn = QPushButton("\U0001f3a4")
        self.mic_btn.setFixedSize(40, 40)
        self.mic_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_card']};
                color: {COLORS['accent_secondary']};
                border: 1px solid {COLORS['border_light']};
                border-radius: 20px;
                font-size: 16px;
            }}
            QPushButton:hover {{
                border-color: {COLORS['accent_primary']};
                background-color: {COLORS['bg_card_hover']};
            }}
        """)
        self.mic_btn.clicked.connect(self._quick_listen)
        input_row.addWidget(self.mic_btn)

        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Ask Pinchu something...")
        self.chat_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLORS['bg_card']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 20px;
                padding: 12px 18px;
                font-size: {SIZES['body_size']}px;
            }}
            QLineEdit:focus {{ border-color: {COLORS['accent_primary']}; }}
        """)
        self.chat_input.returnPressed.connect(self._send)
        input_row.addWidget(self.chat_input, 1)

        self.send_btn = QPushButton("\u2192")
        self.send_btn.setFixedSize(40, 40)
        self.send_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['accent_primary']};
                color: white;
                border: none;
                border-radius: 20px;
                font-size: 16px;
                font-weight: 700;
            }}
            QPushButton:hover {{ background-color: {COLORS['accent_secondary']}; }}
            QPushButton:disabled {{ background-color: {COLORS['border']}; color: {COLORS['text_muted']}; }}
        """)
        self.send_btn.clicked.connect(self._send)
        input_row.addWidget(self.send_btn)
        layout.addLayout(input_row)

    def _toggle_voice_mode(self, checked):
        if checked:
            self.voice_panel.show()
            self.chat_scroll.hide()
        else:
            self.voice_panel.hide()
            self.chat_scroll.show()
            self.voice.stop_continuous()

    def _toggle_voice(self):
        if self.voice.is_listening:
            self.voice.stop_continuous()
        else:
            self.voice.start_continuous()

    def _quick_listen(self):
        self.voice.listen_once()

    def _on_listening_start(self):
        self.pulse_indicator.set_active(True)
        self.pulse_indicator.set_color(QColor(COLORS['accent_primary']))
        self.big_mic_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {COLORS['danger']}, stop:1 #ff6b6b);
                color: white;
                border: none;
                border-radius: 32px;
                font-size: 24px;
            }}
        """)
        self.mic_btn.setText("\U0001f534")
        self.mic_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['danger']};
                color: white;
                border: none;
                border-radius: 20px;
                font-size: 16px;
            }}
        """)
        self.voice_status_label.setText("Listening... speak now")

    def _on_listening_stop(self):
        self.pulse_indicator.set_active(False)
        self.big_mic_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {COLORS['accent_primary']}, stop:1 {COLORS['accent_secondary']});
                color: white;
                border: none;
                border-radius: 32px;
                font-size: 24px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {COLORS['accent_secondary']}, stop:1 {COLORS['accent_primary']});
            }}
        """)
        self.mic_btn.setText("\U0001f3a4")
        self.mic_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_card']};
                color: {COLORS['accent_secondary']};
                border: 1px solid {COLORS['border_light']};
                border-radius: 20px;
                font-size: 16px;
            }}
            QPushButton:hover {{
                border-color: {COLORS['accent_primary']};
                background-color: {COLORS['bg_card_hover']};
            }}
        """)
        if not self.voice.is_speaking:
            self.voice_status_label.setText("Click mic or space to talk")

    def _on_speaking_start(self):
        self.pulse_indicator.set_active(True)
        self.pulse_indicator.set_color(QColor(COLORS['success']))
        self.voice_status_label.setText("Pinchu is speaking...")

    def _on_speaking_finish(self):
        self.pulse_indicator.set_active(False)
        if self.voice.is_continuous:
            self.voice_status_label.setText("Listening... speak now")
        else:
            self.voice_status_label.setText("Click mic or space to talk")

    def _on_status_change(self, status):
        self.voice_status_label.setText(status)

    def _on_voice_text(self, text):
        self.transcript_label.setText(f'You said: "{text}"')
        QTimer.singleShot(500, lambda: self._process_voice_input(text))

    def _process_voice_input(self, text):
        self._add_user_message(text)
        self.messages.append({"role": "user", "content": text})
        self.voice_status_label.setText("Thinking...")
        self._show_typing()
        try:
            context = f"Today's tasks: {self.ai_client}" if hasattr(self, '_task_context') else ""
            recent = self.messages[-8:] if len(self.messages) > 8 else self.messages
            context_str = f"Conversation history: {recent}"
            response = _get_or_create_loop().run_until_complete(
                self.ai_client.chat_conversational(text, context_str)
            )
        except Exception:
            response = "Sorry, I'm having trouble connecting right now."
        self._hide_typing()
        self._add_system_message(response)
        self.messages.append({"role": "assistant", "content": response})
        self.voice.speak(response)

    def _on_voice_error(self, error):
        self.voice_status_label.setText(error)
        QTimer.singleShot(3000, lambda: self.voice_status_label.setText("Click mic or space to talk"))

    def _show_typing(self):
        self.typing_card = QFrame()
        self.typing_card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 14px;
                padding: 12px 16px;
            }}
        """)
        layout = QVBoxLayout(self.typing_card)
        layout.setContentsMargins(16, 10, 16, 10)
        sender = QLabel("Pinchu")
        sender.setStyleSheet(f"color: {COLORS['accent_secondary']}; font-size: {SIZES['tiny_size']}px; font-weight: 600; background: transparent; border: none;")
        layout.addWidget(sender)
        dots = QLabel("Thinking...")
        dots.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: {SIZES['body_size']}px; background: transparent; border: none; font-style: italic;")
        layout.addWidget(dots)
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, self.typing_card)
        self.chat_scroll.verticalScrollBar().setValue(self.chat_scroll.verticalScrollBar().maximum())

    def _hide_typing(self):
        if hasattr(self, 'typing_card') and self.typing_card:
            self.typing_card.deleteLater()
            self.typing_card = None

    def _add_system_message(self, text):
        msg_card = QFrame()
        msg_card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 14px;
                padding: 12px 16px;
            }}
        """)
        layout = QVBoxLayout(msg_card)
        layout.setContentsMargins(16, 10, 16, 10)
        sender = QLabel("Pinchu")
        sender.setStyleSheet(f"color: {COLORS['accent_secondary']}; font-size: {SIZES['tiny_size']}px; font-weight: 600; background: transparent; border: none;")
        layout.addWidget(sender)
        lbl = QLabel(text)
        lbl.setWordWrap(True)
        lbl.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: {SIZES['body_size']}px; background: transparent; border: none;")
        layout.addWidget(lbl)
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, msg_card)
        self.chat_scroll.verticalScrollBar().setValue(self.chat_scroll.verticalScrollBar().maximum())

    def _add_user_message(self, text):
        msg_card = QFrame()
        msg_card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['accent_dark']};
                border-radius: 14px;
                padding: 12px 16px;
            }}
        """)
        layout = QVBoxLayout(msg_card)
        layout.setContentsMargins(16, 10, 16, 10)
        sender = QLabel("You")
        sender.setStyleSheet(f"color: {COLORS['purple_light']}; font-size: {SIZES['tiny_size']}px; font-weight: 600; background: transparent; border: none;")
        layout.addWidget(sender)
        lbl = QLabel(text)
        lbl.setWordWrap(True)
        lbl.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: {SIZES['body_size']}px; background: transparent; border: none;")
        layout.addWidget(lbl)
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, msg_card)
        self.chat_scroll.verticalScrollBar().setValue(self.chat_scroll.verticalScrollBar().maximum())

    def _send(self):
        text = self.chat_input.text().strip()
        if not text:
            return
        self.chat_input.clear()
        self._add_user_message(text)
        self.messages.append({"role": "user", "content": text})
        self.send_btn.setEnabled(False)
        self._show_typing()
        try:
            recent = self.messages[-8:] if len(self.messages) > 8 else self.messages
            context_str = f"Conversation history: {recent}"
            response = _get_or_create_loop().run_until_complete(
                self.ai_client.chat_conversational(text, context_str)
            )
        except Exception:
            response = "Oops, I'm having trouble connecting right now. Try again in a moment!"
        self._hide_typing()
        self._add_system_message(response)
        self.messages.append({"role": "assistant", "content": response})
        self.send_btn.setEnabled(True)

    def _on_back(self):
        self.voice.stop_continuous()
        self.back_clicked.emit()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space and not self.chat_input.hasFocus():
            self._toggle_voice()
        else:
            super().keyPressEvent(event)

    def paintEvent(self, event):
        from PyQt5.QtGui import QPainter, QColor, QLinearGradient
        p = QPainter(self)
        grad = QLinearGradient(0, 0, 0, self.height())
        grad.setColorAt(0, QColor(COLORS['bg_primary']))
        grad.setColorAt(1, QColor(COLORS['gradient_end']))
        p.fillRect(self.rect(), grad)
        p.end()
