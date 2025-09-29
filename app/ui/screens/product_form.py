from PyQt6.QtCore import Qt, QDate
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFrame, QLabel, QLineEdit,
    QComboBox, QPushButton, QSpinBox, QTextEdit, QDateEdit, QTabWidget,
    QSizePolicy
)
from PyQt6.QtGui import QColor, QPalette


def _h28(widget):
    """Ajusta altura padrão dos inputs para harmonia visual."""
    widget.setMinimumHeight(28)
    widget.setMaximumHeight(28)
    return widget


def _lbl(texto: str) -> QLabel:
    l = QLabel(texto)
    l.setObjectName("FormLabel")
    l.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    return l


class ProductsFormWidget(QFrame):
    """
    Formulário de Produtos organizado em 3 colunas.
    Guia "Dados do Produto" com campos principais.
    Guia "Ficha de Segurança" para observações ou link.
    Busca com Localizar, navegação e CRUD simples.
    """
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setObjectName("Card")

        self.ids: list[int] = []
        self.index: int = -1
        self._building = False

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        # Toolbar
        toolbar = QFrame(objectName="Toolbar")
        tb = QHBoxLayout(toolbar)
        tb.setContentsMargins(0, 0, 0, 0)
        tb.setSpacing(8)

        self.btn_new   = QPushButton("Novo");   self.btn_new.setProperty("kind", "outline")
        self.btn_save  = QPushButton("Salvar"); self.btn_save.setProperty("kind", "primary")
        self.btn_del   = QPushButton("Excluir");self.btn_del.setProperty("kind", "danger")

        self.lbl_buscar = QLabel("Buscar")
        self.ed_busca   = _h28(QLineEdit())
        self.ed_busca.setPlaceholderText("Código, nome ou segmento")
        self.btn_find   = QPushButton("Localizar"); self.btn_find.setProperty("kind", "outline")

        tb.addWidget(self.btn_new)
        tb.addWidget(self.btn_save)
        tb.addWidget(self.btn_del)
        tb.addStretch(1)
        tb.addWidget(self.lbl_buscar)
        tb.addWidget(self.ed_busca)
        tb.addWidget(self.btn_find)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.page_dados = QWidget()
        self.page_msds  = QWidget()
        self.tabs.addTab(self.page_dados, "Dados do Produto")
        self.tabs.addTab(self.page_msds,  "Ficha de Segurança")

        # ---------- Guia: Dados do Produto ----------
        grid = QGridLayout(self.page_dados)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(10)
        grid.setContentsMargins(8, 8, 8, 8)

        # 9 colunas: [0]=label, [1..2]=campo, [3]=label, [4..5]=campo, [6]=label, [7..8]=campo
        for i in (1, 2, 4, 5, 7, 8):
            grid.setColumnStretch(i, 1)
        grid.setColumnMinimumWidth(0, 130)
        grid.setColumnMinimumWidth(3, 130)
        grid.setColumnMinimumWidth(6, 130)

        r = 0
        # Título do produto
        grid.addWidget(_lbl("Produto"), r, 0)
        self.ed_nome = _h28(QLineEdit()); self.ed_nome.setMinimumWidth(300)
        grid.addWidget(self.ed_nome, r, 1, 1, 8)
        r += 1

        # Linha: Código, Família, Cor
        grid.addWidget(_lbl("Código"), r, 0)
        self.ed_codigo = _h28(QLineEdit())
        grid.addWidget(self.ed_codigo, r, 1, 1, 2)

        grid.addWidget(_lbl("Família do produto"), r, 3)
        self.cb_familia = _h28(QComboBox()); self.cb_familia.setEditable(True)
        self.cb_familia.addItems(["", "Composto Micropellet", "Composto Minipellet", "Composto Micronizado"])
        grid.addWidget(self.cb_familia, r, 4, 1, 2)

        grid.addWidget(_lbl("Cor"), r, 6)
        cor_wrap = QFrame(); cor_l = QHBoxLayout(cor_wrap); cor_l.setContentsMargins(0, 0, 0, 0); cor_l.setSpacing(6)
        self.cb_cor = _h28(QComboBox()); self.cb_cor.setEditable(True)
        self.cb_cor.addItems(["", "Natural", "Azul", "Vermelho", "Preto", "#FF0000", "#0080FF"])
        self.lbl_swatch = QLabel(); self.lbl_swatch.setFixedSize(24, 24); self.lbl_swatch.setFrameShape(QFrame.Shape.Box); self.lbl_swatch.setAutoFillBackground(True)
        cor_l.addWidget(self.cb_cor); cor_l.addWidget(self.lbl_swatch, alignment=Qt.AlignmentFlag.AlignVCenter)
        grid.addWidget(cor_wrap, r, 7, 1, 2)
        r += 1

        # Linha: Segmento, Reavaliar dias, Direto extrusão
        grid.addWidget(_lbl("Segmento"), r, 0)
        self.cb_segmento = _h28(QComboBox()); self.cb_segmento.setEditable(True)
        self.cb_segmento.addItems(["", "Rotomoldagem", "Injeção", "Sopro"])
        grid.addWidget(self.cb_segmento, r, 1, 1, 2)

        grid.addWidget(_lbl("Reavaliar padrão a cada"), r, 3)
        reav_wrap = QFrame(); reav_l = QHBoxLayout(reav_wrap); reav_l.setContentsMargins(0,0,0,0); reav_l.setSpacing(6)
        self.sp_reavaliar = _h28(QSpinBox()); self.sp_reavaliar.setRange(0, 9999)
        reav_l.addWidget(self.sp_reavaliar); reav_l.addWidget(QLabel("dias"))
        grid.addWidget(reav_wrap, r, 4, 1, 2)

        grid.addWidget(_lbl("Direto na Extrusão"), r, 6)
        self.cb_extrusao = _h28(QComboBox()); self.cb_extrusao.addItems(["Não", "Sim"])
        grid.addWidget(self.cb_extrusao, r, 7, 1, 2)
        r += 1

        # Linha: Localização, Fabricado em, Lote padrão
        grid.addWidget(_lbl("Localização Padrão"), r, 0)
        self.ed_local = _h28(QLineEdit())
        grid.addWidget(self.ed_local, r, 1, 1, 2)

        grid.addWidget(_lbl("Fabricado em"), r, 3)
        self.dt_fabricado = _h28(QDateEdit()); self.dt_fabricado.setCalendarPopup(True); self.dt_fabricado.setDate(QDate.currentDate())
        grid.addWidget(self.dt_fabricado, r, 4, 1, 2)

        grid.addWidget(_lbl("Lote Padrão"), r, 6)
        self.ed_lote = _h28(QLineEdit())
        grid.addWidget(self.ed_lote, r, 7, 1, 2)
        r += 1

        # Linha: Válido até, Revisão Nº, Data Revisão
        grid.addWidget(_lbl("Válido Até"), r, 0)
        self.dt_valido = _h28(QDateEdit()); self.dt_valido.setCalendarPopup(True); self.dt_valido.setDate(QDate.currentDate())
        grid.addWidget(self.dt_valido, r, 1, 1, 2)

        grid.addWidget(_lbl("Revisão Nº"), r, 3)
        self.ed_rev = _h28(QLineEdit()); self.ed_rev.setMaximumWidth(120)
        grid.addWidget(self.ed_rev, r, 4, 1, 2)

        grid.addWidget(_lbl("Data Revisão"), r, 6)
        self.dt_revisao = _h28(QDateEdit()); self.dt_revisao.setCalendarPopup(True); self.dt_revisao.setDate(QDate.currentDate())
        grid.addWidget(self.dt_revisao, r, 7, 1, 2)
        r += 1

        # Linha: Histórico
        grid.addWidget(_lbl("Histórico das Revisões"), r, 0)
        self.txt_historico = _h28(QLineEdit()); self.txt_historico.setPlaceholderText("Ex.: Revisão: 00 - 21/11/2014 - Emissão inicial")
        grid.addWidget(self.txt_historico, r, 1, 1, 8)
        r += 1

        # Seção: Descrição Geral
        grid.addWidget(self._section_title("Descrição Geral"), r, 0, 1, 9); r += 1
        self.descricao_pt = self._lang_text(grid, r, "PT"); r += 1
        self.descricao_en = self._lang_text(grid, r, "EN"); r += 1
        self.descricao_es = self._lang_text(grid, r, "ES"); r += 1

        # Seção: Aplicações
        grid.addWidget(self._section_title("Aplicações"), r, 0, 1, 9); r += 1
        self.aplicacoes_pt = self._lang_text(grid, r, "PT"); r += 1
        self.aplicacoes_en = self._lang_text(grid, r, "EN"); r += 1
        self.aplicacoes_es = self._lang_text(grid, r, "ES"); r += 1

        # ---------- Guia: Ficha de Segurança ----------
        ms = QVBoxLayout(self.page_msds)
        ms.setContentsMargins(8, 8, 8, 8)
        self.txt_msds = QTextEdit()
        self.txt_msds.setPlaceholderText("Cole observações ou um link para a ficha de segurança")
        self.txt_msds.setMinimumHeight(180)
        ms.addWidget(self.txt_msds)

        # Navegação
        nav = QFrame()
        nb = QHBoxLayout(nav); nb.setContentsMargins(0,0,0,0); nb.setSpacing(6)
        self.btn_first = QPushButton("≪"); self.btn_prev = QPushButton("‹"); self.btn_next = QPushButton("›"); self.btn_last = QPushButton("≫")
        for b in [self.btn_first, self.btn_prev, self.btn_next, self.btn_last]:
            b.setProperty("kind", "outline"); b.setFixedWidth(36); b.setMinimumHeight(28)
        self.lbl_status = QLabel("Registros")
        nb.addWidget(self.btn_first); nb.addWidget(self.btn_prev)
        nb.addWidget(self.btn_next);  nb.addWidget(self.btn_last)
        nb.addStretch(1)
        nb.addWidget(self.lbl_status)

        # Montagem
        root.addWidget(toolbar)
        root.addWidget(self.tabs, 1)
        root.addWidget(nav)

        # Sinais
        self.cb_cor.editTextChanged.connect(self._update_swatch)
        self.btn_new.clicked.connect(self._new)
        self.btn_save.clicked.connect(self._save)
        self.btn_del.clicked.connect(self._delete)
        self.btn_find.clicked.connect(self._search)

        self.btn_first.clicked.connect(lambda: self._goto(0))
        self.btn_prev.clicked.connect(lambda: self._goto(max(0, self.index - 1)))
        self.btn_next.clicked.connect(lambda: self._goto(min(len(self.ids) - 1, self.index + 1)))
        self.btn_last.clicked.connect(lambda: self._goto(len(self.ids) - 1))

        # Inicialização
        self._update_swatch(self.cb_cor.currentText())
        self._reload_all()

    # ---------- helpers de UI ----------
    def _section_title(self, texto: str) -> QLabel:
        t = QLabel(texto)
        t.setObjectName("SectionTitle")
        return t

    def _lang_text(self, grid: QGridLayout, row: int, sigla: str) -> QTextEdit:
        tag = QLabel(sigla)
        tag.setObjectName("LangTag")
        tag.setAlignment(Qt.AlignmentFlag.AlignCenter)
        txt = QTextEdit(); txt.setMinimumHeight(64)
        grid.addWidget(tag, row, 0, 1, 1)
        grid.addWidget(txt, row, 1, 1, 8)
        return txt

    def _update_swatch(self, text: str):
        color = QColor(text) if text else QColor("#FFFFFF")
        if not color.isValid():
            color = QColor("#FFFFFF")
        pal = self.lbl_swatch.palette()
        pal.setColor(QPalette.ColorRole.Window, color)
        self.lbl_swatch.setPalette(pal)
        self.lbl_swatch.setAutoFillBackground(True)

    # ---------- dados ----------
    def _reload_all(self, where: str = "", args: tuple = ()):
        cur = self.db.conn.cursor()
        sql = "SELECT id FROM produtos"
        if where:
            sql += " WHERE " + where
        sql += " ORDER BY COALESCE(codigo, ''), COALESCE(nome, '')"
        cur.execute(sql, args)
        self.ids = [r[0] for r in cur.fetchall()]
        self._goto(0 if self.ids else -1)

    def _goto(self, idx: int):
        if idx < 0 or idx >= len(self.ids):
            self._clear()
            self.index = -1
            self._update_status()
            return
        self.index = idx
        self._load(self.ids[idx])
        self._update_status()

    def _update_status(self):
        total = len(self.ids)
        pos = self.index + 1 if self.index >= 0 else 0
        self.lbl_status.setText(f"Registros  {pos} de {total}")

    def _clear(self):
        self._building = True
        self._current_id = None
        self.ed_nome.clear(); self.ed_codigo.clear()
        self.cb_familia.setCurrentIndex(0)
        self.cb_cor.setCurrentIndex(0); self._update_swatch("")
        self.cb_segmento.setCurrentIndex(0)
        self.sp_reavaliar.setValue(0)
        self.cb_extrusao.setCurrentIndex(0)
        self.ed_local.clear(); self.dt_fabricado.setDate(QDate.currentDate())
        self.ed_lote.clear(); self.dt_valido.setDate(QDate.currentDate())
        self.ed_rev.clear(); self.dt_revisao.setDate(QDate.currentDate())
        self.txt_historico.clear()
        for attr in ["descricao_pt", "descricao_en", "descricao_es",
                     "aplicacoes_pt", "aplicacoes_en", "aplicacoes_es"]:
            getattr(self, attr).clear()
        self.txt_msds.clear()
        self._building = False

    def _to_date(self, s):
        try:
            y, m, d = str(s or "").split("-")
            return QDate(int(y), int(m), int(d))
        except Exception:
            return QDate.currentDate()

    def _load(self, pid: int):
        self._building = True
        cur = self.db.conn.cursor()
        cur.execute("""
            SELECT id, nome, codigo, familia, cor, segmento, reavaliar_dias, extrusao_direto,
                   localizacao, fabricado_em, lote_padrao, valido_ate, revisao_num, revisao_data,
                   historico, descricao_pt, descricao_en, descricao_es,
                   aplicacoes_pt, aplicacoes_en, aplicacoes_es, ficha_seguranca
            FROM produtos WHERE id=?""", (pid,))
        r = cur.fetchone()
        self._clear()
        if r:
            self._current_id = r[0]
            self.ed_nome.setText(r[1] or "")
            self.ed_codigo.setText(r[2] or "")
            self.cb_familia.setEditText(r[3] or "")
            self.cb_cor.setEditText(r[4] or ""); self._update_swatch(self.cb_cor.currentText())
            self.cb_segmento.setEditText(r[5] or "")
            self.sp_reavaliar.setValue(int(r[6] or 0))
            self.cb_extrusao.setCurrentIndex(1 if (r[7] or 0) else 0)
            self.ed_local.setText(r[8] or "")
            self.dt_fabricado.setDate(self._to_date(r[9]))
            self.ed_lote.setText(r[10] or "")
            self.dt_valido.setDate(self._to_date(r[11]))
            self.ed_rev.setText(r[12] or "")
            self.dt_revisao.setDate(self._to_date(r[13]))
            self.txt_historico.setText(r[14] or "")
            self.descricao_pt.setPlainText(r[15] or "")
            self.descricao_en.setPlainText(r[16] or "")
            self.descricao_es.setPlainText(r[17] or "")
            self.aplicacoes_pt.setPlainText(r[18] or "")
            self.aplicacoes_en.setPlainText(r[19] or "")
            self.aplicacoes_es.setPlainText(r[20] or "")
            self.txt_msds.setPlainText(r[21] or "")
        self._building = False

    def _collect(self):
        return {
            "nome": self.ed_nome.text().strip(),
            "codigo": self.ed_codigo.text().strip(),
            "familia": self.cb_familia.currentText().strip(),
            "cor": self.cb_cor.currentText().strip(),
            "segmento": self.cb_segmento.currentText().strip(),
            "reavaliar_dias": self.sp_reavaliar.value(),
            "extrusao_direto": 1 if self.cb_extrusao.currentText() == "Sim" else 0,
            "localizacao": self.ed_local.text().strip(),
            "fabricado_em": self.dt_fabricado.date().toString("yyyy-MM-dd"),
            "lote_padrao": self.ed_lote.text().strip(),
            "valido_ate": self.dt_valido.date().toString("yyyy-MM-dd"),
            "revisao_num": self.ed_rev.text().strip(),
            "revisao_data": self.dt_revisao.date().toString("yyyy-MM-dd"),
            "historico": self.txt_historico.text().strip(),
            "descricao_pt": self.descricao_pt.toPlainText().strip(),
            "descricao_en": self.descricao_en.toPlainText().strip(),
            "descricao_es": self.descricao_es.toPlainText().strip(),
            "aplicacoes_pt": self.aplicacoes_pt.toPlainText().strip(),
            "aplicacoes_en": self.aplicacoes_en.toPlainText().strip(),
            "aplicacoes_es": self.aplicacoes_es.toPlainText().strip(),
            "ficha_seguranca": self.txt_msds.toPlainText().strip(),
        }

    def _new(self):
        self._clear()

    def _save(self):
        data = self._collect()
        cur = self.db.conn.cursor()
        if getattr(self, "_current_id", None):
            sets = ", ".join([f"{k}=?" for k in data.keys()])
            cur.execute(f"UPDATE produtos SET {sets} WHERE id=?", (*data.values(), self._current_id))
        else:
            cols = ", ".join(data.keys())
            qs   = ", ".join("?" for _ in data)
            cur.execute(f"INSERT INTO produtos ({cols}) VALUES ({qs})", tuple(data.values()))
            self._current_id = cur.lastrowid
        self.db.conn.commit()
        self._reload_all(where="id=?", args=(self._current_id,))

    def _delete(self):
        if not getattr(self, "_current_id", None):
            return
        cur = self.db.conn.cursor()
        cur.execute("DELETE FROM produtos WHERE id=?", (self._current_id,))
        self.db.conn.commit()
        self._reload_all()

    def _search(self):
        txt = self.ed_busca.text().strip()
        if not txt:
            self._reload_all()
            return
        like = f"%{txt}%"
        self._reload_all(where="codigo LIKE ? OR nome LIKE ? OR segmento LIKE ?",
                         args=(like, like, like))
