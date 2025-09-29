# app/ui/screens/produto.py
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPlainTextEdit,
    QTableWidget, QTableWidgetItem, QComboBox, QDateEdit, QCheckBox,
    QSpinBox, QAbstractItemView, QPushButton, QSizePolicy, QMessageBox,
    QColorDialog, QHeaderView
)

# --- largura responsiva da coluna "Campo" (barra) ---
LABEL_COL_MIN = 200
LABEL_COL_MAX = 560
LABEL_COL_PCT = 0.40  # ajuste fino: 0.36 (mais à esquerda) / 0.46 (mais à direita)

# --- campos ---
FIELDS = [
    {"key": "produto_nome", "label": "Produto", "type": "text"},
    {"key": "codigo",       "label": "Código",  "type": "text"},
    {"key": "familia",      "label": "Família do produto", "type": "combo",
     "options": ["Micropellet", "Compound", "Masterbatch", "Outro"]},
    {"key": "cor",          "label": "Cor", "type": "color"},
    {"key": "segmento",     "label": "Segmento", "type": "combo",
     "options": ["Extrusão", "Rotomoldagem", "Injeção", "Sopro", "Outro"]},
    {"key": "reavaliar",    "label": "Reavaliar padrão a cada (dias)", "type": "spin_days"},
    {"key": "direto_ext",   "label": "Direto na Extrusão?", "type": "checkbox"},
    {"key": "local_padrao", "label": "Localização Padrão", "type": "text"},
    {"key": "fabricado_em", "label": "Fabricado em", "type": "date"},
    {"key": "lote_padrao",  "label": "Lote Padrão", "type": "text"},
    {"key": "valido_ate",   "label": "Válido Até", "type": "date_valid"},
    {"key": "rev_ndata",    "label": "Revisão Nº - Data:", "type": "rev_pack"},
    {"key": "desc_pt",      "label": "Descrição Geral - Português", "type": "multiline"},
    {"key": "desc_en",      "label": "Descrição Geral - Inglês",     "type": "multiline"},
    {"key": "desc_es",      "label": "Descrição Geral - Espanhol",   "type": "multiline"},
    {"key": "aplic_pt",     "label": "Aplicações - Português", "type": "multiline"},
    {"key": "aplic_en",     "label": "Aplicações - Inglês",    "type": "multiline"},
    {"key": "aplic_es",     "label": "Aplicações - Espanhol",  "type": "multiline"},
    {"key": "historico",    "label": "Histórico das Revisões", "type": "history"},
]


class ProdutoWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = getattr(parent, "db", None)

        self._editors = {}
        self._current_record = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 12, 16, 16)
        root.setSpacing(10)

        # Ações e busca
        actions = QHBoxLayout()
        self.btn_novo = QPushButton("Novo");   self.btn_novo.setProperty("kind", "primary")
        self.btn_save = QPushButton("Salvar"); self.btn_save.setProperty("kind", "primary")
        self.btn_del  = QPushButton("Excluir"); self.btn_del.setProperty("kind", "danger")
        for b in (self.btn_novo, self.btn_save, self.btn_del):
            b.setMinimumHeight(32)
            actions.addWidget(b)
        actions.addStretch(1)

        lbl_busca = QLabel("Buscar"); lbl_busca.setProperty("class", "Field")
        self.ed_busca = QLineEdit(); self.ed_busca.setPlaceholderText("Digite nome ou código")
        self.ed_busca.setMinimumWidth(360)
        self.btn_buscar = QPushButton("Localizar"); self.btn_buscar.setProperty("kind", "outline")
        actions.addWidget(lbl_busca); actions.addWidget(self.ed_busca, 1); actions.addWidget(self.btn_buscar)
        root.addLayout(actions)

        # Tabela formulário
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Campo", "Valor"])
        self.table.setRowCount(len(FIELDS))
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header.setMinimumSectionSize(100)  # deixa arrastar mais para a esquerda
        root.addWidget(self.table)

        # Linhas
        for r, spec in enumerate(FIELDS):
            self._add_row(r, spec)

        # Ajustes visuais iniciais
        self._fit_label_column()
        self._ensure_date_widgets()

        # Sinais
        self.btn_novo.clicked.connect(self._on_new)
        self.btn_save.clicked.connect(self._on_save)
        self.btn_del.clicked.connect(self._on_delete)
        self.btn_buscar.clicked.connect(self._on_search)
        self.ed_busca.returnPressed.connect(self._on_search)

        self._seed_example()

    # ---------- construção ----------
    def _add_row(self, row, spec):
        label = QTableWidgetItem(spec["label"])
        label.setFlags(Qt.ItemFlag.ItemIsEnabled)
        self.table.setItem(row, 0, label)

        editor = self._build_editor(spec)
        self._editors[spec["key"]] = editor
        self.table.setCellWidget(row, 1, editor)

        tall = spec["type"] in {"multiline"}
        self.table.setRowHeight(row, 110 if tall else 40)

    def _build_editor(self, spec):
        t = spec["type"]

        if t == "text":
            w = QLineEdit(); w.setPlaceholderText("Digite aqui")
            return w

        if t == "combo":
            w = QComboBox(); w.addItems(spec.get("options", []))
            return w

        if t == "color":
            container = QWidget()
            hb = QHBoxLayout(container); hb.setContentsMargins(0, 0, 0, 0); hb.setSpacing(6)
            ed = QLineEdit(); ed.setPlaceholderText("Digite a cor")
            swatch = QLabel(); swatch.setFixedSize(22, 22); swatch.setStyleSheet("border-radius:4px; border:1px solid rgba(0,0,0,0.15);")
            btn = QPushButton("Escolher"); btn.setProperty("kind", "outline"); btn.setFixedHeight(28)
            def pick():
                c = QColorDialog.getColor(QColor("#1f7ae0"), self, "Escolher cor")
                if c.isValid():
                    ed.setText(c.name())
                    swatch.setStyleSheet(f"border-radius:4px; border:1px solid rgba(0,0,0,0.15); background:{c.name()};")
            btn.clicked.connect(pick)
            hb.addWidget(ed, 1); hb.addWidget(swatch); hb.addWidget(btn, 0)
            container._line = ed; container._swatch = swatch
            return container

        if t == "spin_days":
            sp = QSpinBox(); sp.setRange(0, 10000); sp.setSuffix(" dias"); sp.setValue(0)
            return sp

        if t == "checkbox":
            c = QWidget()
            hb = QHBoxLayout(c); hb.setContentsMargins(0, 0, 0, 0); hb.setSpacing(8)
            chk = QCheckBox(); lbl = QLabel("Sim"); lbl.setEnabled(False)
            hb.addWidget(chk); hb.addWidget(lbl); hb.addStretch(1)
            c._chk = chk
            return c

        if t in {"date", "date_valid"}:
            d = QDateEdit()
            d.setCalendarPopup(True)
            d.setDisplayFormat("dd/MM/yyyy")
            d.setDate(QDate.currentDate())
            d.setMinimumWidth(130)
            d.setMaximumWidth(150)
            if t == "date_valid":
                d.dateChanged.connect(lambda _=None, ref=d: self._refresh_valid_style(ref))
                self._refresh_valid_style(d)
            return d

        if t == "rev_pack":
            c = QWidget()
            hb = QHBoxLayout(c); hb.setContentsMargins(0, 0, 0, 0); hb.setSpacing(8)
            sp = QSpinBox(); sp.setRange(0, 9999); sp.setFixedWidth(80)
            dt = QDateEdit(); dt.setCalendarPopup(True)
            dt.setDisplayFormat("dd/MM/yyyy"); dt.setDate(QDate.currentDate())
            dt.setMinimumWidth(130); dt.setMaximumWidth(150)
            hb.addWidget(sp); hb.addWidget(dt); hb.addStretch(1)
            c._spin = sp; c._date = dt
            return c

        if t == "multiline":
            p = QPlainTextEdit(); p.setPlaceholderText("Digite aqui"); p.setMinimumHeight(90)
            return p

        if t == "history":
            e = QLineEdit(); e.setReadOnly(True)
            return e

        return QLineEdit()

    # ---------- layout da coluna de rótulos ----------
    def _fit_label_column(self):
        try:
            view_w = self.table.viewport().width()
        except Exception:
            view_w = self.table.width()
        desired = int(view_w * LABEL_COL_PCT)
        desired = max(LABEL_COL_MIN, min(desired, LABEL_COL_MAX))
        self.table.setColumnWidth(0, desired)
        self.table.horizontalHeader().setStretchLastSection(True)

    def _ensure_date_widgets(self):
        for de in self.table.findChildren(QDateEdit):
            de.setDisplayFormat("dd/MM/yyyy")
            de.setMinimumWidth(130)
            de.setMaximumWidth(150)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._fit_label_column()
        self._ensure_date_widgets()

    def _refresh_valid_style(self, d: QDateEdit):
        expired = d.date() < QDate.currentDate()
        d.setStyleSheet("QDateEdit { background: #ffe9e9; }" if expired else "")

    # ---------- valores ----------
    def _get_values(self) -> dict:
        out = {}
        for spec in FIELDS:
            key = spec["key"]
            ed = self._editors[key]
            t = spec["type"]
            if t == "text":
                out[key] = ed.text().strip()
            elif t == "combo":
                out[key] = ed.currentText()
            elif t == "color":
                out[key] = ed._line.text().strip()
            elif t == "spin_days":
                out[key] = str(ed.value())
            elif t == "checkbox":
                out[key] = "Sim" if ed._chk.isChecked() else "Não"
            elif t in {"date", "date_valid"}:
                out[key] = ed.date().toString("dd/MM/yyyy")
            elif t == "rev_pack":
                out["rev_num"] = str(ed._spin.value())
                out["rev_data"] = ed._date.date().toString("dd/MM/yyyy")
            elif t == "multiline":
                out[key] = ed.toPlainText().strip()
            elif t == "history":
                out[key] = ed.text()
        return out

    def _set_values(self, data: dict):
        for spec in FIELDS:
            key = spec["key"]
            ed = self._editors[key]
            t = spec["type"]
            val = data.get(key, "")
            if t == "text":
                ed.setText(val)
            elif t == "combo":
                idx = ed.findText(val); ed.setCurrentIndex(idx if idx >= 0 else 0)
            elif t == "color":
                ed._line.setText(val)
                if val:
                    ed._swatch.setStyleSheet(f"border-radius:4px; border:1px solid rgba(0,0,0,0.15); background:{val};")
            elif t == "spin_days":
                try: ed.setValue(int(val))
                except Exception: pass
            elif t == "checkbox":
                ed._chk.setChecked(str(val).strip().lower() in {"sim", "true", "1"})
            elif t in {"date", "date_valid"}:
                try:
                    d, m, y = str(val).split("/")
                    ed.setDate(QDate(int(y), int(m), int(d)))
                except Exception:
                    ed.setDate(QDate.currentDate())
                if t == "date_valid":
                    self._refresh_valid_style(ed)
            elif t == "rev_pack":
                try: ed._spin.setValue(int(data.get("rev_num", "0")))
                except Exception: pass
                try:
                    d, m, y = str(data.get("rev_data", "")).split("/")
                    ed._date.setDate(QDate(int(y), int(m), int(d)))
                except Exception:
                    ed._date.setDate(QDate.currentDate())
            elif t == "multiline":
                ed.setPlainText(val)
            elif t == "history":
                ed.setText(val)

        self._ensure_date_widgets()

    # ---------- ações ----------
    def _on_new(self):
        for spec in FIELDS:
            key = spec["key"]; ed = self._editors[key]; t = spec["type"]
            if t in {"text", "history"}:
                ed.clear()
            elif t == "combo":
                ed.setCurrentIndex(0)
            elif t == "color":
                ed._line.clear(); ed._swatch.setStyleSheet("border-radius:4px; border:1px solid rgba(0,0,0,0.15);")
            elif t == "spin_days":
                ed.setValue(0)
            elif t == "checkbox":
                ed._chk.setChecked(False)
            elif t in {"date", "date_valid"}:
                ed.setDate(QDate.currentDate())
                if t == "date_valid": self._refresh_valid_style(ed)
            elif t == "rev_pack":
                ed._spin.setValue(0); ed._date.setDate(QDate.currentDate())
            elif t == "multiline":
                ed.clear()
        self._editors["produto_nome"].setFocus()
        self._ensure_date_widgets()

    def _on_save(self):
        self._current_record = self._get_values()
        QMessageBox.information(self, "Produto", "Registro preparado para salvar.")

    def _on_delete(self):
        self._current_record = {}
        self._on_new()

    # ---------- busca ----------
    def _on_search(self):
        termo = self.ed_busca.text().strip()
        if not termo:
            return
        if self.db:
            tabela = self._detect_products_table()
            if tabela:
                try:
                    cols = self._table_columns(tabela)
                    cand_nome = [c for c in cols if c.lower() in {"nome", "produto", "descricao", "produto_nome"}]
                    cand_codigo = [c for c in cols if c.lower() in {"codigo", "cod", "codigo_produto"}]
                    where = []; params = []
                    if cand_nome:
                        where.append(" OR ".join([f"LOWER({c}) LIKE ?" for c in cand_nome]))
                        params.extend([f"%{termo.lower()}%"] * len(cand_nome))
                    if cand_codigo:
                        where.append(" OR ".join([f"LOWER({c}) = ?" for c in cand_codigo]))
                        params.extend([termo.lower()] * len(cand_codigo))
                    if where:
                        sql = f"SELECT * FROM {tabela} WHERE {' OR '.join(where)} LIMIT 1"
                        cur = self.db.conn.cursor(); cur.execute(sql, params)
                        row = cur.fetchone()
                        if row:
                            rec = {cols[i]: row[i] for i in range(len(cols))}
                            values = self._map_db_to_form(rec)
                            self._set_values(values)
                            return
                except Exception:
                    pass

        # fallback local (nome contém o termo OU termo == código)
        if self._current_record:
            t = termo.lower()
            nome = self._current_record.get("produto_nome", "").lower()
            codigo = self._current_record.get("codigo", "").lower()
            if t in nome or t == codigo:
                self._set_values(self._current_record)
                return

        QMessageBox.information(self, "Busca", "Nada encontrado.")

    # ---------- util banco ----------
    def _detect_products_table(self) -> str | None:
        try:
            cur = self.db.conn.cursor()
            for cand in ["produtos", "produto", "tb_produtos", "tb_produto", "products"]:
                cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND LOWER(name)=?", (cand,))
                r = cur.fetchone()
                if r:
                    return r[0]
        except Exception:
            return None
        return None

    def _table_columns(self, table: str) -> list[str]:
        cur = self.db.conn.cursor()
        cur.execute(f"PRAGMA table_info({table})")
        return [r[1] for r in cur.fetchall()]

    def _map_db_to_form(self, rec: dict) -> dict:
        def g(*names):
            for n in names:
                for k in rec.keys():
                    if k.lower() == n.lower():
                        v = rec[k]
                        return "" if v is None else str(v)
            return ""
        lookup = {
            "produto_nome": g("nome", "produto", "descricao", "produto_nome"),
            "codigo":       g("codigo", "cod", "codigo_produto"),
            "familia":      g("familia", "familia_produto"),
            "cor":          g("cor"),
            "segmento":     g("segmento", "linha", "processo"),
            "reavaliar":    g("reavaliar_dias", "revisao_periodo_dias"),
            "direto_ext":   g("direto_extrusao", "direto_na_extrusao"),
            "local_padrao": g("localizacao", "local_padrao"),
            "fabricado_em": g("fabricado_em", "data_fabricacao"),
            "lote_padrao":  g("lote_padrao", "lote"),
            "valido_ate":   g("valido_ate"),
            "rev_num":      g("revisao_numero", "revisao"),
            "rev_data":     g("revisao_data"),
            "desc_pt":      g("descricao_pt", "desc_pt"),
            "desc_en":      g("descricao_en", "desc_en"),
            "desc_es":      g("descricao_es", "desc_es"),
            "aplic_pt":     g("aplicacoes_pt", "aplic_pt"),
            "aplic_en":     g("aplicacoes_en", "aplic_en"),
            "aplic_es":     g("aplicacoes_es", "aplic_es"),
            "historico":    g("historico_revisoes", "historico"),
        }
        if lookup["rev_num"] or lookup["rev_data"]:
            lookup["rev_ndata"] = ""
        return lookup

    # ---------- exemplo ----------
    def _seed_example(self):
        demo = {
            "produto_nome": "COMPOSTO POLIETILENO ML 4439 AZ 100 MC",
            "codigo": "4000000396",
            "familia": "Micropellet",
            "cor": "#000000",
            "segmento": "Extrusão",
            "reavaliar": "730",
            "direto_ext": "Sim",
            "local_padrao": "A01 P02",
            "fabricado_em": QDate.currentDate().toString("dd/MM/yyyy"),
            "lote_padrao": "14J008",
            "valido_ate": QDate.currentDate().addDays(-5).toString("dd/MM/yyyy"),
            "rev_num": "0",
            "rev_data": QDate.currentDate().toString("dd/MM/yyyy"),
            "desc_pt": "Produto Micropellet produzido com resina de polietileno base buteno.",
            "desc_en": "Micropellet product produced with polyethylene resin based on butene.",
            "desc_es": "Producto Micropellet producido con resina de polietileno.",
            "aplic_pt": "Reservatórios de água e outros usos gerais.",
            "aplic_en": "Water tanks and general purpose.",
            "aplic_es": "Depósitos de agua y usos generales.",
            "historico": "Revisão: 00 - Emissão Inicial",
        }
        self._set_values(demo)
        self._current_record = demo
