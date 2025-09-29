from __future__ import annotations
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QDateEdit, QComboBox, QLineEdit,
    QPushButton, QGroupBox, QRadioButton, QWidget, QGridLayout, QMessageBox,
    QSizePolicy
)
from PyQt6.QtCore import Qt, QDate
from typing import List, Tuple


class ReportsWidget(QFrame):
    """
    Tela de Consultas/Relatórios no layout do print (Access).

    - Período Inicial/Final (QDateEdit)
    - Lote (QComboBox, editável)
    - Produto (QComboBox, editável)
    - Rótulo "Produto Pesquisado"
    - Grupo "Opções de Relatórios" com rádios em duas colunas
    - Botões "Gerar" e "Imprimir" (ganchos para você plugar seu gerador)

    Observação: fazemos tentativas de preencher Produto/Lote a partir do DB;
    se as tabelas/colunas não existirem, os combos ficam vazios mas editáveis.
    """
    def __init__(self, db):
        super().__init__(objectName="Card")
        self.db = db

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        # ---------- Barra superior (botões de ação) ----------
        topbar = QHBoxLayout()
        topbar.addStretch(1)

        self.btn_print = QPushButton("Imprimir")
        self.btn_print.setProperty("kind", "outline")
        self.btn_print.clicked.connect(self._on_print)
        topbar.addWidget(self.btn_print)

        self.btn_generate = QPushButton("Gerar")
        self.btn_generate.setProperty("kind", "primary")
        self.btn_generate.clicked.connect(self._on_generate)
        topbar.addWidget(self.btn_generate)

        root.addLayout(topbar)

        # ---------- Linha com título "Consultas" (opcional) ----------
        title = QLabel("Consultas", objectName="PageSubtitle")
        title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        title.setStyleSheet("font-weight: 600; font-size: 18px; color: #3a3a3a;")
        root.addWidget(title)

        # ---------- Conteúdo principal ----------
        content = QHBoxLayout()
        content.setSpacing(16)
        root.addLayout(content, 1)

        # ========== Coluna esquerda: filtros ==========
        left_card = QFrame(objectName="Card")
        left_card.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        left = QGridLayout(left_card)
        left.setContentsMargins(14, 14, 14, 14)
        left.setHorizontalSpacing(10)
        left.setVerticalSpacing(8)

        # Período
        left.addWidget(QLabel("Período Inicial:"), 0, 0, Qt.AlignmentFlag.AlignVCenter)
        self.dt_ini = QDateEdit()
        self.dt_ini.setCalendarPopup(True)
        self.dt_ini.setDisplayFormat("dd/MM/yyyy")
        self.dt_ini.setDate(QDate.currentDate().addDays(-30))
        left.addWidget(self.dt_ini, 0, 1)

        left.addWidget(QLabel("Período Final:"), 1, 0, Qt.AlignmentFlag.AlignVCenter)
        self.dt_fim = QDateEdit()
        self.dt_fim.setCalendarPopup(True)
        self.dt_fim.setDisplayFormat("dd/MM/yyyy")
        self.dt_fim.setDate(QDate.currentDate())
        left.addWidget(self.dt_fim, 1, 1)

        # Lote
        left.addWidget(QLabel("Lote"), 2, 0)
        self.cmb_lote = QComboBox(); self.cmb_lote.setEditable(True)
        self.cmb_lote.setMinimumWidth(200)
        left.addWidget(self.cmb_lote, 2, 1)

        # Produto
        left.addWidget(QLabel("Produto"), 3, 0)
        self.cmb_prod = QComboBox(); self.cmb_prod.setEditable(True)
        self.cmb_prod.setMinimumWidth(200)
        left.addWidget(self.cmb_prod, 3, 1)

        # Produto Pesquisado (rótulo)
        self.lbl_pesquisado = QLabel("Produto Pesquisado")
        self.lbl_pesquisado.setStyleSheet("color:#6b7280; margin-top:10px;")
        left.addWidget(self.lbl_pesquisado, 4, 0, 1, 2)

        content.addWidget(left_card)

        # ========== Coluna direita: opções de relatórios ==========
        right_card = QFrame(objectName="Card")
        right = QVBoxLayout(right_card)
        right.setContentsMargins(14, 14, 14, 14)
        right.setSpacing(10)

        group_title = QLabel("Opções de Relatórios")
        group_title.setStyleSheet("font-weight:600;")
        right.addWidget(group_title)

        options_box = self._build_options_group()
        right.addWidget(options_box, 1)

        content.addWidget(right_card, 1)

        # Eventos simples para atualizar o rótulo "Produto Pesquisado"
        self.cmb_prod.editTextChanged.connect(self._update_pesquisado)
        self.cmb_prod.currentTextChanged.connect(self._update_pesquisado)

        # Tenta carregar produto/lote do DB
        self._try_load_produtos()
        self._try_load_lotes()

    # ==================================================================
    # Construção dos rádios
    # ==================================================================
    def _build_options_group(self) -> QWidget:
        """
        Cria duas colunas de rádios como no print.
        """
        container = QFrame()
        grid = QGridLayout(container)
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(8)
        grid.setContentsMargins(0, 0, 0, 0)

        # lista da esquerda
        left_opts: List[Tuple[str, str]] = [
            ("spec_produto",      "Especificação Produto"),
            ("spec_grupo",        "Especificação p/ Grupo"),
            ("fispq",             "Imprime FISPQ"),
            ("cert_por_lote",     "Certificados por lote"),
            ("cert_por_produto",  "Certificados por produto"),
            ("ceq",               "Controle Estatístico (CEQ)"),
        ]
        # lista da direita
        right_opts: List[Tuple[str, str]] = [
            ("res_lote",          "Resultados por lote"),
            ("res_produto",       "Resultados por produto"),
            ("cliente_prod",      "Cliente x produto"),
            ("ensaios_prod",      "Ensaios por produto"),
            ("lib_especial",      "Liberação Especial Produto"),
        ]

        self._radios: dict[str, QRadioButton] = {}

        # esquerda (col 0)
        for i, (key, text) in enumerate(left_opts):
            rb = QRadioButton(text)
            self._radios[key] = rb
            grid.addWidget(rb, i, 0, Qt.AlignmentFlag.AlignLeft)

        # direita (col 1)
        for i, (key, text) in enumerate(right_opts):
            rb = QRadioButton(text)
            self._radios[key] = rb
            grid.addWidget(rb, i, 1, Qt.AlignmentFlag.AlignLeft)

        # marca "Resultados por lote" por padrão (igual imagem)
        self._radios["res_lote"].setChecked(True)

        return container

    def _selected_report_key(self) -> str:
        for key, rb in self._radios.items():
            if rb.isChecked():
                return key
        return "res_lote"

    # ==================================================================
    # Ações (ganchos)
    # ==================================================================
    def _on_generate(self):
        # Parâmetros básicos
        p_ini = self.dt_ini.date().toString("yyyy-MM-dd")
        p_fim = self.dt_fim.date().toString("yyyy-MM-dd")
        lote = self.cmb_lote.currentText().strip()
        prod = self.cmb_prod.currentText().strip()
        key = self._selected_report_key()

        # Aqui você pluga seu gerador real (PDF/planilha/view).
        # Por enquanto só mostramos um resumo do que foi solicitado.
        resumo = (
            f"Relatório: {self._label_by_key(key)}\n"
            f"Período: {p_ini} a {p_fim}\n"
            f"Lote: {lote or '—'}\n"
            f"Produto: {prod or '—'}"
        )
        QMessageBox.information(self, "Gerar relatório", resumo)

    def _on_print(self):
        # Mesmo gancho do gerar, mas separado.
        key = self._selected_report_key()
        QMessageBox.information(self, "Imprimir",
                                f"Enviar para impressão: {self._label_by_key(key)}")

    # ==================================================================
    # DB helpers (tentativas seguras)
    # ==================================================================
    def _try_load_produtos(self):
        """
        Tenta carregar produtos do DB (várias hipóteses de tabelas/colunas).
        Se falhar, o combo permanece vazio (editável).
        """
        cur = self.db.conn.cursor()
        queries = [
            ("SELECT descricao FROM produtos ORDER BY 1", 0),
            ("SELECT nome FROM produtos ORDER BY 1", 0),
            ("SELECT descricao_pt FROM produtos ORDER BY 1", 0),
        ]
        for sql, idx in queries:
            try:
                cur.execute(sql)
                rows = [r[idx] for r in cur.fetchall() if r and r[idx]]
                if rows:
                    self.cmb_prod.clear()
                    self.cmb_prod.addItems(rows)
                    break
            except Exception:
                continue

    def _try_load_lotes(self):
        """
        Tenta carregar lotes do DB (se existir alguma tabela de lotes).
        """
        cur = self.db.conn.cursor()
        queries = [
            ("SELECT DISTINCT lote FROM inspecoes ORDER BY 1 DESC", 0),
            ("SELECT DISTINCT lote FROM certificados ORDER BY 1 DESC", 0),
        ]
        for sql, idx in queries:
            try:
                cur.execute(sql)
                rows = [r[idx] for r in cur.fetchall() if r and r[idx]]
                if rows:
                    self.cmb_lote.clear()
                    self.cmb_lote.addItems(rows)
                    break
            except Exception:
                continue

    # ==================================================================
    # Utilidades
    # ==================================================================
    def _update_pesquisado(self, _=None):
        txt = self.cmb_prod.currentText().strip()
        self.lbl_pesquisado.setText(f"Produto Pesquisado: {txt}" if txt else "Produto Pesquisado")

    def _label_by_key(self, key: str) -> str:
        mapping = {
            "spec_produto":     "Especificação Produto",
            "spec_grupo":       "Especificação p/ Grupo",
            "fispq":            "Imprime FISPQ",
            "cert_por_lote":    "Certificados por lote",
            "cert_por_produto": "Certificados por produto",
            "ceq":              "Controle Estatístico (CEQ)",
            "res_lote":         "Resultados por lote",
            "res_produto":      "Resultados por produto",
            "cliente_prod":     "Cliente x produto",
            "ensaios_prod":     "Ensaios por produto",
            "lib_especial":     "Liberação Especial Produto",
        }
        return mapping.get(key, key)
