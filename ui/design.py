import platform
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor

IS_MACOS = platform.system() == "Darwin"

COLORS = {
    "bg_primary": "#0d0b14",
    "bg_secondary": "#161225",
    "bg_card": "#1c1730",
    "bg_card_hover": "#231e3a",
    "bg_sidebar": "#110e1c",
    "accent_primary": "#9b6dff",
    "accent_secondary": "#c49bff",
    "accent_glow": "#7c4dff",
    "accent_dark": "#5a3db8",
    "text_primary": "#f0eaf8",
    "text_secondary": "#a99bc0",
    "text_muted": "#6b5d85",
    "border": "#2a2240",
    "border_light": "#3a2f55",
    "success": "#4ade80",
    "warning": "#fbbf24",
    "danger": "#f87171",
    "info": "#60a5fa",
    "gradient_start": "#1a1230",
    "gradient_end": "#0d0820",
    "card_gradient_start": "#1e1838",
    "card_gradient_end": "#15102a",
    "sidebar_active": "#2a1f45",
    "sidebar_hover": "#1e1835",
    "purple_light": "#d4b8ff",
    "purple_dark": "#3d1f6d",
    "text_white": "#ffffff",
}

if IS_MACOS:
    FONTS = {
        "heading": "SF Pro Display",
        "body": "SF Pro Text",
        "mono": "SF Mono",
        "accent": "SF Pro Display Bold",
    }
else:
    FONTS = {
        "heading": "Segoe UI",
        "body": "Segoe UI",
        "mono": "Cascadia Code",
        "accent": "Segoe UI Semibold",
    }

SIZES = {
    "sidebar_width": 220,
    "card_radius": 16,
    "button_radius": 12,
    "input_radius": 10,
    "icon_size": 20,
    "avatar_size": 36,
    "title_size": 22,
    "heading_size": 16,
    "body_size": 13,
    "small_size": 11,
    "tiny_size": 9,
}

MAIN_STYLESHEET = f"""
QMainWindow, QWidget {{
    background-color: {COLORS['bg_primary']};
    color: {COLORS['text_primary']};
    font-family: '{FONTS["body"]}';
    font-size: {SIZES['body_size']}px;
}}

QScrollBar:vertical {{
    background: {COLORS['bg_secondary']};
    width: 8px;
    border-radius: 4px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {COLORS['border_light']};
    border-radius: 4px;
    min-height: 30px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: none;
}}

QScrollBar:horizontal {{
    background: {COLORS['bg_secondary']};
    height: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:horizontal {{
    background: {COLORS['border_light']};
    border-radius: 4px;
    min-width: 30px;
}}

QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: {COLORS['bg_card']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: {SIZES['input_radius']}px;
    padding: 10px 14px;
    font-size: {SIZES['body_size']}px;
    selection-background-color: {COLORS['accent_primary']};
}}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border: 1px solid {COLORS['accent_primary']};
}}

QPushButton {{
    background-color: {COLORS['accent_primary']};
    color: {COLORS['text_white']};
    border: none;
    border-radius: {SIZES['button_radius']}px;
    padding: 10px 24px;
    font-size: {SIZES['body_size']}px;
    font-weight: 600;
}}
QPushButton:hover {{
    background-color: {COLORS['accent_secondary']};
}}
QPushButton:pressed {{
    background-color: {COLORS['accent_dark']};
}}
QPushButton:disabled {{
    background-color: {COLORS['border']};
    color: {COLORS['text_muted']};
}}

QPushButton.secondary {{
    background-color: transparent;
    border: 1px solid {COLORS['border_light']};
    color: {COLORS['text_secondary']};
}}
QPushButton.secondary:hover {{
    background-color: {COLORS['bg_card']};
    border-color: {COLORS['accent_primary']};
    color: {COLORS['text_primary']};
}}

QLabel {{
    color: {COLORS['text_primary']};
    background: transparent;
}}

QLabel.muted {{
    color: {COLORS['text_secondary']};
}}

QLabel.heading {{
    font-size: {SIZES['heading_size']}px;
    font-weight: 600;
    color: {COLORS['text_primary']};
}}

QLabel.title {{
    font-size: {SIZES['title_size']}px;
    font-weight: 700;
    color: {COLORS['text_primary']};
}}

QFrame.card {{
    background-color: {COLORS['bg_card']};
    border: 1px solid {COLORS['border']};
    border-radius: {SIZES['card_radius']}px;
    padding: 20px;
}}

QFrame.sidebar {{
    background-color: {COLORS['bg_sidebar']};
    border-right: 1px solid {COLORS['border']};
}}

QProgressBar {{
    background-color: {COLORS['bg_card']};
    border: none;
    border-radius: 6px;
    height: 8px;
    text-align: center;
    color: transparent;
}}
QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {COLORS['accent_primary']}, stop:1 {COLORS['accent_secondary']});
    border-radius: 6px;
}}

QComboBox {{
    background-color: {COLORS['bg_card']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: {SIZES['input_radius']}px;
    padding: 8px 12px;
    font-size: {SIZES['body_size']}px;
}}
QComboBox::drop-down {{
    border: none;
    width: 30px;
}}
QComboBox QAbstractItemView {{
    background-color: {COLORS['bg_card']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    selection-background-color: {COLORS['accent_primary']};
}}

QTabWidget::pane {{
    border: 1px solid {COLORS['border']};
    border-radius: {SIZES['card_radius']}px;
    background-color: {COLORS['bg_card']};
}}
QTabBar::tab {{
    background-color: {COLORS['bg_secondary']};
    color: {COLORS['text_secondary']};
    border: none;
    padding: 10px 20px;
    font-size: {SIZES['body_size']}px;
    border-top-left-radius: {SIZES['card_radius']}px;
    border-top-right-radius: {SIZES['card_radius']}px;
}}
QTabBar::tab:selected {{
    background-color: {COLORS['bg_card']};
    color: {COLORS['accent_secondary']};
}}

QToolTip {{
    background-color: {COLORS['bg_card']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border_light']};
    border-radius: 6px;
    padding: 6px 10px;
    font-size: {SIZES['small_size']}px;
}}
"""


