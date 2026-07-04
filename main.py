import sys
import asyncio
import threading
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QStackedWidget, QFrame
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QFont, QPainter, QColor, QLinearGradient, QIcon, QPixmap

from ui.design import COLORS, SIZES, FONTS, MAIN_STYLESHEET
from task_manager import TaskManager
from activity_monitor import ActivityMonitor
from ai_client import AIClient, _get_or_create_loop
from memory import MemoryManager
from overlay import DesktopOverlay
from tray import TrayIcon
from ui.character import CharacterState
from ui.views.dashboard import DashboardView
from ui.views.task_input import TaskInputView
from ui.views.summary import SummaryView
from ui.views.chat import ChatView
from ui.views.knowledge_graph import KnowledgeGraphView
from context_chain import SessionContext


def run_async(coro):
    loop = asyncio.new_event_loop()
    threading.Thread(target=loop.run_until_complete, args=(coro,), daemon=True).start()


def create_app_icon():
    pixmap = QPixmap(64, 64)
    pixmap.fill(QColor(0, 0, 0, 0))
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    grad = QColor(155, 109, 255)
    painter.setBrush(grad)
    painter.setPen(QColor(0, 0, 0, 0))
    painter.drawEllipse(4, 4, 56, 56)
    painter.setPen(QColor("#ffffff"))
    font = QFont("Segoe UI", 28, QFont.Bold)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), 0x84 | 0x80, "P")
    painter.end()
    return QIcon(pixmap)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pinchu - Your Productivity Buddy")
        self.setMinimumSize(1100, 720)
        self.resize(1200, 780)
        self.setWindowIcon(create_app_icon())

        self.task_manager = TaskManager()
        self.activity_monitor = ActivityMonitor()
        self.ai_client = AIClient()
        self.memory = MemoryManager()
        self.session_context = SessionContext()

        self._setup_ui()
        self._setup_overlay()
        self._setup_tray()
        self._setup_timers()
        self._setup_memory_signals()

        self.session_context.start_session()
        self.overlay.show_message("Hey! I'm Pinchu. Ready to have a productive day?", 6000)

        try:
            loop = _get_or_create_loop()
            loop.run_until_complete(self.memory.init_cognee())
        except Exception:
            pass

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        sidebar = self._create_sidebar()
        main_layout.addWidget(sidebar)

        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background: transparent;")

        self.dashboard_view = DashboardView(self.task_manager, self.memory)
        self.dashboard_view.add_tasks_clicked.connect(lambda: self.stack.setCurrentWidget(self.task_input_view))
        self.dashboard_view.view_changed.connect(self._on_view_change)

        self.task_input_view = TaskInputView()
        self.task_input_view.tasks_submitted.connect(self._on_tasks_submitted)
        self.task_input_view.back_clicked.connect(lambda: self.stack.setCurrentWidget(self.dashboard_view))

        self.summary_view = SummaryView(self.task_manager)
        self.summary_view.back_clicked.connect(lambda: self.stack.setCurrentWidget(self.dashboard_view))

        self.chat_view = ChatView(self.ai_client)
        self.chat_view.back_clicked.connect(lambda: self.stack.setCurrentWidget(self.dashboard_view))

        self.knowledge_graph_view = KnowledgeGraphView(self.memory)
        self.knowledge_graph_view.back_clicked.connect(lambda: self.stack.setCurrentWidget(self.dashboard_view))

        self.stack.addWidget(self.dashboard_view)
        self.stack.addWidget(self.task_input_view)
        self.stack.addWidget(self.summary_view)
        self.stack.addWidget(self.chat_view)
        self.stack.addWidget(self.knowledge_graph_view)

        main_layout.addWidget(self.stack, 1)

    def _create_sidebar(self):
        sidebar = QFrame()
        sidebar.setFixedWidth(SIZES['sidebar_width'])
        sidebar.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_sidebar']};
                border-right: 1px solid {COLORS['border']};
            }}
        """)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(16, 20, 16, 20)
        layout.setSpacing(4)

        logo_row = QHBoxLayout()
        logo_row.setSpacing(10)
        logo_icon = QLabel("P")
        logo_icon.setFixedSize(36, 36)
        logo_icon.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {COLORS['accent_primary']}, stop:1 {COLORS['accent_secondary']});
            color: white;
            border-radius: 10px;
            font-size: 18px;
            font-weight: 700;
        """)
        logo_icon.setAlignment(Qt.AlignCenter)
        logo_row.addWidget(logo_icon)
        logo_text = QLabel("Pinchu")
        logo_text.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 20px; font-weight: 700; background: transparent; border: none;")
        logo_row.addWidget(logo_text)
        logo_row.addStretch()
        layout.addLayout(logo_row)

        layout.addSpacing(20)

        nav_items = [
            ("Dashboard", "dashboard"),
            ("Tasks", "tasks"),
            ("Summary", "summary"),
            ("Chat", "chat"),
            ("Graph", "graph"),
        ]

        self.nav_buttons = {}
        for label, key in nav_items:
            btn = QPushButton(f"  {label}")
            btn.setCheckable(True)
            btn.setStyleSheet(self._nav_btn_style(False))
            btn.clicked.connect(lambda checked, k=key: self._on_nav(k))
            self.nav_buttons[key] = btn
            layout.addWidget(btn)

        layout.addStretch()

        version_label = QLabel("v1.0.0")
        version_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: {SIZES['tiny_size']}px; background: transparent; border: none; padding: 8px 16px;")
        layout.addWidget(version_label)

        return sidebar

    def _nav_btn_style(self, active):
        bg = COLORS['sidebar_active'] if active else "transparent"
        color = COLORS['text_primary'] if active else COLORS['text_secondary']
        weight = "600" if active else "400"
        return f"""
            QPushButton {{
                background-color: {bg};
                color: {color};
                border: none;
                border-radius: 10px;
                padding: 12px 16px;
                text-align: left;
                font-size: {SIZES['body_size']}px;
                font-weight: {weight};
            }}
            QPushButton:hover {{
                background-color: {COLORS['sidebar_hover']};
            }}
        """

    def _on_nav(self, key):
        for k, btn in self.nav_buttons.items():
            btn.setChecked(k == key)
            btn.setStyleSheet(self._nav_btn_style(k == key))

        view_map = {
            "dashboard": self.dashboard_view,
            "tasks": self.dashboard_view,
            "summary": self.summary_view,
            "chat": self.chat_view,
            "graph": self.knowledge_graph_view,
        }
        if key in view_map:
            self.stack.setCurrentWidget(view_map[key])
            if key == "summary":
                self.summary_view.refresh()
            elif key == "dashboard":
                self.dashboard_view.refresh()

    def _on_view_change(self, view_name):
        self._on_nav(view_name)

    def _setup_overlay(self):
        self.overlay = DesktopOverlay()
        self.overlay.chat_submitted.connect(self._on_chat_submit)
        self.overlay.move(50, 100)
        self.overlay.show()

    def _setup_tray(self):
        self.tray = TrayIcon()
        self.tray.show_dashboard.connect(self._show_dashboard)
        self.tray.show_overlay.connect(lambda: self.overlay.show())
        self.tray.quit_app.connect(self._quit)
        self.tray.improve_memory.connect(self._on_improve_memory)
        self.tray.clear_memory.connect(self._on_clear_memory)

    def _setup_timers(self):
        self.reminder_timer = QTimer(self)
        self.reminder_timer.timeout.connect(self._send_reminder)
        self.reminder_timer.start(600000)

        self.activity_timer = QTimer(self)
        self.activity_timer.timeout.connect(self._check_activity)
        self.activity_timer.start(30000)

        self.overlay_timer = QTimer(self)
        self.overlay_timer.timeout.connect(self._cycle_overlay_state)
        self.overlay_timer.start(120000)

    def _setup_memory_signals(self):
        self.memory.memory_improved.connect(lambda msg: self.tray.show_notification("Memory", msg, 3000))
        self.memory.memory_cleared.connect(lambda msg: self.tray.show_notification("Memory", msg, 3000))
        self.memory.memory_error.connect(lambda msg: self.tray.show_notification("Memory Error", msg, 5000))

    def _on_tasks_submitted(self, raw_text: str):
        self.task_manager.set_today_tasks(raw_text)
        self.overlay.set_character_state(CharacterState.THINKING, "Let me organize your tasks...")
        self.stack.setCurrentWidget(self.dashboard_view)
        self._on_nav("dashboard")

        self.session_context.add_context(f"Tasks submitted: {raw_text}", "user")

        try:
            tasks = [line.strip() for line in raw_text.split("\n") if line.strip()]
            result = _get_or_create_loop().run_until_complete(
                self.ai_client.classify_tasks(tasks)
            )
            self.task_manager.set_classified_tasks(result)
            self.dashboard_view.refresh()
            self.overlay.set_character_state(CharacterState.EXCITED, "Got it! Your day is planned.")
            run_async(self.memory.remember(
                f"Tasks set for today: {raw_text}",
                metadata={"type": "task_plan", "date": datetime.now().isoformat()}
            ))
            run_async(self.memory.improve())
            self.session_context.add_context(f"Tasks classified: {len(tasks)} tasks created", "pinchu")
            self.tray.show_notification(
                "Tasks Organized!",
                f"Created {len(tasks)} tasks. Pinchu will keep you on track!",
                4000
            )
        except Exception as e:
            self.overlay.set_character_state(CharacterState.CONCERNED, "Oops, something went wrong.")
            self.tray.show_notification("Error", str(e), 4000)
        finally:
            self.task_input_view.on_submit_done()

    def _send_reminder(self):
        pending = self.task_manager.get_pending_tasks()
        if pending:
            task = pending[0]
            try:
                activity = self.activity_monitor.get_active_window_title()
                msg = _get_or_create_loop().run_until_complete(
                    self.ai_client.generate_reminder(
                        task["task"], task.get("progress", 0), activity
                    )
                )
                state = CharacterState.NOTICING if len(pending) > 2 else CharacterState.PRESENTING
                self.overlay.set_character_state(state, msg)
                self.tray.show_notification("Task Reminder", msg, 5000)
            except Exception:
                pass

    def _check_activity(self):
        title = self.activity_monitor.get_active_window_title()
        app = self.activity_monitor.get_browser_url()
        self.activity_monitor.log_activity(title, app)

        pending = self.task_manager.get_pending_tasks()
        if pending:
            matches = self.activity_monitor.check_task_match(pending, title, app)
            if matches:
                task = matches[0]
                try:
                    msg = _get_or_create_loop().run_until_complete(
                        self.ai_client.generate_motivation(app, task["task"])
                    )
                    self.overlay.set_character_state(CharacterState.PROUD, msg)
                    self.task_manager.mark_task_progress(
                        str(task["index"]),
                        min(1.0, task.get("progress", 0) + 0.1)
                    )
                    run_async(self.memory.remember(
                        f"Working on: {task['task']} in {app}",
                        metadata={"type": "activity", "app": app, "task": task["task"]}
                    ))
                except Exception:
                    pass

    def _cycle_overlay_state(self):
        pending = self.task_manager.get_pending_tasks()
        if not pending:
            self.overlay.set_character_state(CharacterState.PLEASED, "All done for today!")
        elif len(pending) > 3:
            self.overlay.set_character_state(CharacterState.CONCERNED, f"{len(pending)} tasks remaining...")
        else:
            self.overlay.set_character_state(CharacterState.IDLE)

    def _on_chat_submit(self, text: str):
        self.session_context.add_context(text, "user")
        session_context = self.session_context.get_context_for_ai()
        context = f"Today's tasks: {self.task_manager.get_today_tasks()}\n\nSession context:\n{session_context}"
        try:
            response = _get_or_create_loop().run_until_complete(
                self.ai_client.chat_conversational(text, context)
            )
            self.overlay.add_chat_response(response)
            self.session_context.add_context(response, "pinchu")
            run_async(self.memory.remember(
                f"Chat: User asked '{text[:50]}' | Pinchu replied '{response[:50]}'",
                metadata={"type": "chat", "user_msg": text[:100], "ai_msg": response[:100]}
            ))
        except Exception:
            self.overlay.add_chat_response("Sorry, I'm having connection issues right now.")

    def _show_dashboard(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def _on_improve_memory(self):
        self.overlay.set_character_state(CharacterState.THINKING, "Optimizing my memory...")
        try:
            result = _get_or_create_loop().run_until_complete(
                self.memory.improve()
            )
            self.overlay.set_character_state(CharacterState.PROUD, "Memory optimized! I remember better now.")
            self.tray.show_notification("Memory Improved", "Pinchu's memory has been optimized.", 3000)
        except Exception as e:
            self.overlay.set_character_state(CharacterState.CONCERNED, "Memory optimization failed.")
            self.tray.show_notification("Error", f"Improve failed: {e}", 3000)

    def _on_clear_memory(self):
        self.overlay.set_character_state(CharacterState.THINKING, "Clearing memory...")
        try:
            _get_or_create_loop().run_until_complete(
                self.memory.forget()
            )
            self.overlay.set_character_state(CharacterState.EXCITED, "Memory cleared! Fresh start.")
            self.tray.show_notification("Memory Cleared", "Pinchu's memory has been cleared.", 3000)
        except Exception as e:
            self.overlay.set_character_state(CharacterState.CONCERNED, "Failed to clear memory.")
            self.tray.show_notification("Error", f"Clear failed: {e}", 3000)

    def _quit(self):
        self.session_context.end_session()
        self.overlay.hide()
        self.tray.hide()
        QApplication.quit()

    def closeEvent(self, event):
        event.ignore()
        self.hide()
        self.tray.show_notification(
            "Pinchu",
            "I'm still here! Double-click the tray icon to open.",
            3000
        )


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Pinchu")
    app.setApplicationVersion("1.0.0")
    app.setQuitOnLastWindowClosed(False)
    app.setWindowIcon(create_app_icon())

    font = QFont(FONTS['body'], 10)
    app.setFont(font)

    app.setStyleSheet(MAIN_STYLESHEET)

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
