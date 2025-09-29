# app/ui/appearance.py
from __future__ import annotations
from pathlib import Path
import json
from typing import Dict

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor, QPalette
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QTextEdit, QPlainTextEdit, QTableWidget, QHeaderView, QComboBox, QPushButton

APP_SETTINGS = Path.home() / ".enepol_ui_prefs.json"

DEFAULT_PREFS: Dict[str, object] = {
    "family": "Segoe UI",
    "size": 10,
    "weight": 50,            # 0..99  sendo 50 normal, 63 semibold, 75 bold
    "italic": False,
    "color": "#1E293B",      # Slate 800
    "align_labels": "left",  # left, center, right
    "align_inputs": "left",  # left, center, right
    "align_headers": "center"
}

def load_prefs() -> Dict[str, object]:
    try:
        if APP_SETTINGS.exists():
            return {**DEFAULT_PREFS, **json.loads(APP_SETTINGS.read_text(encoding="utf-8"))}
    except Exception:
        pass
    return DEFAULT_PREFS.copy()

def save_prefs(prefs: Dict[str, object]) -> None:
    try:
        APP_SETTINGS.write_text(json.dumps(prefs, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass

# ---------- aplicação global ----------

def apply_global_font(family: str, size: int, weight: int, italic: bool) -> None:
    app = QApplication.instance()
    if not app:
        return
    f = QFont(family, int(size))
    f.setWeight(int(weight))
    f.setItalic(bool(italic))
    app.setFont(f)

def apply_global_text_color(hex_color: str) -> None:
    app = QApplication.instance()
    if not app:
        return
    c = QColor(hex_color)
    pal: QPalette = app.palette()
    pal.setColor(QPalette.ColorRole.WindowText, c)
    pal.setColor(QPalette.ColorRole.Text, c)
    pal.setColor(QPalette.ColorRole.ButtonText, c)
    pal.setColor(QPalette.ColorRole.ToolTipText, c)
    pal.setColor(QPalette.ColorRole.PlaceholderText, QColor(c).lighter(160))
    app.setPalette(pal)

def _to_align(value: str) -> Qt.AlignmentFlag:
    v = (value or "left").lower()
    if v == "center":
        return Qt.AlignmentFlag.AlignHCenter
    if v == "right":
        return Qt.AlignmentFlag.AlignRight
    return Qt.AlignmentFlag.AlignLeft

def apply_alignments(root: QWidget, align_labels: str, align_inputs: str, align_headers: str) -> None:
    """Alinha textos de rótulos, entradas e cabeçalhos em toda a subárvore."""
    a_labels  = _to_align(align_labels)  | Qt.AlignmentFlag.AlignVCenter
    a_inputs  = _to_align(align_inputs)  | Qt.AlignmentFlag.AlignVCenter
    a_headers = _to_align(align_headers) | Qt.AlignmentFlag.AlignVCenter

    for w in root.findChildren(QLabel):
        # evita mexer em logos e ícones sem texto
        if w.text():
            w.setAlignment(a_labels)

    for w in root.findChildren(QLineEdit):
        w.setAlignment(a_inputs)

    for w in root.findChildren(QTextEdit):
        # QTextEdit alinha parágrafo atual
        cursor = w.textCursor()
        block_format = cursor.blockFormat()
        block_format.setAlignment(a_inputs)
        cursor.setBlockFormat(block_format)
        w.setTextCursor(cursor)

    for w in root.findChildren(QPlainTextEdit):
        # QPlainTextEdit não tem alinhamento horizontal global
        # truque leve com fonte monoespaçada, porém mantemos padrão do app
        pass

    for w in root.findChildren(QTableWidget):
        header = w.horizontalHeader()
        if isinstance(header, QHeaderView):
            header.setDefaultAlignment(a_headers)

def apply_typography_everywhere(root: QWidget, prefs: Dict[str, object]) -> None:
    apply_global_font(
        str(prefs.get("family", DEFAULT_PREFS["family"])),
        int(prefs.get("size", DEFAULT_PREFS["size"])),
        int(prefs.get("weight", DEFAULT_PREFS["weight"])),
        bool(prefs.get("italic", DEFAULT_PREFS["italic"]))
    )
    apply_global_text_color(str(prefs.get("color", DEFAULT_PREFS["color"])))
    apply_alignments(
        root,
        str(prefs.get("align_labels", DEFAULT_PREFS["align_labels"])),
        str(prefs.get("align_inputs", DEFAULT_PREFS["align_inputs"])),
        str(prefs.get("align_headers", DEFAULT_PREFS["align_headers"])),
    )
