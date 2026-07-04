from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QFrame, QScrollArea, QProgressBar
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QColor
from ui.design import COLORS, SIZES, FONTS, make_card
from voice import VoiceEngine


class TaskInputView(QWidget):
    tasks_submitted = pyqtSignal(str)
    back_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        self.voice = VoiceEngine()
        self.voice.text_recognized.connect(self._on_voice_text)
        self.voice.listening_started.connect(self._on_listening_start)
        self.voice.listening_stopped.connect(self._on_listening_stop)
        self.voice.error_occurred.connect(self._on_voice_error)
        self.voice.status_changed.connect(self._on_status_change)
        self._is_submitting = False
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(20)

        header = QHBoxLayout()
        back_btn = QPushButton("\u2190 Back")
        back_btn.setStyleSheet(f"""
            QPushButton {{
                color: {COLORS['text_secondary']};
                background: transparent;
                border: none;
                font-size: {SIZES['body_size']}px;
                padding: 8px;
            }}
            QPushButton:hover {{ color: {COLORS['accent_secondary']}; }}
        """)
        back_btn.clicked.connect(self.back_clicked.emit)
        header.addWidget(back_btn)
        header.addStretch()
        layout.addLayout(header)

        title = QLabel("What's on your plate today?")
        title.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 26px; font-weight: 700; background: transparent; border: none;")
        layout.addWidget(title)

        subtitle = QLabel("List your tasks or speak them. Pinchu's AI will organize them for you.")
        subtitle.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: {SIZES['body_size']}px; background: transparent; border: none;")
        layout.addWidget(subtitle)

        tips_card = make_card()
        tips_layout = QVBoxLayout(tips_card)
        tips_layout.setContentsMargins(18, 14, 18, 14)
        tips_label = QLabel("Tips for better task planning:")
        tips_label.setStyleSheet(f"color: {COLORS['accent_secondary']}; font-size: {SIZES['small_size']}px; font-weight: 600; background: transparent; border: none;")
        tips_layout.addWidget(tips_label)
        tips = [
            "Be specific: 'Finish report for Q2 review' instead of 'work on report'",
            "Include time estimates: '30 min yoga', '1 hour study session'",
            "Add deadlines: 'Submit proposal by 3pm'",
            "Mix task types: work, health, learning, personal",
        ]
        for tip in tips:
            t = QLabel(f"  \u2022  {tip}")
            t.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: {SIZES['tiny_size']}px; background: transparent; border: none;")
            tips_layout.addWidget(t)
        layout.addWidget(tips_card)

        self.task_input = QTextEdit()
        self.task_input.setPlaceholderText(
            "Enter your tasks, one per line:\n\n"
            "  Finish the project proposal\n"
            "  30 min exercise\n"
            "  Read for 20 minutes\n"
            "  Reply to client emails\n"
            "  Review quarterly goals"
        )
        self.task_input.setMinimumHeight(180)
        self.task_input.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLORS['bg_card']};
                color: {COLORS['text_primary']};
                border: 2px solid {COLORS['border']};
                border-radius: {SIZES['card_radius']}px;
                padding: 16px;
                font-size: 14px;
                font-family: '{FONTS["body"]}';
                line-height: 1.6;
            }}
            QTextEdit:focus {{
                border-color: {COLORS['accent_primary']};
            }}
        """)
        layout.addWidget(self.task_input, 1)

        voice_card = make_card()
        vc_layout = QVBoxLayout(voice_card)
        vc_layout.setContentsMargins(16, 12, 16, 12)
        vc_layout.setSpacing(8)

        vc_header = QHBoxLayout()
        vc_title = QLabel("\U0001f3a4 Voice Input")
        vc_title.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: {SIZES['body_size']}px; font-weight: 600; background: transparent; border: none;")
        vc_header.addWidget(vc_title)
        vc_header.addStretch()
        self.voice_hint = QLabel("Click mic or press Space")
        self.voice_hint.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: {SIZES['tiny_size']}px; background: transparent; border: none;")
        vc_header.addWidget(self.voice_hint)
        vc_layout.addLayout(vc_header)

        voice_row = QHBoxLayout()
        voice_row.setSpacing(12)

        self.mic_btn = QPushButton("\U0001f3a4")
        self.mic_btn.setFixedSize(48, 48)
        self.mic_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {COLORS['accent_primary']}, stop:1 {COLORS['accent_secondary']});
                color: white;
                border: none;
                border-radius: 24px;
                font-size: 18px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {COLORS['accent_secondary']}, stop:1 {COLORS['accent_primary']});
            }}
        """)
        self.mic_btn.clicked.connect(self._toggle_voice)
        voice_row.addWidget(self.mic_btn)

        voice_text_col = QVBoxLayout()
        voice_text_col.setSpacing(2)
        self.voice_status = QLabel("Ready to listen")
        self.voice_status.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: {SIZES['small_size']}px; background: transparent; border: none;")
        voice_text_col.addWidget(self.voice_status)
        self.last_spoken = QLabel("")
        self.last_spoken.setWordWrap(True)
        self.last_spoken.setStyleSheet(f"color: {COLORS['accent_secondary']}; font-size: {SIZES['small_size']}px; font-style: italic; background: transparent; border: none;")
        voice_text_col.addWidget(self.last_spoken)
        voice_row.addLayout(voice_text_col, 1)

        self.pause_btn = QPushButton("\u23f8")
        self.pause_btn.setFixedSize(36, 36)
        self.pause_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_card_hover']};
                color: {COLORS['text_secondary']};
                border: 1px solid {COLORS['border_light']};
                border-radius: 18px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                border-color: {COLORS['accent_primary']};
            }}
        """)
        self.pause_btn.clicked.connect(self._stop_voice)
        self.pause_btn.hide()
        voice_row.addWidget(self.pause_btn)

        vc_layout.addLayout(voice_row)
        layout.addWidget(voice_card)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.task_count_label = QLabel("")
        self.task_count_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: {SIZES['small_size']}px; background: transparent; border: none;")
        btn_row.addWidget(self.task_count_label)

        clear_btn = QPushButton("Clear")
        clear_btn.setProperty("class", "secondary")
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                color: {COLORS['text_secondary']};
                background: transparent;
                border: 1px solid {COLORS['border_light']};
                border-radius: {SIZES['button_radius']}px;
                padding: 12px 28px;
                font-size: {SIZES['body_size']}px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_card']};
                border-color: {COLORS['accent_primary']};
                color: {COLORS['text_primary']};
            }}
        """)
        clear_btn.clicked.connect(self._clear_input)
        btn_row.addWidget(clear_btn)

        self.submit_btn = QPushButton("\u2728 Let Pinchu Organize")
        self.submit_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['accent_primary']}, stop:1 {COLORS['accent_secondary']});
                color: white;
                border: none;
                border-radius: {SIZES['button_radius']}px;
                padding: 12px 32px;
                font-size: {SIZES['body_size']}px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['accent_secondary']}, stop:1 {COLORS['accent_primary']});
            }}
            QPushButton:disabled {{
                background-color: {COLORS['border']};
                color: {COLORS['text_muted']};
            }}
        """)
        self.submit_btn.clicked.connect(self._submit)
        btn_row.addWidget(self.submit_btn)
        layout.addLayout(btn_row)

    def _update_task_count(self):
        text = self.task_input.toPlainText().strip()
        if text:
            lines = [l.strip() for l in text.split("\n") if l.strip()]
            count = len(lines)
            self.task_count_label.setText(f"{count} task{'s' if count != 1 else ''} detected")
        else:
            self.task_count_label.setText("")

    def _clear_input(self):
        self.task_input.clear()
        self.task_count_label.setText("")

    def _toggle_voice(self):
        if self.voice.is_continuous:
            self.voice.stop_continuous()
        else:
            self.voice.start_continuous()
            self.pause_btn.show()

    def _stop_voice(self):
        self.voice.stop_continuous()
        self.pause_btn.hide()

    def _on_listening_start(self):
        self.mic_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {COLORS['danger']}, stop:1 #ff6b6b);
                color: white;
                border: none;
                border-radius: 24px;
                font-size: 18px;
            }}
        """)
        self.voice_status.setText("Listening... speak your tasks")
        self.voice_hint.setText("Speak now, click mic to pause")

    def _on_listening_stop(self):
        self.mic_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {COLORS['accent_primary']}, stop:1 {COLORS['accent_secondary']});
                color: white;
                border: none;
                border-radius: 24px;
                font-size: 18px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {COLORS['accent_secondary']}, stop:1 {COLORS['accent_primary']});
            }}
        """)
        self.voice_status.setText("Ready to listen")
        self.voice_hint.setText("Click mic or press Space")
        self.pause_btn.hide()

    def _on_status_change(self, status):
        self.voice_status.setText(status)

    def _on_voice_text(self, text):
        self.last_spoken.setText(f'"{text}"')
        current = self.task_input.toPlainText().strip()
        if current:
            self.task_input.setPlainText(current + "\n" + text)
        else:
            self.task_input.setPlainText(text)
        self._update_task_count()
        QTimer.singleShot(2000, lambda: self.last_spoken.setText(""))

    def _on_voice_error(self, error):
        self.voice_status.setText(error)
        QTimer.singleShot(3000, lambda: self.voice_status.setText("Ready to listen"))

    def _submit(self):
        if self._is_submitting:
            return
        text = self.task_input.toPlainText().strip()
        if not text:
            return
        self._is_submitting = True
        self.submit_btn.setEnabled(False)
        self.submit_btn.setText("Organizing...")
        self.tasks_submitted.emit(text)

    def on_submit_done(self):
        self._is_submitting = False
        self.submit_btn.setEnabled(True)
        self.submit_btn.setText("\u2728 Let Pinchu Organize")
        self.task_input.clear()
        self.task_count_label.setText("")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space and not self.task_input.hasFocus():
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
