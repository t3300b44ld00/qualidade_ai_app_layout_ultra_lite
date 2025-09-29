
from __future__ import annotations

import csv
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QFileDialog, QMessageBox, QSizePolicy, QComboBox
)
from PyQt6.QtGui import QTextDocument, QPageSize
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog


@dataclass
class CertRow:
    laudo: str
    emissao: str
    codigo: str
    cliente: str
    nota: str
    lote: str
    qte: str


class ImpressaoCertificadosWidget(QWidget):
    """
    Tela de consulta/impressão dos certificados.
    - Consulta a tabela cert_consulta (criada se não existir).
    - Importa CSV para popular rapidamente a tabela.
    - Gera PDF/Imprime um certificado visual a partir da linha selecionada.
    """
    def __init__(self, db):
        super().__init__()
        self.db = db
        self._ensure_table()

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        # Barra de filtros + ações
        bar = QFrame(objectName="Card")
        hb = QHBoxLayout(bar)
        hb.setContentsMargins(12, 12, 12, 12)
        hb.setSpacing(8)

        def col(label: str, w: int = 160) -> QVBoxLayout:
            box = QVBoxLayout()
            box.setSpacing(4)
            box.addWidget(QLabel(label))
            return box

        # Filtros
        self.ed_codigo = QLineEdit(); self.ed_codigo.setPlaceholderText("Código")
        self.ed_cliente = QLineEdit(); self.ed_cliente.setPlaceholderText("Cliente")
        self.ed_nf = QLineEdit(); self.ed_nf.setPlaceholderText("N. Fiscal")
        self.ed_lote = QLineEdit(); self.ed_lote.setPlaceholderText("Lote")

        c1 = col("Código"); c1.addWidget(self.ed_codigo)
        c2 = col("Cliente"); c2.addWidget(self.ed_cliente)
        c3 = col("N. Fiscal"); c3.addWidget(self.ed_nf)
        c4 = col("Lote"); c4.addWidget(self.ed_lote)

        hb.addLayout(c1); hb.addLayout(c2); hb.addLayout(c3); hb.addLayout(c4)

        self.btn_consultar = QPushButton("Consultar"); self.btn_consultar.setProperty("kind","primary")
        self.btn_import = QPushButton("Importar CSV")
        self.btn_pdf = QPushButton("Gerar Certificado (PDF)")
        self.btn_print = QPushButton("Imprimir Certificado")

        for b in (self.btn_consultar, self.btn_import, self.btn_pdf, self.btn_print):
            b.setMinimumHeight(32)
            hb.addWidget(b)

        self.btn_sair = QPushButton("Sair"); self.btn_sair.setProperty("kind","outline")
        hb.addStretch(1); hb.addWidget(self.btn_sair)

        root.addWidget(bar)

        # Tabela
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(["Nº Laudo", "Emissão", "Código", "Cliente", "Nota", "Lote", "QTE"])
        self.table.setSelectionBehavior(self.table.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(self.table.SelectionMode.SingleSelection)
        self.table.setEditTriggers(self.table.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        root.addWidget(self.table, 1)

        # Ligação de eventos
        self.btn_consultar.clicked.connect(self._consultar)
        self.btn_import.clicked.connect(self._importar_csv)
        self.btn_pdf.clicked.connect(self._salvar_pdf)
        self.btn_print.clicked.connect(self._imprimir)
        self.btn_sair.clicked.connect(self._limpar_filtros)

        # Consulta inicial (opcional)
        self._consultar()

    # ---------- Infra de dados ----------
    def _ensure_table(self):
        cur = self.db.conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS cert_consulta (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                laudo TEXT, emissao TEXT, codigo TEXT, cliente TEXT,
                nota TEXT, lote TEXT, qte TEXT
            );
        """)
        self.db.conn.commit()

    # ---------- Ações ----------
    def _limpar_filtros(self):
        self.ed_codigo.clear(); self.ed_cliente.clear(); self.ed_nf.clear(); self.ed_lote.clear()

    def _consultar(self):
        sql = "SELECT laudo, emissao, codigo, cliente, nota, lote, qte FROM cert_consulta WHERE 1=1"
        params = []
        if self.ed_codigo.text().strip():
            sql += " AND codigo LIKE ?"; params.append(f"%{self.ed_codigo.text().strip()}%")
        if self.ed_cliente.text().strip():
            sql += " AND cliente LIKE ?"; params.append(f"%{self.ed_cliente.text().strip()}%")
        if self.ed_nf.text().strip():
            sql += " AND nota LIKE ?"; params.append(f"%{self.ed_nf.text().strip()}%")
        if self.ed_lote.text().strip():
            sql += " AND lote LIKE ?"; params.append(f"%{self.ed_lote.text().strip()}%")

        sql += " ORDER BY CAST(REPLACE(laudo,'/','') AS INTEGER) DESC"

        cur = self.db.conn.cursor()
        cur.execute(sql, params)
        rows = cur.fetchall()

        self.table.setRowCount(0)
        for r in rows:
            i = self.table.rowCount()
            self.table.insertRow(i)
            for c, val in enumerate(r):
                item = QTableWidgetItem(str(val or ""))
                if c in (0,1):  # laudo/emissao
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(i, c, item)

    def _importar_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "Selecione CSV", "", "CSV (*.csv)")
        if not path:
            return
        inserted = 0
        with open(path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f, delimiter=",", quotechar='"')
            cur = self.db.conn.cursor()
            for row in reader:
                # tenta mapear nomes variados de cabeçalhos
                laudo = row.get("Nº Laudo") or row.get("Laudo") or row.get("N Laudo") or row.get("N_laudo") or ""
                emissao = row.get("Emissão") or row.get("Emissao") or row.get("Data") or ""
                codigo = row.get("Código") or row.get("Codigo") or row.get("Cod") or ""
                cliente = row.get("Cliente") or ""
                nota = row.get("Nota") or row.get("N. Fiscal") or row.get("NF") or ""
                lote = row.get("Lote") or ""
                qte  = row.get("QTE") or row.get("Qtd") or row.get("Quantidade") or ""

                cur.execute("""
                    INSERT INTO cert_consulta(laudo, emissao, codigo, cliente, nota, lote, qte)
                    VALUES (?,?,?,?,?,?,?)
                """, (str(laudo), str(emissao), str(codigo), str(cliente), str(nota), str(lote), str(qte)))
                inserted += 1

        self.db.conn.commit()
        QMessageBox.information(self, "Importação", f"{inserted} registros importados.")
        self._consultar()

    def _linha_selecionada(self) -> Optional[CertRow]:
        idxs = self.table.selectionModel().selectedRows()
        if not idxs:
            QMessageBox.information(self, "Atenção", "Selecione uma linha para gerar/imprimir o certificado.")
            return None
        r = idxs[0].row()
        return CertRow(
            laudo=self.table.item(r,0).text(),
            emissao=self.table.item(r,1).text(),
            codigo=self.table.item(r,2).text(),
            cliente=self.table.item(r,3).text(),
            nota=self.table.item(r,4).text(),
            lote=self.table.item(r,5).text(),
            qte=self.table.item(r,6).text(),
        )

    # ---------- Certificado (HTML -> PDF/Impressora) ----------
    def _cert_html(self, row: CertRow) -> str:
        # HTML simples e responsivo para A4
        return f"""
<!DOCTYPE html>
<html>
<head>
<meta charset='utf-8'>
<style>
  body {{ font-family: Arial, Helvetica, sans-serif; color:#222; }}
  .title {{ text-align:center; font-size:20px; font-weight:bold; margin-bottom:8px; color:#1f4bf0; }}
  .sub {{ text-align:center; font-size:12px; color:#888; margin-bottom:20px; }}
  .grid {{ width:100%; border-collapse:collapse; margin-top:12px; }}
  .grid th, .grid td {{ border:1px solid #ccc; padding:8px; font-size:12px; }}
  .grid th {{ background:#f4f7ff; text-align:left; }}
  .kv {{ width:100%; margin-top:8px; }}
  .kv td {{ padding:4px 2px; font-size:12px; }}
  .right {{ text-align:right; }}
  .center {{ text-align:center; }}
  .foot {{ margin-top:28px; font-size:11px; color:#666; }}
</style>
</head>
<body>
  <div class='title'>CERTIFICADO DE ANÁLISE</div>
  <div class='sub'>Sistema de Controle da Qualidade · Inspeção em Linha</div>

  <table class='kv'>
    <tr><td><b>Nº Laudo:</b> {row.laudo}</td><td class='right'><b>Emissão:</b> {row.emissao}</td></tr>
    <tr><td><b>Código:</b> {row.codigo}</td><td class='right'><b>Cliente:</b> {row.cliente}</td></tr>
    <tr><td><b>Nota Fiscal:</b> {row.nota}</td><td class='right'><b>Lote:</b> {row.lote}</td></tr>
    <tr><td colspan='2'><b>Quantidade:</b> {row.qte}</td></tr>
  </table>

  <table class='grid'>
    <tr><th>Parâmetro</th><th>Resultado</th><th>Especificação</th><th>Método</th></tr>
    <tr><td>Conformidade</td><td class='center'>ATENDE</td><td>Conforme Plano de Controle</td><td>Procedimento interno</td></tr>
  </table>

  <div class='foot'>
    Este certificado foi gerado eletronicamente. Válido sem assinatura. — {row.cliente} | Lote {row.lote}
  </div>
</body>
</html>
"""

    def _salvar_pdf(self):
        row = self._linha_selecionada()
        if not row:
            return
        out, _ = QFileDialog.getSaveFileName(self, "Salvar certificado em PDF", f"certificado_{row.laudo}.pdf", "PDF (*.pdf)")
        if not out:
            return
        html = self._cert_html(row)
        doc = QTextDocument()
        doc.setHtml(html)

        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setPaperSize(QPageSize(QPageSize.PageSizeId.A4))
        printer.setOutputFileName(out)

        doc.print(printer)
        QMessageBox.information(self, "PDF", f"Certificado salvo em:\n{out}")

    def _imprimir(self):
        row = self._linha_selecionada()
        if not row:
            return
        html = self._cert_html(row)
        doc = QTextDocument(); doc.setHtml(html)

        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setPaperSize(QPageSize(QPageSize.PageSizeId.A4))

        dlg = QPrintDialog(printer, self)
        if dlg.exec():
            doc.print(printer)
            QMessageBox.information(self, "Impressão", "Certificado enviado à impressora." )
