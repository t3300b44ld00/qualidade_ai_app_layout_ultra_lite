# app/ui/screens/certificado.py
from PyQt6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QLineEdit, QPushButton, QSizePolicy, QPlainTextEdit
)
from PyQt6.QtCore import Qt


class CertificadoWidget(QWidget):
    """
    Emissão de Certificado
    - Topo: selecionar produto (código + descrição) e lote, com botão Sair
    - Centro: área de pré-visualização (placeholder por enquanto)
    - Rodapé: faixa para compor o layout como no sistema antigo
    """
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self._build_ui()
        self._wire_signals()
        self._load_produtos()

    # ---------- UI ----------
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        # Barra superior (igual ao mock)
        top = QFrame(objectName="Card")
        top_l = QHBoxLayout(top)
        top_l.setContentsMargins(12, 10, 12, 10)
        top_l.setSpacing(12)

        # Bloco: Selecione o Produto
        prod_blk = QVBoxLayout()
        prod_blk.setSpacing(4)
        prod_lbl = QLabel("Selecione o Produto")
        prod_row = QHBoxLayout()
        prod_row.setSpacing(6)

        self.cmb_codigo = QComboBox()
        self.cmb_codigo.setMinimumWidth(120)

        self.txt_desc = QLineEdit()
        self.txt_desc.setReadOnly(True)
        self.txt_desc.setPlaceholderText("Descrição do produto")

        prod_row.addWidget(self.cmb_codigo)
        prod_row.addWidget(self.txt_desc, 1)
        prod_blk.addWidget(prod_lbl)
        prod_blk.addLayout(prod_row)

        # Bloco: Selecione um lote
        lote_blk = QVBoxLayout()
        lote_blk.setSpacing(4)
        lote_lbl = QLabel("Selecione um lote")
        lote_row = QHBoxLayout()
        lote_row.setSpacing(6)

        self.cmb_lote = QComboBox()
        self.cmb_lote.setMinimumWidth(160)

        self.btn_sair = QPushButton("Sair")
        self.btn_sair.setProperty("kind", "outline")

        lote_row.addWidget(self.cmb_lote)
        lote_row.addWidget(self.btn_sair)
        lote_blk.addWidget(lote_lbl)
        lote_blk.addLayout(lote_row)

        top_l.addLayout(prod_blk, 1)
        top_l.addLayout(lote_blk, 0)

        # Centro: pré-visualização (placeholder)
        self.preview = QPlainTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setPlainText(
            "Pré-visualização do certificado.\n"
            "Selecione um produto e um lote."
        )
        self.preview.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Rodapé (faixa cinza do layout antigo)
        footer = QFrame(objectName="Footer")
        footer.setMinimumHeight(36)

        root.addWidget(top)
        root.addWidget(self.preview, 1)
        root.addWidget(footer)

    # ---------- Sinais ----------
    def _wire_signals(self):
        self.cmb_codigo.currentIndexChanged.connect(self._on_produto_trocado)
        self.cmb_lote.currentIndexChanged.connect(self._on_lote_trocado)
        self.btn_sair.clicked.connect(self._voltar_principal)

    # ---------- Dados ----------
    def _load_produtos(self):
        """Tenta popular os produtos (código + descrição) de forma resiliente."""
        self.cmb_codigo.clear()
        cur = self.db.conn.cursor()
        rows = []
        try:
            # tentativa 1: produtos(codigo, nome)
            cur.execute("SELECT codigo, nome FROM produtos ORDER BY codigo")
            rows = cur.fetchall()
        except Exception:
            try:
                # tentativa 2: produtos(codigo, descricao_pt)
                cur.execute("SELECT codigo, descricao_pt FROM produtos ORDER BY codigo")
                rows = cur.fetchall()
            except Exception:
                rows = []

        for cod, desc in rows:
            self.cmb_codigo.addItem(str(cod), {"codigo": cod, "desc": desc})

        if rows:
            self._on_produto_trocado(0)  # carrega lotes do primeiro
        else:
            self.txt_desc.clear()
            self.cmb_lote.clear()

    def _load_lotes(self, codigo_prod):
        """Tenta buscar lotes para o produto nas tabelas mais prováveis."""
        self.cmb_lote.clear()
        cur = self.db.conn.cursor()
        lotes = []

        # 1) tabela lotes(produto_codigo, lote)
        try:
            cur.execute(
                "SELECT DISTINCT lote FROM lotes WHERE produto_codigo=? ORDER BY lote DESC",
                (codigo_prod,),
            )
            lotes = [r[0] for r in cur.fetchall()]
        except Exception:
            pass

        # 2) fallback: inspecoes(codigo_produto, lote)
        if not lotes:
            try:
                cur.execute(
                    "SELECT DISTINCT lote FROM inspecoes WHERE codigo_produto=? ORDER BY lote DESC",
                    (codigo_prod,),
                )
                lotes = [r[0] for r in cur.fetchall()]
            except Exception:
                pass

        # 3) fallback alternativo: inspecoes(produto, lote)
        if not lotes:
            try:
                cur.execute(
                    "SELECT DISTINCT lote FROM inspecoes WHERE produto=? ORDER BY lote DESC",
                    (codigo_prod,),
                )
                lotes = [r[0] for r in cur.fetchall()]
            except Exception:
                pass

        if lotes:
            self.cmb_lote.addItems([str(l) for l in lotes])
        else:
            self.preview.setPlainText(
                "Nenhum lote encontrado para o produto selecionado."
            )

    # ---------- Handlers ----------
    def _on_produto_trocado(self, _):
        data = self.cmb_codigo.currentData()
        self.txt_desc.setText("" if not data else str(data.get("desc", "")))
        if data:
            self._load_lotes(data["codigo"])
            if self.cmb_lote.count():
                self._on_lote_trocado(0)

    def _on_lote_trocado(self, _):
        prod = self.cmb_codigo.currentText()
        desc = self.txt_desc.text()
        lote = self.cmb_lote.currentText()
        if not lote:
            return
        # Monta uma prévia simples (substitua pela renderização real do certificado)
        self.preview.setPlainText(
            f"Produto: {prod} - {desc}\n"
            f"Lote: {lote}\n\n"
            "Pré-visualização do Certificado.\n"
            "— Quando a geração estiver pronta, renderize aqui o PDF/HTML."
        )

    def _voltar_principal(self):
        # volta para o dashboard (funciona dentro do wrapper do MainWindow)
        mw = self.window()
        if hasattr(mw, "pages") and hasattr(mw, "page_dashboard"):
            mw.pages.setCurrentWidget(mw.page_dashboard)
