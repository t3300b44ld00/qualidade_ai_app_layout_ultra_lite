from typing import Dict
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from PyQt6.QtGui import QTextDocument

class CertificateService:
    def render_html(self, payload: Dict) -> str:
        rows = payload.get("linhas", []) or []
        body_rows = []
        for l in rows:
            body_rows.append(
                "<tr>"
                f"<td>{l.get('analise','')}</td>"
                f"<td>{l.get('metodo','')}</td>"
                f"<td style='text-align:center'>{l.get('min','')}</td>"
                f"<td style='text-align:center'>{l.get('max','')}</td>"
                f"<td style='text-align:center'>{'✔' if l.get('spec') else '—'}</td>"
                "</tr>"
            )
        tbody = "".join(body_rows) if body_rows else "<tr><td colspan='5' style='text-align:center;color:#999'>Sem dados</td></tr>"
        html = (
            "<html><head><meta charset='utf-8'/>"
            "<style>body{font-family:Arial,Helvetica,sans-serif;font-size:11pt}"
            "h1{margin:0 0 6px 0;font-size:16pt}.muted{color:#666}"
            "table{border-collapse:collapse;width:100%}"
            "th,td{border:1px solid #ddd;padding:6px}"
            "th{background:#f4f5f7;text-align:left}</style>"
            "</head><body>"
            "<h1>Certificado de Qualidade</h1>"
            f"<div class='muted'>Cliente: <b>{payload.get('cliente','')}</b></div>"
            f"<div class='muted'>Produto: <b>{payload.get('produto_desc','')}</b></div>"
            f"<div class='muted'>Lote: <b>{payload.get('lote','')}</b></div><br/>"
            "<table><thead><tr>"
            "<th>Análises Básicas</th><th>Método</th><th>Mínimo</th><th>Máximo</th><th>Especificação</th>"
            "</tr></thead><tbody>"
            f"{tbody}</tbody></table></body></html>"
        )
        return html

    def print_html(self, html: str, title: str = "Certificado"):
        doc = QTextDocument()
        doc.setHtml(html)
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setDocName(title)
        dlg = QPrintDialog(printer)
        if dlg.exec():
            doc.print(printer)

    def save_pdf(self, html: str, filepath: str):
        if not filepath.lower().endswith(".pdf"):
            filepath = filepath + ".pdf"
        doc = QTextDocument()
        doc.setHtml(html)
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(filepath)
        doc.print(printer)
