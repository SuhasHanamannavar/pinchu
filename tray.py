from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QRadialGradient, QFont
from PyQt5.QtCore import pyqtSignal, QObject


def create_tray_icon():
    pixmap = QPixmap(64, 64)
    pixmap.fill(QColor(0, 0, 0, 0))
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    grad = QRadialGradient(32, 32, 30)
    grad.setColorAt(0, QColor("#c49bff"))
    grad.setColorAt(1, QColor("#7c4dff"))
    painter.setBrush(grad)
    painter.setPen(QColor(0, 0, 0, 0))
    painter.drawEllipse(4, 4, 56, 56)
    painter.setPen(QColor("#ffffff"))
    font = QFont("Segoe UI", 28, QFont.Bold)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), 0x84 | 0x80, "P")
    painter.end()
    return QIcon(pixmap)


class TrayIcon(QObject):
    show_dashboard = pyqtSignal()
    show_overlay = pyqtSignal()
    quit_app = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.tray = QSystemTrayIcon()
        self.tray.setIcon(create_tray_icon())
        self.tray.setToolTip("Pinchu - Your Productivity Buddy")

        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: #1c1730;
                color: #f0eaf8;
                border: 1px solid #2a2240;
                border-radius: 8px;
                padding: 4px;
            }
            QMenu::item {
                padding: 8px 24px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #9b6dff;
            }
        """)

        show_action = QAction("Open Dashboard")
        show_action.triggered.connect(self.show_dashboard.emit)
        menu.addAction(show_action)

        overlay_action = QAction("Show Pinchu")
        overlay_action.triggered.connect(self.show_overlay.emit)
        menu.addAction(overlay_action)

        menu.addSeparator()

        quit_action = QAction("Quit")
        quit_action.triggered.connect(self.quit_app.emit)
        menu.addAction(quit_action)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_activate)
        self.tray.show()

    def _on_activate(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_dashboard.emit()

    def show_notification(self, title: str, message: str, duration: int = 5000):
        self.tray.showMessage(title, message, QSystemTrayIcon.Information, duration)

    def hide(self):
        self.tray.hide()
