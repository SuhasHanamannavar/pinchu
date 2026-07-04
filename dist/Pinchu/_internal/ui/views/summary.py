from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QProgressBar
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from ui.design import COLORS, SIZES, make_card, make_stat_card


class SummaryView(QWidget):
    back_clicked = pyqtSignal()

    def __init__(self, task_manager, parent=None):
        super().__init__(parent)
        self.task_manager = task_manager
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
        back_btn = QPushButton("\u2190 Back")
        back_btn.setStyleSheet(f"QPushButton {{ color: {COLORS['text_secondary']}; background: transparent; border: none; font-size: {SIZES['body_size']}px; padding: 8px; }} QPushButton:hover {{ color: {COLORS['accent_secondary']}; }}")
        back_btn.clicked.connect(self.back_clicked.emit)
        header.addWidget(back_btn)
        header.addStretch()
        self.main_layout.addLayout(header)

        title = QLabel("Daily Summary")
        title.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 26px; font-weight: 700; background: transparent; border: none;")
        self.main_layout.addWidget(title)

        self.dynamic_container = QWidget()
        self.dynamic_container.setStyleSheet("background: transparent;")
        self.dynamic_layout = QVBoxLayout(self.dynamic_container)
        self.dynamic_layout.setContentsMargins(0, 0, 0, 0)
        self.dynamic_layout.setSpacing(16)
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
        status = today_data.get("task_status", {})
        classified = today_data.get("classified") or {}
        tasks_list = classified.get("classified_tasks", [])
        total = len(tasks_list)
        done = sum(1 for v in status.values() if v.get("completed"))
        missed = total - done

        stats_row = QHBoxLayout()
        stats_row.setSpacing(14)
        stats_row.addWidget(make_stat_card("Total Tasks", str(total), "Today"))
        stats_row.addWidget(make_stat_card("Completed", str(done), f"{done/total*100:.0f}%" if total else "0%", COLORS['success']))
        stats_row.addWidget(make_stat_card("Missed", str(missed), f"{missed/total*100:.0f}%" if total else "0%", COLORS['danger']))

        partial = sum(1 for i, v in enumerate(status.values())
                      if not v.get("completed") and v.get("progress", 0) > 0)
        stats_row.addWidget(make_stat_card("In Progress", str(partial), "Partially done", COLORS['info']))
        self.dynamic_layout.addLayout(stats_row)

        score = int((done / total * 100) if total > 0 else 0)
        score_card = make_card()
        sc_layout = QVBoxLayout(score_card)
        sc_layout.setContentsMargins(20, 16, 20, 16)
        sc_layout.setSpacing(10)
        sc_title = QLabel("Productivity Score")
        sc_title.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: {SIZES['heading_size']}px; font-weight: 600; background: transparent; border: none;")
        sc_layout.addWidget(sc_title)
        sc_val = QLabel(f"{score}%")
        color = COLORS['success'] if score >= 70 else COLORS['warning'] if score >= 40 else COLORS['danger']
        sc_val.setStyleSheet(f"color: {color}; font-size: 36px; font-weight: 700; background: transparent; border: none;")
        sc_layout.addWidget(sc_val)
        prog = QProgressBar()
        prog.setFixedHeight(10)
        prog.setValue(score)
        prog.setTextVisible(False)
        sc_layout.addWidget(prog)
        self.dynamic_layout.addWidget(score_card)

        if tasks_list:
            completed_card = make_card()
            cc_layout = QVBoxLayout(completed_card)
            cc_layout.setContentsMargins(20, 16, 20, 16)
            cc_layout.setSpacing(4)
            cc_title = QLabel("Completed Tasks")
            cc_title.setStyleSheet(f"color: {COLORS['success']}; font-size: {SIZES['heading_size']}px; font-weight: 600; background: transparent; border: none;")
            cc_layout.addWidget(cc_title)
            has_completed = False
            for i, task in enumerate(tasks_list):
                if status.get(str(i), {}).get("completed"):
                    has_completed = True
                    row = QLabel(f"  \u2713  {task['task']}")
                    row.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: {SIZES['body_size']}px; padding: 6px 0; background: transparent; border: none;")
                    cc_layout.addWidget(row)
            if not has_completed:
                row = QLabel("  No tasks completed yet. Keep going!")
                row.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: {SIZES['body_size']}px; padding: 6px 0; background: transparent; border: none; font-style: italic;")
                cc_layout.addWidget(row)
            self.dynamic_layout.addWidget(completed_card)

        if missed > 0:
            missed_card = make_card()
            mc_layout = QVBoxLayout(missed_card)
            mc_layout.setContentsMargins(20, 16, 20, 16)
            mc_layout.setSpacing(4)
            mc_title = QLabel("Missed Tasks")
            mc_title.setStyleSheet(f"color: {COLORS['danger']}; font-size: {SIZES['heading_size']}px; font-weight: 600; background: transparent; border: none;")
            mc_layout.addWidget(mc_title)
            for i, task in enumerate(tasks_list):
                if not status.get(str(i), {}).get("completed"):
                    row = QLabel(f"  \u2717  {task['task']}")
                    row.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: {SIZES['body_size']}px; padding: 6px 0; background: transparent; border: none;")
                    mc_layout.addWidget(row)
            self.dynamic_layout.addWidget(missed_card)

        motivation_card = make_card()
        mot_layout = QVBoxLayout(motivation_card)
        mot_layout.setContentsMargins(20, 16, 20, 16)
        if score >= 70:
            mot_text = "Amazing work today! You're crushing your goals. Keep it up!"
        elif score >= 40:
            mot_text = "Good progress! Every task completed is a step forward. You've got this!"
        elif total > 0:
            mot_text = "Tough day, but tomorrow is a fresh start. Small steps lead to big wins!"
        else:
            mot_text = "Ready to plan your day? Add some tasks and let's get started!"
        mot_label = QLabel(mot_text)
        mot_label.setStyleSheet(f"color: {COLORS['accent_secondary']}; font-size: {SIZES['body_size']}px; font-style: italic; background: transparent; border: none;")
        mot_label.setWordWrap(True)
        mot_layout.addWidget(mot_label)
        self.dynamic_layout.addWidget(motivation_card)

        self.dynamic_layout.addStretch()

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
        grad = QLinearGradient(0, 0, 0, self.height())
        grad.setColorAt(0, QColor(COLORS['bg_primary']))
        grad.setColorAt(1, QColor(COLORS['gradient_end']))
        p.fillRect(self.rect(), grad)
        p.end()
