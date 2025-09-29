# app/ui/screens/analise_cliente.py
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QPushButton, QTableWidget, QTableWidgetItem, QCheckBox, QHeaderView,
    QAbstractScrollArea, QRadioButton, QMessageBox
)

COL_SIM   = 0
COL_DESC  = 1
COL_MIN   = 2
COL_MAX   = 3

class AnaliseClienteWidget(QWidget):
    """
    Tela Análise/Cliente:
      - Cliente (combo) + 'Produtos do Cliente' + 'Gravar / Sair'
      - Código (combo), Descrição (linha)
      - Ensaio: Analítico | Orientativo
      - Grid: Sim? | Análises Básicas | Especificação Mínima | Especificação Máxima
      - Sem barra de rolagem: a altura da tabela se ajusta ao conteúdo
      - Sempre mantém uma linha vazia no final
    Persiste em 'analises_cliente' (cria a tabela se não existir).
    """

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self._ensure_table()

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        # *** REMOVIDO PageBar interno (era o "banner" destacado) ***

        # Linha 1: Cliente + botões
        l1 = QHBoxLayout()
        l1.setSpacing(8)
        l1.addWidget(QLabel("Cliente"))
        self.cmb_cliente = QComboBox(); self.cmb_cliente.setEditable(True)
        self.cmb_cliente.setMinimumWidth(460)
        self.cmb_cliente.lineEdit().setPlaceholderText("Digite/Selecione o cliente")
        l1.addWidget(self.cmb_cliente, 1)

        self.btn_produtos_cli = QPushButton("Produtos do Cliente"); self.btn_produtos_cli.setProperty("kind", "outline")
        self.btn_gravar_sair  = QPushButton("Gravar / Sair");       self.btn_gravar_sair.setProperty("kind", "primary")
        self.btn_gravar_sair.clicked.connect(self._on_save_and_exit)

        l1.addWidget(self.btn_produtos_cli)
        l1.addWidget(self.btn_gravar_sair)
        root.addLayout(l1)

        # Linha 2: Código + Descrição + Ensaio
        l2 = QHBoxLayout()
        l2.setSpacing(8)

        l2.addWidget(QLabel("Código"))
        self.cmb_codigo = QComboBox(); self.cmb_codigo.setEditable(True)
        self.cmb_codigo.setMinimumWidth(140)
        self.cmb_codigo.lineEdit().setPlaceholderText("Código")
        l2.addWidget(self.cmb_codigo)

        l2.addWidget(QLabel("Descrição"))
        self.ed_descricao = QLineEdit(); self.ed_descricao.setPlaceholderText("Descrição")
        self.ed_descricao.setMinimumWidth(380)
        l2.addWidget(self.ed_descricao, 1)

        l2.addWidget(QLabel("Ensaio"))
        self.rb_analitico   = QRadioButton("Analítico")
        self.rb_orientativo = QRadioButton("Orientativo")
        self.rb_analitico.setChecked(True)
        l2.addWidget(self.rb_analitico)
        l2.addWidget(self.rb_orientativo)

        root.addLayout(l2)

        # Tabela
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels([
            "Sim?", "Análises Básicas", "Especificação Mínima", "Especificação Máxima"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.AllEditTriggers)

        # Sem scroll (altura autoadaptável)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.table.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)

        self.table.itemChanged.connect(self._maybe_append_empty_row)

        root.addWidget(self.table)

        # Rodapé
        foot = QHBoxLayout()
        self.lbl_qtde = QLabel("Quantidade de Ensaios: 0")
        foot.addWidget(self.lbl_qtde); foot.addStretch(1)
        root.addLayout(foot)

        # Sinais
        self.cmb_cliente.currentTextChanged.connect(self._on_cliente_changed)
        self.cmb_codigo.currentTextChanged.connect(self._on_codigo_changed)
        self.btn_produtos_cli.clicked.connect(self._load_codigos_do_cliente)

        # Inicialização
        self._load_clientes()
        self._append_empty_row()
        self._autosize_table()
        self._update_count()

    # ------------------------------- DB ---------------------------------
    def _ensure_table(self):
        cur = self.db.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS analises_cliente (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente TEXT,
                codigo  TEXT,
                descricao TEXT,
                tipo_ensaio TEXT,
                sim INTEGER DEFAULT 0,
                analise TEXT,
                espec_min TEXT,
                espec_max TEXT
            )
            """
        )
        self.db.conn.commit()

    def _load_clientes(self):
        self.cmb_cliente.clear()
        cur = self.db.conn.cursor()
        nomes = []
        for tb in ("clientes", "tb_clientes", "client", "customer", "cad_clientes"):
            try:
                cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND LOWER(name)=?", (tb,))
                if cur.fetchone():
                    for col in ("nome", "cliente", "razao", "descricao", "name"):
                        try:
                            cur.execute(f"SELECT {col} FROM {tb} WHERE {col} IS NOT NULL ORDER BY {col}")
                            nomes = [r[0] for r in cur.fetchall()]
                            if nomes: break
                        except Exception:
                            pass
                if nomes: break
            except Exception:
                pass
        self.cmb_cliente.addItems(nomes)

    def _load_codigos_do_cliente(self):
        cliente = self.cmb_cliente.currentText().strip()
        if not cliente:
            return
        cur = self.db.conn.cursor()
        cods = []
        guesses = [
            ("produtos_cliente", ("cliente", "codigo", "descricao")),
            ("itens_cliente", ("cliente", "codigo", "descricao")),
            ("produtos", ("cliente", "codigo", "descricao")),
        ]
        try:
            for tb, cols in guesses:
                cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND LOWER(name)=?", (tb,))
                if not cur.fetchone():
                    continue
                col_cli, col_cod, col_desc = cols
                ok = True
                for c in cols:
                    try:
                        cur.execute(f"SELECT {c} FROM {tb} LIMIT 1")
                    except Exception:
                        ok = False; break
                if not ok:
                    continue
                cur.execute(
                    f"SELECT {col_cod}, {col_desc} FROM {tb} WHERE LOWER({col_cli}) = ? ORDER BY {col_cod}",
                    (cliente.lower(),)
                )
                cods = [r[0] for r in cur.fetchall()]
                if cods:
                    break
        except Exception:
            pass

        self.cmb_codigo.clear()
        self.cmb_codigo.addItems(cods)

    # ------------------------------- Tabela -------------------------------
    def _append_empty_row(self):
        r = self.table.rowCount()
        self.table.insertRow(r)
        chk = QCheckBox(); chk.setTristate(False); chk.setStyleSheet("margin-left:8px;")
        self.table.setCellWidget(r, COL_SIM, chk)
        for c in (COL_DESC, COL_MIN, COL_MAX):
            it = QTableWidgetItem("")
            it.setFlags(it.flags() | Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(r, c, it)

    def _is_last_row_filled(self) -> bool:
        r = self.table.rowCount() - 1
        if r < 0: return False
        desc = (self.table.item(r, COL_DESC).text() if self.table.item(r, COL_DESC) else "").strip()
        minv = (self.table.item(r, COL_MIN).text() if self.table.item(r, COL_MIN) else "").strip()
        maxv = (self.table.item(r, COL_MAX).text() if self.table.item(r, COL_MAX) else "").strip()
        return any([desc, minv, maxv])

    def _maybe_append_empty_row(self, _item: QTableWidgetItem):
        if self._is_last_row_filled():
            self._append_empty_row()
            self._autosize_table()
        self._update_count()

    def _autosize_table(self):
        try:
            self.table.resizeRowsToContents()
            header_h = self.table.horizontalHeader().height()
            rows_h   = sum(self.table.rowHeight(r) for r in range(self.table.rowCount()))
            frame    = self.table.frameWidth() * 2
            total_h  = header_h + rows_h + frame + 4
            self.table.setFixedHeight(max(total_h, 160))
        except Exception:
            pass

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._autosize_table()

    def _update_count(self):
        n = 0
        for r in range(self.table.rowCount()):
            desc = (self.table.item(r, COL_DESC).text() if self.table.item(r, COL_DESC) else "").strip()
            if desc: n += 1
        self.lbl_qtde.setText(f"Quantidade de Ensaios: {n}")

    # ----------------------- Load / Save ----------------------------------
    def _on_cliente_changed(self, _txt: str):
        self._load_codigos_do_cliente()
        self._load_from_db()

    def _on_codigo_changed(self, _txt: str):
        self._load_from_db()

    def _load_from_db(self):
        cliente = self.cmb_cliente.currentText().strip()
        codigo  = self.cmb_codigo.currentText().strip()
        if not cliente or not codigo:
            self._clear_table_to_blank()
            return

        cur = self.db.conn.cursor()
        try:
            cur.execute(
                """
                SELECT descricao, tipo_ensaio, sim, analise, espec_min, espec_max
                FROM analises_cliente
                WHERE cliente = ? AND codigo = ?
                ORDER BY id
                """,
                (cliente, codigo)
            )
            rows = cur.fetchall()
        except Exception:
            rows = []

        self.table.setRowCount(0)
        if rows:
            self.ed_descricao.setText(rows[0][0] or "")
            ens = (rows[0][1] or "Analitico").lower()
            self.rb_analitico.setChecked(ens.startswith("a"))
            self.rb_orientativo.setChecked(not ens.startswith("a"))

            for _, _, sim, analise, e_min, e_max in rows:
                r = self.table.rowCount()
                self.table.insertRow(r)

                chk = QCheckBox(); chk.setChecked(bool(sim)); chk.setTristate(False)
                chk.setStyleSheet("margin-left:8px;")
                self.table.setCellWidget(r, COL_SIM, chk)

                def _it(v: str):
                    it = QTableWidgetItem(v or "")
                    it.setFlags(it.flags() | Qt.ItemFlag.ItemIsEditable)
                    return it

                self.table.setItem(r, COL_DESC, _it(analise or ""))
                self.table.setItem(r, COL_MIN,  _it(e_min or ""))
                self.table.setItem(r, COL_MAX,  _it(e_max or ""))

        self._append_empty_row()
        self._autosize_table()
        self._update_count()

    def _clear_table_to_blank(self):
        self.table.setRowCount(0)
        self._append_empty_row()
        self._autosize_table()
        self._update_count()

    def _on_save_and_exit(self):
        cliente = self.cmb_cliente.currentText().strip()
        codigo  = self.cmb_codigo.currentText().strip()
        if not cliente or not codigo:
            QMessageBox.information(self, "Salvar", "Informe Cliente e Código.")
            return

        desc   = self.ed_descricao.text().strip()
        ensaio = "Analitico" if self.rb_analitico.isChecked() else "Orientativo"

        try:
            cur = self.db.conn.cursor()
            cur.execute("DELETE FROM analises_cliente WHERE cliente = ? AND codigo = ?", (cliente, codigo))

            for r in range(self.table.rowCount()):
                analise = (self.table.item(r, COL_DESC).text() if self.table.item(r, COL_DESC) else "").strip()
                minv    = (self.table.item(r, COL_MIN).text() if self.table.item(r, COL_MIN) else "").strip()
                maxv    = (self.table.item(r, COL_MAX).text() if self.table.item(r, COL_MAX) else "").strip()
                sim     = 1 if isinstance(self.table.cellWidget(r, COL_SIM), QCheckBox) and self.table.cellWidget(r, COL_SIM).isChecked() else 0
                if not any([analise, minv, maxv, sim]):
                    continue

                cur.execute(
                    """
                    INSERT INTO analises_cliente
                    (cliente, codigo, descricao, tipo_ensaio, sim, analise, espec_min, espec_max)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (cliente, codigo, desc, ensaio, sim, analise, minv, maxv)
                )
            self.db.conn.commit()
            QMessageBox.information(self, "Salvar", "Análises do cliente gravadas com sucesso.")
        except Exception as e:
            QMessageBox.warning(self, "Salvar", f"Falha ao gravar: {e}")