def make_card(style="default"):
    from PyQt5.QtWidgets import QFrame
    frame = QFrame()
    frame.setProperty("class", "card")
    frame.setStyleSheet(f"""
        QFrame {{
            background-color: {COLORS['bg_card']};
            border: 1px solid {COLORS['border']};
            border-radius: {SIZES['card_radius']}px;
        }}
        QFrame:hover {{
            border-color: {COLORS['border_light']};
        }}
    """)
    return frame


def make_sidebar_button(text, icon_char="", active=False):
    from PyQt5.QtWidgets import QPushButton
    from PyQt5.QtCore import QSize
    btn = QPushButton(text)
    btn.setIconSize(QSize(SIZES['icon_size'], SIZES['icon_size']))
    bg = COLORS['sidebar_active'] if active else "transparent"
    hover = COLORS['sidebar_hover']
    color = COLORS['text_primary'] if active else COLORS['text_secondary']
    btn.setStyleSheet(f"""
        QPushButton {{
            background-color: {bg};
            color: {color};
            border: none;
            border-radius: 10px;
            padding: 12px 16px;
            text-align: left;
            font-size: {SIZES['body_size']}px;
            font-weight: {'600' if active else '400'};
        }}
        QPushButton:hover {{
            background-color: {hover};
        }}
    """)
    return btn


def make_stat_card(title, value, subtitle="", accent_color=None):
    from PyQt5.QtWidgets import QVBoxLayout, QLabel, QFrame
    from PyQt5.QtCore import Qt
    if accent_color is None:
        accent_color = COLORS['accent_primary']
    card = make_card()
    layout = QVBoxLayout(card)
    layout.setSpacing(6)
    layout.setContentsMargins(18, 16, 18, 16)
    lbl_title = QLabel(title)
    lbl_title.setProperty("class", "muted")
    lbl_title.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: {SIZES['small_size']}px; background: transparent; border: none;")
    lbl_value = QLabel(value)
    lbl_value.setStyleSheet(f"color: {accent_color}; font-size: 24px; font-weight: 700; background: transparent; border: none;")
    layout.addWidget(lbl_title)
    layout.addWidget(lbl_value)
    if subtitle:
        lbl_sub = QLabel(subtitle)
        lbl_sub.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: {SIZES['tiny_size']}px; background: transparent; border: none;")
        layout.addWidget(lbl_sub)
    return card


def make_task_row(task_text, category, priority, progress=0.0, on_complete=None):
    from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QProgressBar, QPushButton
    from PyQt5.QtCore import Qt
    row = QWidget()
    row.setStyleSheet(f"background: transparent;")
    h = QHBoxLayout(row)
    h.setContentsMargins(16, 12, 16, 12)
    h.setSpacing(14)

    color_map = {"high": COLORS['danger'], "medium": COLORS['warning'], "low": COLORS['info']}
    pri_color = color_map.get(priority, COLORS['text_secondary'])

    cat_colors = {
        "work": COLORS['accent_primary'], "health": COLORS['success'],
        "learning": COLORS['info'], "personal": COLORS['warning'],
        "creative": "#f472b6",
    }
    cat_color = cat_colors.get(category, COLORS['text_secondary'])

    dot = QLabel("●")
    dot.setFixedWidth(18)
    dot.setStyleSheet(f"color: {cat_color}; font-size: 14px; background: transparent; border: none;")
    h.addWidget(dot)

    text_col = QVBoxLayout()
    text_col.setSpacing(2)
    lbl_task = QLabel(task_text)
    lbl_task.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: {SIZES['body_size']}px; background: transparent; border: none;")
    text_col.addWidget(lbl_task)
    lbl_meta = QLabel(f"{category.title()}  •  {priority.title()}")
    lbl_meta.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: {SIZES['tiny_size']}px; background: transparent; border: none;")
    text_col.addWidget(lbl_meta)
    h.addLayout(text_col, 1)

    prog_col = QVBoxLayout()
    prog_col.setSpacing(4)
    prog_bar = QProgressBar()
    prog_bar.setFixedWidth(120)
    prog_bar.setFixedHeight(8)
    prog_bar.setValue(int(progress * 100))
    prog_bar.setTextVisible(False)
    prog_col.addWidget(prog_bar)
    lbl_pct = QLabel(f"{int(progress*100)}%")
    lbl_pct.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: {SIZES['tiny_size']}px; background: transparent; border: none;")
    prog_col.addWidget(lbl_pct)
    h.addLayout(prog_col)

    if progress < 1.0:
        btn = QPushButton("\u2713")
        btn.setFixedSize(36, 36)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setToolTip("Mark as complete")
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_card_hover']};
                border: 2px solid {COLORS['border_light']};
                border-radius: 18px;
                color: {COLORS['accent_secondary']};
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent_primary']};
                color: white;
                border-color: {COLORS['accent_primary']};
            }}
            QPushButton:pressed {{
                background-color: {COLORS['accent_dark']};
            }}
        """)
        if on_complete:
            btn.clicked.connect(on_complete)
        h.addWidget(btn)
    else:
        lbl_done = QLabel("\u2713")
        lbl_done.setStyleSheet(f"color: {COLORS['success']}; font-size: 18px; font-weight: bold; background: transparent; border: none;")
        h.addWidget(lbl_done)

    return row
