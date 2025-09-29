# app/ui/screens/analise_produto.py
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QPushButton, QTableWidget, QTableWidgetItem, QAbstractItemView,
    QSpinBox, QCheckBox, QMessageBox
)

BASIC_ROWS = [
    ("Possui Rabichos?",                  "Visual",           "",                               "",   "Não",  False),
    ("Umidade (%)",                       "",                 "UCPT INT LAB 011",               "1",  "",     True),
    ("Transmítica - 1,5mm (%)",           "",                 "UCPT INT LAB 012",               "0,02","",    True),
    ("Codificação da etiqueta produto",   "Visual",           "",                               "OK", "",     False),
    ("Resina",                            "",                 "",                               "PELBD","",   False),
    ("Densidade Aparente Composto (g/l)", "",                 "UCPT INT LAB 008 / ASTM D1895",  "45", "55",   True),
    ("IF Composto 2,16kg (g/10min)",      "",                 "UCPT INT LAB 007 / ASTM D1238",  "3,4","4,6",  True),
    ("Fluidez a Seco (seg)",              "",                 "UCPT INT LAB 008/ ASTM D 1895",  "10", "20",   True),
    ("Contaminação",                      "Visual",           "",                               "Isento","",  False),
    ("Placa fundida (aparência)",         "",                 "UCPT INT LAB 002",               "OK", "",     False),
]

