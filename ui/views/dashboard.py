from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton,
    QProgressBar, QScrollArea, QGridLayout, QTextEdit
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from ui.design import COLORS, SIZES, FONTS, make_card, make_stat_card, make_task_row


class DashboardView(QWidget):
    task_selected = pyqtSignal(int)
    add_tasks_clicked = pyqtSignal()
    view_changed = pyqtSignal(str)

    def __init__(self, task_manager, memory_manager=None, parent=None):
        super().__init__(parent)
        self.task_manager = task_manager
        self.memory_manager = memory_manager
        self.setStyleSheet("background: transparent;")
        self._setup_ui()
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self.refresh)
        self._refresh_timer.start(5000)

    def _setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(28, 24, 28, 24)
        self.main_layout.setSpacing(20)

        header = QHBoxLayout()
        header.setSpacing(16)
        title_col = QVBoxLayout()
        greeting = QLabel("Welcome back")
        greeting.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: {SIZES['body_size']}px; background: transparent; border: none;")
        title_col.addWidget(greeting)
        name = QLabel("Today's Dashboard")
        name.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 28px; font-weight: 700; background: transparent; border: none;")
        title_col.addWidget(name)
        subtitle = QLabel("Track your tasks, stay motivated, own your day.")
        subtitle.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: {SIZES['small_size']}px; background: transparent; border: none;")
        title_col.addWidget(subtitle)
        header.addLayout(title_col)
        header.addStretch()

        add_btn = QPushButton("+ Add Tasks")
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['accent_primary']}, stop:1 {COLORS['accent_secondary']});
                color: white;
                border: none;
                border-radius: 12px;
                padding: 12px 28px;
                font-size: {SIZES['body_size']}px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['accent_secondary']}, stop:1 {COLORS['accent_primary']});
            }}
        """)
        add_btn.clicked.connect(self.add_tasks_clicked.emit)
        header.addWidget(add_btn)
        self.main_layout.addLayout(header)

        self.dynamic_container = QWidget()
        self.dynamic_container.setStyleSheet("background: transparent;")
        self.dynamic_layout = QVBoxLayout(self.dynamic_container)
        self.dynamic_layout.setContentsMargins(0, 0, 0, 0)
        self.dynamic_layout.setSpacing(20)
        self.main_layout.addWidget(self.dynamic_container, 1)

        self.refresh()

    def refresh(self):
        while self.dynamic_layout.count():
            child = self.dynamic_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                self._clear_layout(child.layout())

        today_data = self.task_manager.get_today_tasks()
        classified = today_data.get("classified") or {}
        tasks_list = classified.get("classified_tasks", [])
        status = today_data.get("task_status", {})
        total = len(tasks_list)
        done = sum(1 for v in status.values() if v.get("completed"))
        pending = total - done
        pct = (done / total * 100) if total > 0 else 0

        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(14)
        stats_layout.addWidget(make_stat_card("Total Tasks", str(total), "Today's plan"))
        stats_layout.addWidget(make_stat_card("Completed", str(done), f"{pct:.0f}% done", COLORS['success']))
        stats_layout.addWidget(make_stat_card("Pending", str(pending), "Remaining today", COLORS['warning']))
        stats_layout.addWidget(make_stat_card("Streak", "0 days", "Keep going!", COLORS['accent_primary']))
        self.dynamic_layout.addLayout(stats_layout)

        progress_card = make_card()
        pc_layout = QVBoxLayout(progress_card)
        pc_layout.setContentsMargins(20, 16, 20, 16)
        pc_layout.setSpacing(12)
        pc_header = QHBoxLayout()
        pc_title = QLabel("Daily Progress")
        pc_title.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: {SIZES['heading_size']}px; font-weight: 600; background: transparent; border: none;")
        pc_header.addWidget(pc_title)
        pc_header.addStretch()
        pc_pct = QLabel(f"{pct:.0f}%")
        pc_pct.setStyleSheet(f"color: {COLORS['accent_secondary']}; font-size: {SIZES['heading_size']}px; font-weight: 700; background: transparent; border: none;")
        pc_header.addWidget(pc_pct)
        pc_layout.addLayout(pc_header)
        progress_bar = QProgressBar()
        progress_bar.setFixedHeight(10)
        progress_bar.setValue(int(pct))
        progress_bar.setTextVisible(False)
        pc_layout.addWidget(progress_bar)
        self.dynamic_layout.addWidget(progress_card)

        tasks_card = make_card()
        tc_layout = QVBoxLayout(tasks_card)
        tc_layout.setContentsMargins(20, 16, 20, 16)
        tc_layout.setSpacing(4)
        tc_header = QHBoxLayout()
        tc_title = QLabel("Today's Tasks")
        tc_title.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: {SIZES['heading_size']}px; font-weight: 600; background: transparent; border: none;")
        tc_header.addWidget(tc_title)
        tc_header.addStretch()
        view_all = QPushButton("See all")
        view_all.setStyleSheet(f"color: {COLORS['accent_secondary']}; background: transparent; border: none; font-size: {SIZES['small_size']}px;")
        view_all.clicked.connect(lambda: self.view_changed.emit("tasks"))
        tc_header.addWidget(view_all)
        tc_layout.addLayout(tc_header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        tasks_list_layout = QVBoxLayout(scroll_content)
        tasks_list_layout.setContentsMargins(0, 0, 0, 0)
        tasks_list_layout.setSpacing(2)

        if tasks_list:
            for i, task in enumerate(tasks_list):
                prog = status.get(str(i), {}).get("progress", 0.0)
                row = make_task_row(
                    task["task"], task.get("category", ""),
                    task.get("priority", "medium"), prog,
                    on_complete=lambda idx=i: self._complete_task(idx)
                )
                tasks_list_layout.addWidget(row)
        else:
            no_tasks = QLabel("No tasks yet. Click 'Add Tasks' to plan your day!")
            no_tasks.setAlignment(Qt.AlignCenter)
            no_tasks.setStyleSheet(f"color: {COLORS['text_muted']}; padding: 40px; background: transparent; border: none;")
            tasks_list_layout.addWidget(no_tasks)

        tasks_list_layout.addStretch()
        scroll.setWidget(scroll_content)
        tc_layout.addWidget(scroll)
        self.dynamic_layout.addWidget(tasks_card, 1)

        if self.memory_manager:
            mem_card = make_card()
            mc_layout = QVBoxLayout(mem_card)
            mc_layout.setContentsMargins(20, 16, 20, 16)
            mc_layout.setSpacing(8)
            mc_header = QHBoxLayout()
            mc_title = QLabel("Memory")
            mc_title.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: {SIZES['heading_size']}px; font-weight: 600; background: transparent; border: none;")
            mc_header.addWidget(mc_title)
            mc_header.addStretch()
            mc_layout.addLayout(mc_header)
            try:
                stats = self.memory_manager.get_memory_stats()
                entries = stats.get("total_entries", 0)
                days = stats.get("total_days", 0)
                connected = "Connected" if stats.get("cognee_connected") else "Local only"
                mem_info = QLabel(f"Entries: {entries}  |  Days: {days}  |  Cognee: {connected}")
                mem_info.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: {SIZES['small_size']}px; background: transparent; border: none;")
                mc_layout.addWidget(mem_info)
            except Exception:
                mem_info = QLabel("Memory stats unavailable")
                mem_info.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: {SIZES['small_size']}px; background: transparent; border: none;")
                mc_layout.addWidget(mem_info)
            self.dynamic_layout.addWidget(mem_card)

    def _complete_task(self, idx):
        self.task_manager.complete_task(str(idx))
        self.refresh()

    def _clear_layout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                self._clear_layout(child.layout())

    def paintEvent(self, event):
        from PyQt5.QtGui import QPainter, QColor, QLinearGradient
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        grad = QLinearGradient(0, 0, 0, self.height())
        grad.setColorAt(0, QColor(COLORS['bg_primary']))
        grad.setColorAt(1, QColor(COLORS['gradient_end']))
        p.fillRect(self.rect(), grad)
        p.end()
