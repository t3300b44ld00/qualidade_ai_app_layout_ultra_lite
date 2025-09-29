# app/ui/screens/testes.py
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QComboBox,
    QHBoxLayout, QPushButton, QLabel, QSizePolicy, QLineEdit, QMessageBox
)
from PyQt6.QtGui import QFont


TIPOS_TESTE = [
    "Plaqueta Forno",
    "Plaqueta Imersão",
    "Tração",
    "Impacto",
    "Outro",
]


class TestesQualidadeWidget(QWidget):
    """
    Tela minimalista: tabela com 3 colunas + rodapé de navegação e botão Gravar.
    Integra com a tabela SQLite 'testes_qualidade' (cria se não existir).
    Colunas esperadas: codigo (PK), tipo, descricao.
    """
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self._ensure_table()

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        # ---------- Tabela ----------
        self.table = QTableWidget(0, 3, self)
        self.table.setHorizontalHeaderLabels(["Cód. Teste", "Tipo de Teste", "Descrição"])
        self.table.setSelectionBehavior(self.table.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(self.table.SelectionMode.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(True)
        self.table.setAlternatingRowColors(False)
        self.table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Colunas: largura confortável; usuário pode redimensionar
        header = self.table.horizontalHeader()
        try:
            from PyQt6.QtWidgets import QHeaderView
            header.setStretchLastSection(True)
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        except Exception:
            pass

        root.addWidget(self.table)

        # ---------- Rodapé (navegação + gravar + contador) ----------
        foot = QHBoxLayout()
        foot.setSpacing(6)

        def _mk_btn(txt, w=36):
            b = QPushButton(txt)
            b.setProperty("kind", "outline")
            b.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            b.setFixedWidth(w)
            return b

        self.btn_first = _mk_btn("⏮")
        self.btn_prev  = _mk_btn("⟨", 30)
        self.btn_next  = _mk_btn("⟩", 30)
        self.btn_last  = _mk_btn("⏭")

        self.btn_save  = QPushButton("Gravar")
        self.btn_save.setProperty("kind", "primary")
        self.btn_save.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_save.setFixedWidth(90)

        foot.addWidget(self.btn_first)
        foot.addWidget(self.btn_prev)
        foot.addWidget(self.btn_next)
        foot.addWidget(self.btn_last)
        foot.addSpacing(10)
        foot.addWidget(self.btn_save)
        foot.addStretch(1)

        self.lbl_count = QLabel("Registros 0 de 0")
        fnt = QFont(self.font())
        fnt.setPointSize(fnt.pointSize() + 1)
        self.lbl_count.setFont(fnt)
        foot.addWidget(self.lbl_count)

        root.addLayout(foot)

        # dados
        self._load_rows()
        self._update_counter()

        # sinais
        sel = self.table.selectionModel()
        if sel is not None:
            sel.selectionChanged.connect(self._update_counter)
        self.btn_first.clicked.connect(lambda: self._goto("first"))
        self.btn_prev.clicked.connect(lambda: self._goto("prev"))
        self.btn_next.clicked.connect(lambda: self._goto("next"))
        self.btn_last.clicked.connect(lambda: self._goto("last"))
        self.btn_save.clicked.connect(self._save_all)

    # -------------------- DB helpers --------------------
    def _ensure_table(self):
        try:
            cur = self.db.conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS testes_qualidade (
                    codigo    TEXT PRIMARY KEY,
                    tipo      TEXT,
                    descricao TEXT
                )
            """)
            self.db.conn.commit()
        except Exception:
            pass

    def _load_rows(self):
        self.table.setRowCount(0)
        rows = []
        try:
            cur = self.db.conn.cursor()
            cur.execute("SELECT codigo, tipo, descricao FROM testes_qualidade ORDER BY codigo")
            rows = cur.fetchall()
        except Exception:
            rows = []

        # se vazio, preenche exemplos como na imagem
        if not rows:
            rows = [
                ("PF01", "Plaqueta Forno", "Composto Micronizado"),
                ("PF02", "Plaqueta Forno", "Composto Micropellet"),
                ("PF03", "Plaqueta Forno", "Composto Minipellet"),
            ]
        for r in rows:
            self._append_row(r[0] or "", r[1] or "", r[2] or "")

        if self.table.rowCount() > 0:
            self.table.selectRow(0)

    # -------------------- Tabela (linhas/editores) --------------------
    def _append_row(self, codigo: str, tipo: str, descricao: str):
        row = self.table.rowCount()
        self.table.insertRow(row)

        # Cód. Teste (editável)
        item_codigo = QTableWidgetItem(codigo)
        item_codigo.setFlags(
            Qt.ItemFlag.ItemIsEnabled |
            Qt.ItemFlag.ItemIsSelectable |
            Qt.ItemFlag.ItemIsEditable
        )
        self.table.setItem(row, 0, item_codigo)

        # Tipo (combo)
        cmb = QComboBox()
        cmb.addItems(TIPOS_TESTE)
        idx = cmb.findText(tipo)
        cmb.setCurrentIndex(idx if idx >= 0 else 0)
        cmb.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table.setCellWidget(row, 1, cmb)

        # Descrição (editável)
        item_desc = QTableWidgetItem(descricao)
        item_desc.setFlags(
            Qt.ItemFlag.ItemIsEnabled |
            Qt.ItemFlag.ItemIsSelectable |
            Qt.ItemFlag.ItemIsEditable
        )
        self.table.setItem(row, 2, item_desc)

    def _current_row(self):
        r = self.table.currentRow()
        if r < 0 and self.table.rowCount() > 0:
            r = 0
        return r

    def _goto(self, where: str):
        n = self.table.rowCount()
        if n == 0:
            return
        r = self._current_row()
        if where == "first":
            r = 0
        elif where == "prev":
            r = max(0, r - 1)
        elif where == "next":
            r = min(n - 1, r + 1)
        elif where == "last":
            r = n - 1
        self.table.selectRow(r)
        self._update_counter()

    def _update_counter(self, *_):
        n = self.table.rowCount()
        r = self._current_row()
        self.lbl_count.setText(f"Registros {1 if n and r>=0 else 0} de {n}" if n else "Registros 0 de 0")
        if n and r >= 0:
            self.lbl_count.setText(f"Registros {r+1} de {n}")

    # -------------------- Gravar --------------------
    def _save_all(self):
        """
        Salva todas as linhas na tabela 'testes_qualidade'.
        Faz upsert por 'codigo'.
        """
        try:
            cur = self.db.conn.cursor()
            cur.execute("BEGIN")
            # opcional: garantir tabela existente
            self._ensure_table()

            for row in range(self.table.rowCount()):
                codigo = (self.table.item(row, 0).text() if self.table.item(row, 0) else "").strip()
                tipo_w = self.table.cellWidget(row, 1)
                tipo = tipo_w.currentText().strip() if isinstance(tipo_w, QComboBox) else ""
                descricao = (self.table.item(row, 2).text() if self.table.item(row, 2) else "").strip()

                if not codigo:
                    # ignora linhas sem código
                    continue

                # UPSERT por 'codigo'
                cur.execute("""
                    INSERT INTO testes_qualidade (codigo, tipo, descricao)
                    VALUES (?, ?, ?)
                    ON CONFLICT(codigo) DO UPDATE SET
                        tipo = excluded.tipo,
                        descricao = excluded.descricao
                """, (codigo, tipo, descricao))

            self.db.conn.commit()
            QMessageBox.information(self, "Testes", "Registros gravados com sucesso.")
        except Exception as e:
            try:
                self.db.conn.rollback()
            except Exception:
                pass
            QMessageBox.warning(self, "Testes", f"Falha ao gravar.\n{e}")