class AnaliseProdutoWidget(QWidget):
    ROLE_IS_BASIC = Qt.ItemDataRole.UserRole + 1

    def __init__(self, db):
        super().__init__()
        self.db = db
        self._ensure_tables()

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        # -------- Localizar (QComboBox com "setinha")
        row_loc = QHBoxLayout()
        lbl_loc = QLabel("Localizar"); lbl_loc.setProperty("class", "Field")
        self.cmb_localizar = QComboBox()
        self.cmb_localizar.setEditable(True)
        self.cmb_localizar.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.cmb_localizar.setMinimumWidth(420)
        self.cmb_localizar.lineEdit().setPlaceholderText("Descrição ou código")

        lbl_id = QLabel("ID")
        self.spin_id = QSpinBox()
        self.spin_id.setRange(0, 999999)
        self.spin_id.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.spin_id.setFixedWidth(80)
        self.spin_id.setReadOnly(True)

        self.btn_localizar = QPushButton("Localizar"); self.btn_localizar.setProperty("kind", "outline")
        self.btn_localizar.setFixedHeight(30)

        row_loc.addWidget(lbl_loc)
        row_loc.addWidget(self.cmb_localizar, 1)
        row_loc.addSpacing(8)
        row_loc.addWidget(lbl_id)
        row_loc.addWidget(self.spin_id)
        row_loc.addSpacing(8)
        row_loc.addWidget(self.btn_localizar)
        root.addLayout(row_loc)

        # -------- Descrição / Família / Ações
        row_desc = QHBoxLayout()
        lbl_desc = QLabel("Descrição"); lbl_desc.setProperty("class", "Field")
        self.ed_descricao = QLineEdit(); self.ed_descricao.setPlaceholderText("Descrição do produto")
        self.ed_descricao.setMinimumWidth(500)

        lbl_fam = QLabel("Família")
        self.cmb_familia = QComboBox()
        self.cmb_familia.addItems(["Micropellet", "Masterbatch", "Compound", "Outro"])
        self.cmb_familia.setFixedWidth(160)

        self.btn_inserir_basicas = QPushButton("Inserir Análises Básicas"); self.btn_inserir_basicas.setProperty("kind", "primary")
        self.btn_inserir_basicas.setFixedHeight(30)

        # NOVO: inserir apenas uma linha
        self.btn_inserir_linha = QPushButton("Inserir Linha"); self.btn_inserir_linha.setProperty("kind", "outline")
        self.btn_inserir_linha.setFixedHeight(30)

        self.btn_remover_basicas = QPushButton("Remover Análises Básicas"); self.btn_remover_basicas.setProperty("kind", "danger")
        self.btn_remover_basicas.setFixedHeight(30)

        row_desc.addWidget(lbl_desc)
        row_desc.addWidget(self.ed_descricao, 1)
        row_desc.addSpacing(6)
        row_desc.addWidget(lbl_fam)
        row_desc.addWidget(self.cmb_familia)
        row_desc.addSpacing(10)
        row_desc.addWidget(self.btn_inserir_basicas)
        row_desc.addWidget(self.btn_inserir_linha)        # <- novo botão
        row_desc.addWidget(self.btn_remover_basicas)
        root.addLayout(row_desc)

        # -------- Tabela
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Análises Básicas", "Tipo", "Método", "Mínimo", "Máximo", "Especificação"])
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setAlternatingRowColors(True)
        root.addWidget(self.table, 1)

        # -------- Rodapé
        foot = QHBoxLayout()
        foot.addStretch(1)
        self.btn_gravar = QPushButton("Gravar"); self.btn_gravar.setProperty("kind", "primary")
        self.btn_gravar.setFixedSize(QSize(92, 36))
        foot.addWidget(self.btn_gravar)
        root.addLayout(foot)

        # Sinais
        self.btn_localizar.clicked.connect(self._on_localizar)
        self.btn_inserir_basicas.clicked.connect(self._on_inserir_basicas)
        self.btn_inserir_linha.clicked.connect(self._on_inserir_linha)       # <- novo handler
        self.btn_remover_basicas.clicked.connect(self._on_remover_basicas)
        self.btn_gravar.clicked.connect(self._on_save)

        # Sugestões para o combo
        self._load_suggestions()

    # ===================== Banco / Persistência =====================
    def _ensure_tables(self):
        cur = self.db.conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS produtos_ap (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descricao TEXT,
                familia  TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS analises_produto_ap (
                produto_id INTEGER,
                propriedade TEXT,
                tipo        TEXT,
                metodo      TEXT,
                minimo      TEXT,
                maximo      TEXT,
                especificacao INTEGER DEFAULT 0
            )
        """)
        self.db.conn.commit()

    def _save_product(self, pid: int, descricao: str, familia: str) -> int:
        cur = self.db.conn.cursor()
        if pid > 0:
            cur.execute("UPDATE produtos_ap SET descricao=?, familia=? WHERE id=?", (descricao, familia, pid))
            self.db.conn.commit()
            return pid
        cur.execute("INSERT INTO produtos_ap (descricao, familia) VALUES (?,?)", (descricao, familia))
        self.db.conn.commit()
        return cur.lastrowid

    def _overwrite_analises(self, pid: int):
        cur = self.db.conn.cursor()
        cur.execute("DELETE FROM analises_produto_ap WHERE produto_id=?", (pid,))
        for r in range(self.table.rowCount()):
            prop   = self._text(r, 0)
            tipo   = self._text(r, 1)
            metodo = self._text(r, 2)
            minimo = self._text(r, 3)
            maximo = self._text(r, 4)
            espec  = 1 if self._checked(r, 5) else 0
            cur.execute("""
                INSERT INTO analises_produto_ap
                    (produto_id, propriedade, tipo, metodo, minimo, maximo, especificacao)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (pid, prop, tipo, metodo, minimo, maximo, espec))
        self.db.conn.commit()

    def _load_analises(self, pid: int):
        self._clear_table()
        cur = self.db.conn.cursor()
        cur.execute("""
            SELECT propriedade, tipo, metodo, minimo, maximo, especificacao
              FROM analises_produto_ap
             WHERE produto_id=?
        """, (pid,))
        for prop, tipo, metodo, minimo, maximo, espec in cur.fetchall():
            self._add_row(prop or "", tipo or "", metodo or "", minimo or "", maximo or "", bool(espec), is_basic=False)

    # ===================== UI Helpers =====================
    def _add_row(self, prop: str, tipo: str, metodo: str, minimo: str, maximo: str, espec: bool, is_basic: bool = False):
        r = self.table.rowCount()
        self.table.insertRow(r)
        def mk(txt, basic=False):
            it = QTableWidgetItem(txt)
            it.setFlags(it.flags() | Qt.ItemFlag.ItemIsEditable)
            if basic: it.setData(self.ROLE_IS_BASIC, True)
            return it
        self.table.setItem(r, 0, mk(prop, is_basic))
        self.table.setItem(r, 1, mk(tipo))
        self.table.setItem(r, 2, mk(metodo))
        self.table.setItem(r, 3, mk(minimo))
        self.table.setItem(r, 4, mk(maximo))
        chk = QCheckBox(); chk.setChecked(bool(espec)); chk.setTristate(False)
        chk.setStyleSheet("margin-left:auto; margin-right:auto;")
        self.table.setCellWidget(r, 5, chk)

    def _clear_table(self):
        self.table.setRowCount(0)

    def _text(self, row: int, col: int) -> str:
        it = self.table.item(row, col)
        return it.text().strip() if it else ""

    def _checked(self, row: int, col: int) -> bool:
        w = self.table.cellWidget(row, col)
        return bool(w.isChecked()) if isinstance(w, QCheckBox) else False

    # ===================== Ações =====================
    def _load_suggestions(self):
        itens = []
        try:
            cur = self.db.conn.cursor()
            for cand in ("produtos", "produto", "tb_produtos", "tb_produto", "products", "produtos_ap"):
                cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND LOWER(name)=?", (cand,))
                if cur.fetchone():
                    table = cand
                    break
            else:
                table = None

            if table:
                cur.execute(f"PRAGMA table_info({table})")
                cols = [c[1].lower() for c in cur.fetchall()]
                col_desc = next((c for c in cols if c in ("descricao", "nome", "produto", "descricao_pt")), None)
                col_cod  = next((c for c in cols if "cod" in c), None)
                col_id   = next((c for c in cols if c in ("id","produto_id","codigo_id")), None)
                if col_desc:
                    sel = [col_desc]
                    if col_cod: sel.append(col_cod)
                    if col_id:  sel.append(col_id)
                    cur.execute(f"SELECT {', '.join(sel)} FROM {table} ORDER BY {col_desc} LIMIT 400")
                    for row in cur.fetchall():
                        desc = str(row[0] or "")
                        cod  = str(row[1]) if (col_cod and len(row) > 1) else ""
                        pid  = int(row[-1]) if (col_id and len(row) > 1) else 0
                        label = f"{desc} ({cod})" if cod else desc
                        itens.append((label, pid, desc))
        except Exception:
            pass
        if not itens:
            itens = [("COMPOSTO POLIETILENO ML 4439 AZ 100 MC (4000000396)", 1886, "COMPOSTO POLIETILENO ML 4439 AZ 100 MC")]
        self.cmb_localizar.clear()
        for label, pid, desc in itens:
            self.cmb_localizar.addItem(label, (pid, desc))

    def _on_localizar(self):
        data = self.cmb_localizar.currentData()
        termo = self.cmb_localizar.currentText().strip()
        if data:
            pid, desc = data
            if pid: self.spin_id.setValue(pid)
            if desc: self.ed_descricao.setText(desc)
            if pid:
                self._load_analises(pid)
        else:
            self.ed_descricao.setText(termo)

    def _on_inserir_basicas(self):
        for row in BASIC_ROWS:
            self._add_row(*row, is_basic=True)
        self.table.scrollToBottom()

    def _on_inserir_linha(self):
        """Insere uma única linha em branco para edição."""
        self._add_row("", "", "", "", "", False, is_basic=False)
        r = self.table.rowCount() - 1
        self.table.scrollToItem(self.table.item(r, 0))
        self.table.setCurrentCell(r, 0)
        self.table.editItem(self.table.item(r, 0))

    def _on_remover_basicas(self):
        removed = 0
        for r in range(self.table.rowCount()-1, -1, -1):
            it = self.table.item(r, 0)
            if it and it.data(self.ROLE_IS_BASIC):
                self.table.removeRow(r); removed += 1
        if removed == 0:
            for r in sorted({ix.row() for ix in self.table.selectedIndexes()}, reverse=True):
                self.table.removeRow(r)

    def _on_save(self):
        desc = self.ed_descricao.text().strip()
        if not desc:
            QMessageBox.information(self, "Salvar", "Informe a descrição do produto.")
            return
        familia = self.cmb_familia.currentText().strip()
        pid_in  = self.spin_id.value()

        pid = self._save_product(pid_in, desc, familia)
        self.spin_id.setValue(pid)
        self._overwrite_analises(pid)

        QMessageBox.information(self, "Salvar", f"Análises do produto #{pid} salvas com sucesso!")
