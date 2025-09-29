# app/ui/table_theme.py
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QHeaderView, QAbstractItemView, QTableView, QTableWidget, QWidget
)

PRIMARY_LIGHT = "#e9f0ff"
PRIMARY_BORDER = "#dde6ff"
ALT_ROW = "#f8fbff"
SELECTION_BG = "#dbe6ff"
SELECTION_FG = "#0f1d33"
TEXT = "#1c2a39"

QSS_TABLE = f"""
QTableView, QTableWidget {{
    background: white;
    gridline-color: {PRIMARY_BORDER};
    border: 1px solid {PRIMARY_BORDER};
    border-radius: 8px;
    selection-background-color: {SELECTION_BG};
    selection-color: {SELECTION_FG};
    alternate-background-color: {ALT_ROW};
    color: {TEXT};
}}
QHeaderView::section {{
    background: {PRIMARY_LIGHT};
    color: {TEXT};
    font-weight: 600;
    border: 0px;
    border-right: 1px solid {PRIMARY_BORDER};
    padding: 8px 10px;
}}
QTableCornerButton::section {{
    background: {PRIMARY_LIGHT};
    border: 0px;
    border-right: 1px solid {PRIMARY_BORDER};
    border-bottom: 1px solid {PRIMARY_BORDER};
}}
"""

def style_single_table(table: QTableView | QTableWidget, editable: bool = True) -> None:
    table.setAlternatingRowColors(True)
    table.setShowGrid(True)
    table.setStyleSheet(QSS_TABLE)

    # Edição liberada por padrão
    if editable:
        table.setEditTriggers(
            QAbstractItemView.EditTrigger.DoubleClicked
            | QAbstractItemView.EditTrigger.SelectedClicked
            | QAbstractItemView.EditTrigger.EditKeyPressed
        )
    else:
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

    table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

    if table.verticalHeader():
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setDefaultSectionSize(36)

    font = QFont()
    font.setPointSize(10)
    table.setFont(font)

    header = table.horizontalHeader()
    header.setStretchLastSection(True)
    header.setHighlightSections(False)
    header.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

def apply_table_theme(root_widget: QWidget, editable: bool = True) -> None:
    for t in root_widget.findChildren(QTableView):
        style_single_table(t, editable=editable)
    for t in root_widget.findChildren(QTableWidget):
        style_single_table(t, editable=editable)
