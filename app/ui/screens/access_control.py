from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QFrame, QLabel, QComboBox,
    QCheckBox, QPushButton, QGridLayout, QMessageBox, QLineEdit
)


class AccessControlWidget(QWidget):
    """
    Tela de Acessos: escolhe o funcionário e marca/desmarca permissões.
    Salva no table 'acessos' (uma linha por usuário). Se não existir, insere.
    Se existir, atualiza.
    """
    # (nome_coluna, rótulo)
    PERMS = [
        ("cad_funcionarios",        "Cadastrar Funcionários"),
        ("definir_acessos",         "Definir Acessos"),
        ("cad_clientes",            "Cadastrar Clientes"),
        ("cad_registros",           "Cadastrar Registros"),
        ("cad_analises",            "Cadastrar Análises"),
        ("cad_produtos",            "Cadastrar Produtos"),
        ("cad_fabrica",             "Cadastrar Fábrica"),
        ("atualizar_dados",         "Atualizar Dados"),

        ("analise_por_produto",     "Cadastrar Análise por Produto"),
        ("analise_por_cliente",     "Cadastrar Análise por Cliente"),
        ("imprimir_rotulos",        "Imprimir Rótulos"),
        ("inserir_resultados",      "Inserir Resultados das Análises"),
        ("emitir_certificados",     "Emitir Certificados"),
        ("imprimir_certificados",   "Imprimir Certificados"),
        ("consultas_gerais",        "Consultas/Relatórios"),
        ("liberacao_especial",      "Liberação Especial"),
    ]

    def __init__(self, db):
        super().__init__()
        self.db = db
        self.user_id = None
        self._build_ui()
        self._load_funcionarios()

    # -----------------------------
    # UI
    # -----------------------------
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 8, 12, 8)
        root.setSpacing(8)

        # Barra de título
        bar = QFrame(objectName="PageBar")
        bar_lay = QHBoxLayout(bar)
        bar_lay.setContentsMargins(12, 8, 12, 8)
        title = QLabel("Acessos", objectName="PageTitle")
        bar_lay.addWidget(title)
        bar_lay.addStretch(1)

        self.btn_voltar = QPushButton("Voltar à Principal")
        self.btn_voltar.setProperty("kind", "outline")
        bar_lay.addWidget(self.btn_voltar)
        root.addWidget(bar)

        # Card principal
        card = QFrame()
        card.setObjectName("Card")
        card_l = QVBoxLayout(card)
        card_l.setSpacing(10)

        # Linha superior: funcionário + ações
        top = QHBoxLayout()
        top.addWidget(QLabel("Funcionário"))

        self.cmb_func = QComboBox()
        self.cmb_func.setMinimumWidth(280)
        self.cmb_func.currentIndexChanged.connect(self._on_user_changed)
        top.addWidget(self.cmb_func)

        top.addStretch(1)

        self.btn_carregar = QPushButton("Carregar")
        self.btn_carregar.clicked.connect(self._load_permissions_clicked)
        self.btn_salvar = QPushButton("Salvar")
        self.btn_salvar.clicked.connect(self._save)
        self.btn_limpar = QPushButton("Limpar Marcações")
        self.btn_limpar.setProperty("kind", "danger")
        self.btn_limpar.clicked.connect(self._clear_checks)

        for b in (self.btn_carregar, self.btn_salvar, self.btn_limpar):
            top.addWidget(b)

        card_l.addLayout(top)

        # Campo busca local nas permissões (filtra rótulos)
        busca_lay = QHBoxLayout()
        busca_lay.addWidget(QLabel("Buscar"))
        self.ed_busca = QLineEdit()
        self.ed_busca.setPlaceholderText("Digite para filtrar")
        self.ed_busca.textChanged.connect(self._apply_filter)
        busca_lay.addWidget(self.ed_busca, 1)
        card_l.addLayout(busca_lay)

        # Grade das permissões (2 colunas)
        grid = QGridLayout()
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        self._check_widgets = []  # [(col, checkbox, wrapper_frame)]

        left_col = QVBoxLayout()
        right_col = QVBoxLayout()

        half = (len(self.PERMS) + 1) // 2
        left_items = self.PERMS[:half]
        right_items = self.PERMS[half:]

        def make_col(items, layout):
            for col_name, label in items:
                frm = QFrame()
                h = QHBoxLayout(frm)
                h.setContentsMargins(6, 2, 6, 2)
                cb = QCheckBox(label)
                cb.setProperty("class", "Field")
                cb._col_name = col_name
                h.addWidget(cb)
                layout.addWidget(frm)
                self._check_widgets.append((col_name, cb, frm))

            layout.addStretch(1)

        make_col(left_items, left_col)
        make_col(right_items, right_col)

        grid.addLayout(left_col, 0, 0)
        grid.addLayout(right_col, 0, 1)
        card_l.addLayout(grid)

        root.addWidget(card, 1)

    # -----------------------------
    # LOADS
    # -----------------------------
    def _load_funcionarios(self):
        self.cmb_func.blockSignals(True)
        self.cmb_func.clear()
        cur = self.db.conn.cursor()
        try:
            cur.execute("SELECT id, nome FROM funcionarios ORDER BY nome")
            rows = cur.fetchall()
        except Exception:
            rows = []
        for i, (uid, nome) in enumerate(rows):
            self.cmb_func.addItem(nome, uid)
        self.cmb_func.blockSignals(False)
        if rows:
            self.user_id = rows[0][0]
            self._load_permissions()

    def _on_user_changed(self, _i):
        self.user_id = self.cmb_func.currentData()
        self._load_permissions()

    def _existing_columns(self, table):
        try:
            cur = self.db.conn.cursor()
            cur.execute(f"PRAGMA table_info({table})")
            return {r[1] for r in cur.fetchall()}
        except Exception:
            return set()

    def _load_permissions_clicked(self):
        if self.user_id is None:
            QMessageBox.information(self, "Acessos", "Escolha um funcionário.")
            return
        self._load_permissions()

    def _clear_checks(self):
        for _, cb, _frm in self._check_widgets:
            cb.setChecked(False)

    def _apply_filter(self, text: str):
        text = (text or "").strip().lower()
        for col, cb, frm in self._check_widgets:
            show = text in cb.text().lower()
            frm.setVisible(True if not text else show)

    def _load_permissions(self):
        self._clear_checks()
        if self.user_id is None:
            return
        cur = self.db.conn.cursor()
        try:
            cur.execute("SELECT * FROM acessos WHERE usuario_id = ?", (self.user_id,))
            row = cur.fetchone()
        except Exception:
            row = None

        if not row:
            return

        # nome->índice
        colnames = [d[0] for d in cur.description]
        data = dict(zip(colnames, row))

        for col, cb, _frm in self._check_widgets:
            v = int(data.get(col, 0) or 0)
            cb.setChecked(v == 1)

    # -----------------------------
    # SAVE
    # -----------------------------
    def _save(self):
        if self.user_id is None:
            QMessageBox.information(self, "Acessos", "Escolha um funcionário.")
            return

        values = {col: 1 if cb.isChecked() else 0 for col, cb, _frm in self._check_widgets}
        cols_exist = self._existing_columns("acessos")

        # Filtra só colunas que realmente existem
        payload = {k: v for k, v in values.items() if k in cols_exist}
        payload["usuario_id"] = self.user_id

        cur = self.db.conn.cursor()
        cur.execute("SELECT 1 FROM acessos WHERE usuario_id = ?", (self.user_id,))
        exists = cur.fetchone() is not None

        if exists:
            # UPDATE
            sets = ", ".join([f"{k}=?" for k in payload.keys() if k != "usuario_id"])
            args = [payload[k] for k in payload.keys() if k != "usuario_id"]
            args.append(payload["usuario_id"])
            sql = f"UPDATE acessos SET {sets} WHERE usuario_id = ?"
            cur.execute(sql, args)
        else:
            # INSERT
            cols = ", ".join(payload.keys())
            qs = ", ".join(["?"] * len(payload))
            sql = f"INSERT INTO acessos ({cols}) VALUES ({qs})"
            cur.execute(sql, list(payload.values()))

        self.db.conn.commit()
        QMessageBox.information(self, "Acessos", "Permissões salvas.")
