from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QLineEdit, QTextEdit, QFrame, QScrollArea
from PyQt5.QtCore import Qt, QPoint, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QPainter, QColor, QRadialGradient, QPainterPath
from ui.character import CharacterWidget, CharacterState


class DesktopOverlay(QWidget):
    dismiss_clicked = pyqtSignal()
    chat_submitted = pyqtSignal(str)
    expand_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(320, 420)
        self._drag_pos = None
        self._expanded = False
        self._messages = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.character = CharacterWidget()
        self.character.clicked.connect(self._toggle_expand)
        layout.addWidget(self.character, alignment=Qt.AlignCenter)

        self.message_label = QLabel("")
        self.message_label.setWordWrap(True)
        self.message_label.setAlignment(Qt.AlignCenter)
        self.message_label.setStyleSheet(f"""
            QLabel {{
                color: #f0eaf8;
                font-size: 12px;
                padding: 8px 14px;
                background-color: rgba(28, 23, 48, 220);
                border: 1px solid rgba(155, 109, 255, 80);
                border-radius: 12px;
                margin: 0 20px 8px 20px;
            }}
        """)
        self.message_label.hide()
        layout.addWidget(self.message_label)

        self.chat_panel = QFrame()
        self.chat_panel.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(13, 11, 20, 240);
                border: 1px solid rgba(155, 109, 255, 60);
                border-radius: 16px;
                margin: 4px;
            }}
        """)
        chat_layout = QVBoxLayout(self.chat_panel)
        chat_layout.setContentsMargins(10, 8, 10, 8)
        chat_layout.setSpacing(6)

        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self.chat_content = QWidget()
        self.chat_content.setStyleSheet("background: transparent;")
        self.chat_msgs_layout = QVBoxLayout(self.chat_content)
        self.chat_msgs_layout.setContentsMargins(0, 0, 0, 0)
        self.chat_msgs_layout.setSpacing(4)
        self.chat_msgs_layout.addStretch()
        self.chat_scroll.setWidget(self.chat_content)
        chat_layout.addWidget(self.chat_scroll)

        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Say something...")
        self.chat_input.setFixedHeight(36)
        self.chat_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: rgba(28, 23, 48, 200);
                color: #f0eaf8;
                border: 1px solid rgba(155, 109, 255, 60);
                border-radius: 10px;
                padding: 6px 10px;
                font-size: 11px;
            }}
            QLineEdit:focus {{
                border-color: rgba(155, 109, 255, 150);
            }}
        """)
        self.chat_input.returnPressed.connect(self._send_chat)
        chat_layout.addWidget(self.chat_input)
        self.chat_panel.hide()
        layout.addWidget(self.chat_panel)

        self.chat_panel.setFixedHeight(0)

    def _toggle_expand(self):
        if self._expanded:
            self.chat_panel.hide()
            self.setFixedHeight(420)
            self._expanded = False
        else:
            self.chat_panel.show()
            self.chat_panel.setFixedHeight(250)
            self.setFixedHeight(670)
            self._expanded = True

    def show_message(self, text: str, duration: int = 5000):
        self.message_label.setText(text)
        self.message_label.show()
        QTimer.singleShot(duration, self.message_label.hide)

    def set_character_state(self, state: CharacterState, caption: str = ""):
        self.character.set_state(state, caption)

    def _send_chat(self):
        text = self.chat_input.text().strip()
        if not text:
            return
        self.chat_input.clear()
        self._add_msg("You", text)
        self.chat_submitted.emit(text)

    def add_chat_response(self, text: str):
        self._add_msg("Pinchu", text)

    def _add_msg(self, sender: str, text: str):
        msg_widget = QFrame()
        is_pinchu = sender == "Pinchu"
        bg_color = "rgba(28, 23, 48, 200)" if is_pinchu else "rgba(90, 61, 184, 180)"
        msg_widget.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border-radius: 8px;
                padding: 4px;
            }}
        """)
        msg_layout = QVBoxLayout(msg_widget)
        msg_layout.setContentsMargins(8, 4, 8, 4)
        msg_layout.setSpacing(2)

        sender_lbl = QLabel(sender)
        color = "#c49bff" if is_pinchu else "#d4b8ff"
        sender_lbl.setStyleSheet(f"color: {color}; font-size: 9px; font-weight: 600; background: transparent; border: none;")
        msg_layout.addWidget(sender_lbl)

        text_lbl = QLabel(text)
        text_lbl.setWordWrap(True)
        text_lbl.setStyleSheet(f"color: #f0eaf8; font-size: 10px; background: transparent; border: none;")
        msg_layout.addWidget(text_lbl)

        self.chat_msgs_layout.insertWidget(self.chat_msgs_layout.count() - 1, msg_widget)
        self.chat_scroll.verticalScrollBar().setValue(self.chat_scroll.verticalScrollBar().maximum())

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() & Qt.LeftButton:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        event.accept()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        grad = QRadialGradient(160, 200, 200)
        grad.setColorAt(0, QColor(155, 109, 255, 25))
        grad.setColorAt(1, QColor(155, 109, 255, 0))
        painter.fillRect(self.rect(), grad)
        painter.end()
