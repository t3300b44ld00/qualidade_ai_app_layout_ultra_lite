from typing import List, Dict, Any, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QComboBox, QFrame, QTableWidget, QTableWidgetItem, QLabel
)
from PyQt6.QtCore import Qt

class ResultadosInspecaoWidget(QWidget):
    def __init__(self, db=None, bus=None, services=None, cert_service=None, parent=None):
        super().__init__(parent)
        self.bus = bus
        self.services = services
        self.cert = cert_service

        root = QVBoxLayout(self)
        root.setContentsMargins(8,8,8,8)
        root.setSpacing(8)

        # filtros simples
        bar = QFrame()
        hb = QHBoxLayout(bar); hb.setContentsMargins(0,0,0,0)
        self.cmb_prod = QComboBox(); self.cmb_prod.setEditable(True); self.cmb_prod.setPlaceholderText("Produto")
        self.cmb_cli  = QComboBox(); self.cmb_cli.setEditable(True); self.cmb_cli.setPlaceholderText("Cliente")
        self.txt_lote = QLineEdit(); self.txt_lote.setPlaceholderText("Lote")
        self.btn_buscar = QPushButton("Buscar")
        self.btn_cert = QPushButton("Certificado do lote")
        for w in (self.cmb_prod, self.cmb_cli, self.txt_lote, self.btn_buscar, self.btn_cert):
            hb.addWidget(w)
        root.addWidget(bar)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(["ID","Produto","Cliente","Lote","Nota","Qtd","Emissão"])
        self.table.horizontalHeader().setStretchLastSection(True)
        root.addWidget(self.table, 1)

        # carregar combos se possível
        if self.services:
            self.cmb_prod.addItems(self.services.list_products())
            self.cmb_cli.addItems(self.services.list_clients())

        # sinais globais
        if self.bus:
            self.bus.productSelected.connect(self._on_product_selected)
            self.bus.clientSelected.connect(self._on_client_selected)

        self.btn_buscar.clicked.connect(self._buscar)
        self.btn_cert.clicked.connect(self._cert)

    def _on_product_selected(self, pid: str):
        self.cmb_prod.setEditText(str(pid))

    def _on_client_selected(self, cid: str):
        self.cmb_cli.setEditText(str(cid))

    def _buscar(self):
        if not self.services: return
        pid = self.services.find_product_id(self.cmb_prod.currentText().strip() or "") if self.cmb_prod.currentText() else None
        cid = self.services.find_client_id(self.cmb_cli.currentText().strip() or "") if self.cmb_cli.currentText() else None
        lote = self.txt_lote.text().strip() or None
        rows = self.services.search_inspections(product_id=pid, client_id=cid, lote=lote)
        self._fill(rows)

    def _fill(self, rows: List[Dict[str, Any]]):
        self.table.setRowCount(0)
        for r in rows:
            i = self.table.rowCount()
            self.table.insertRow(i)
            def put(col, val):
                it = QTableWidgetItem("" if val is None else str(val))
                if col in (0,3,4,5): it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(i, col, it)
            put(0, r.get("id"))
            put(1, r.get("produto_id"))
            put(2, r.get("cliente_id"))
            put(3, r.get("lote"))
            put(4, r.get("nota"))
            put(5, r.get("quantidade"))
            put(6, r.get("data_emissao"))

    def _cert(self):
        if not (self.services and self.cert): return
        # usa primeiro selecionado
        i = self.table.currentRow()
        if i < 0: return
        pid = self.table.item(i,1).text() if self.table.item(i,1) else ""
        lote = self.table.item(i,3).text() if self.table.item(i,3) else ""
        payload = self.services.certificate_payload_from_product_lot(pid, lote)
        html = self.cert.render_html(payload)
        if self.bus:
            self.bus.requestPrint.emit(html, "Certificado")
        else:
            self.cert.print_html(html, "Certificado")
