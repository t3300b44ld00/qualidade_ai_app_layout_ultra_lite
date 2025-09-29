# app/ui/font_prefs_dialog.py
from __future__ import annotations
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QFontComboBox, QSpinBox,
    QCheckBox, QComboBox, QPushButton, QColorDialog
)

from .appearance import load_prefs, save_prefs, apply_typography_everywhere

class FontPrefsDialog(QDialog):
    def __init__(self, root_for_preview, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Aparência e Tipografia")
        self.setModal(True)
        self._root = root_for_preview

        p = load_prefs()

        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(10)

        # Linha 1: família, tamanho, peso, itálico
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Família"))
        self.cmb_family = QFontComboBox()
        self.cmb_family.setCurrentFont(self.cmb_family.currentFont())
        self.cmb_family.setEditable(False)
        self.cmb_family.setCurrentText(str(p.get("family")))
        row1.addWidget(self.cmb_family, 1)

        row1.addWidget(QLabel("Tamanho"))
        self.sp_size = QSpinBox(); self.sp_size.setRange(8, 28); self.sp_size.setValue(int(p.get("size", 10)))
        row1.addWidget(self.sp_size)

        row1.addWidget(QLabel("Peso"))
        self.cmb_weight = QComboBox()
        self.cmb_weight.addItems(["Thin 12", "Light 25", "Regular 50", "Semibold 63", "Bold 75", "Black 87"])
        # converte para índice aproximado
        w = int(p.get("weight", 50))
        idx = 2 if w <= 50 else 3 if w <= 63 else 4 if w <= 75 else 5
        self.cmb_weight.setCurrentIndex(idx)
        row1.addWidget(self.cmb_weight)

        self.chk_italic = QCheckBox("Itálico")
        self.chk_italic.setChecked(bool(p.get("italic", False)))
        row1.addWidget(self.chk_italic)

        lay.addLayout(row1)

        # Linha 2: cor da fonte e alinhamentos
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Cor da fonte"))
        self.btn_color = QPushButton(str(p.get("color"))); self.btn_color.setProperty("kind", "outline")
        self.btn_color.clicked.connect(self._pick_color)
        row2.addWidget(self.btn_color)

        row2.addSpacing(16)
        row2.addWidget(QLabel("Rótulos"))
        self.cmb_align_labels = QComboBox(); self.cmb_align_labels.addItems(["left", "center", "right"])
        self.cmb_align_labels.setCurrentText(str(p.get("align_labels", "left")))
        row2.addWidget(self.cmb_align_labels)

        row2.addWidget(QLabel("Entradas"))
        self.cmb_align_inputs = QComboBox(); self.cmb_align_inputs.addItems(["left", "center", "right"])
        self.cmb_align_inputs.setCurrentText(str(p.get("align_inputs", "left")))
        row2.addWidget(self.cmb_align_inputs)

        row2.addWidget(QLabel("Cabeçalhos"))
        self.cmb_align_headers = QComboBox(); self.cmb_align_headers.addItems(["left", "center", "right"])
        self.cmb_align_headers.setCurrentText(str(p.get("align_headers", "center")))
        row2.addWidget(self.cmb_align_headers)

        lay.addLayout(row2)

        # Ações
        actions = QHBoxLayout()
        actions.addStretch(1)
        self.btn_preview = QPushButton("Aplicar prévia")
        self.btn_ok = QPushButton("Salvar"); self.btn_ok.setProperty("kind", "primary")
        self.btn_cancel = QPushButton("Cancelar"); self.btn_cancel.setProperty("kind", "outline")
        actions.addWidget(self.btn_preview); actions.addWidget(self.btn_ok); actions.addWidget(self.btn_cancel)
        lay.addLayout(actions)

        self.btn_preview.clicked.connect(self._preview)
        self.btn_ok.clicked.connect(self._save_and_close)
        self.btn_cancel.clicked.connect(self.reject)

    def _pick_color(self):
        c = QColorDialog.getColor(QColor(self.btn_color.text()), self, "Escolher cor da fonte")
        if c.isValid():
            self.btn_color.setText(c.name())

    def _collect(self):
        map_weight = {0:12, 1:25, 2:50, 3:63, 4:75, 5:87}
        return {
            "family": self.cmb_family.currentText(),
            "size": int(self.sp_size.value()),
            "weight": int(map_weight.get(self.cmb_weight.currentIndex(), 50)),
            "italic": bool(self.chk_italic.isChecked()),
            "color": self.btn_color.text(),
            "align_labels": self.cmb_align_labels.currentText(),
            "align_inputs": self.cmb_align_inputs.currentText(),
            "align_headers": self.cmb_align_headers.currentText(),
        }

    def _preview(self):
        prefs = self._collect()
        apply_typography_everywhere(self._root, prefs)

    def _save_and_close(self):
        prefs = self._collect()
        save_prefs(prefs)
        apply_typography_everywhere(self._root, prefs)
        self.accept()
