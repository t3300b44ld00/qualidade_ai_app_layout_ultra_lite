# app/ui/button_theme.py
from PyQt6.QtWidgets import QWidget

QSS_BUTTONS = """
QPushButton {
    background: #ffffff;
    color: #1c2a39;
    border: 1px solid #dde6ff;
    border-radius: 10px;
    padding: 6px 14px;
    min-height: 28px;
}
QPushButton:hover {
    background: #f5f9ff;
}
QPushButton:pressed {
    background: #e9f0ff;
}

/* Variações por propriedade */
QPushButton[kind="primary"] {
    background: #2b6dff;
    color: #ffffff;
    border: 1px solid #2b6dff;
}
QPushButton[kind="primary"]:hover { filter: brightness(1.04); }
QPushButton[kind="primary"]:pressed { filter: brightness(0.96); }

QPushButton[kind="outline"] {
    background: #ffffff;
    color: #2b6dff;
    border: 1px solid #2b6dff;
}

QPushButton[kind="danger"] {
    background: #fff5f5;
    color: #b00020;
    border: 1px solid #ffcccc;
}
"""

def apply_button_theme(root: QWidget) -> None:
    # aplica nos descendentes sem quebrar o style.qss existente
    root.setStyleSheet(root.styleSheet() + "\n" + QSS_BUTTONS)
