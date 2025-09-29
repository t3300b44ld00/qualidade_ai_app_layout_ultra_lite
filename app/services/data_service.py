
# -*- coding: utf-8 -*-
import csv
import sqlite3
from typing import Iterable, List, Dict, Any, Optional

class DataService:
    """Serviço de dados de alto nível sobre o SQLite já utilizado pelo app."""
    def __init__(self, db) -> None:
        # espera objeto Database do projeto (com atributo .conn = sqlite3.Connection)
        self.db = db
        self.conn: sqlite3.Connection = db.conn
        self.ensure_schema()

    # ---------- schema ----------
    def ensure_schema(self) -> None:
        cur = self.conn.cursor()
        # Tabela específica para as consultas da tela "Impressão de Certificados"
        cur.execute(
            """CREATE TABLE IF NOT EXISTS cert_consulta (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    laudo TEXT,
                    emissao TEXT,
                    codigo TEXT,
                    cliente TEXT,
                    nota TEXT,
                    lote TEXT,
                    qte REAL
            )"""
        )
        self.conn.commit()

    # ---------- consultas ----------
    def search_impressao(self,
                         codigo: Optional[str] = None,
                         cliente: Optional[str] = None,
                         nfiscal: Optional[str] = None,
                         lote: Optional[str] = None) -> List[Dict[str, Any]]:
        sql = "SELECT laudo, emissao, codigo, cliente, nota, lote, qte FROM cert_consulta WHERE 1=1"
        params: List[Any] = []
        if codigo:
            sql += " AND codigo LIKE ?"
            params.append(f"%{codigo}%")
        if cliente:
            sql += " AND cliente LIKE ?"
            params.append(f"%{cliente}%")
        if nfiscal:
            sql += " AND nota LIKE ?"
            params.append(f"%{nfiscal}%")
        if lote:
            sql += " AND lote LIKE ?"
            params.append(f"%{lote}%")
        sql += " ORDER BY CAST(laudo AS TEXT) DESC"
        cur = self.conn.cursor()
        cur.execute(sql, params)
        cols = [c[0] for c in cur.description]
        out = [dict(zip(cols, r)) for r in cur.fetchall()]
        return out

    # ---------- importações ----------
    # Aceita CSV com cabeçalhos equivalentes: Nº Laudo/Laudo, Emissão/Emissao, Código/Codigo, Cliente,
    # Nota/Nota Fiscal/N Fiscal, Lote, QTE/Qtd/Quantidade
    def bulk_import_csv_for_impressao(self, csv_path: str) -> int:
        def norm(s: str) -> str:
            return (s or '').strip().lower().replace('º', '').replace('  ', ' ')
        header_map = {
            'n laudo': 'laudo', 'nº laudo': 'laudo', 'laudo': 'laudo',
            'emissão': 'emissao', 'emissao': 'emissao',
            'código': 'codigo', 'codigo': 'codigo',
            'cliente': 'cliente',
            'nota': 'nota', 'nota fiscal': 'nota', 'n fiscal': 'nota',
            'lote': 'lote',
            'qte': 'qte', 'qtd': 'qte', 'quantidade': 'qte'
        }
        inserted = 0
        with open(csv_path, 'r', encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f)
            cols = [header_map.get(norm(c), None) for c in reader.fieldnames]
            # Verifica se temos pelo menos laudo/codigo/cliente/nota/lote
            if 'laudo' not in cols or 'codigo' not in cols or 'cliente' not in cols:
                # tenta latin-1 se utf-8 falhar ou cabeçalhos vierem em outro encoding
                f.seek(0); txt = f.read()
                try:
                    txt = txt.encode('latin-1').decode('utf-8', errors='ignore')
                except Exception:
                    pass
                import io, csv as _csv
                reader = _csv.DictReader(io.StringIO(txt))
                cols = [header_map.get(norm(c), None) for c in reader.fieldnames]
            # Mapeia linhas
            cur = self.conn.cursor()
            for row in reader:
                rec = { 'laudo':'', 'emissao':'', 'codigo':'', 'cliente':'', 'nota':'', 'lote':'', 'qte':None }
                for k_src, v in row.items():
                    k = header_map.get(norm(k_src))
                    if not k: 
                        continue
                    rec[k] = (v or '').strip()
                # insere (simples) – se já existir mesmo laudo + lote, atualiza
                cur.execute("SELECT id FROM cert_consulta WHERE laudo=? AND lote=?", (rec['laudo'], rec['lote']))
                hit = cur.fetchone()
                if hit:
                    cur.execute("""UPDATE cert_consulta
                                   SET emissao=?, codigo=?, cliente=?, nota=?, qte=?
                                 WHERE id=?""",
                                (rec['emissao'], rec['codigo'], rec['cliente'], rec['nota'], rec['qte'], hit[0]))
                else:
                    cur.execute("""INSERT INTO cert_consulta
                                  (laudo, emissao, codigo, cliente, nota, lote, qte)
                                  VALUES (?,?,?,?,?,?,?)""",
                                (rec['laudo'], rec['emissao'], rec['codigo'], rec['cliente'], rec['nota'], rec['lote'], rec['qte']))
                    inserted += 1
            self.conn.commit()
        return inserted
