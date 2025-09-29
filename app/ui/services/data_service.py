from typing import Any, Dict, List, Optional, Tuple
from ..core.app_context import AppContext
from ..core.event_bus import EventBus
from ...data.db import Database

class DataService:
    """
    Camada única de leitura. Tenta várias consultas (fallback) para acomodar
    diferenças de nomes de coluna/tabela sem quebrar a UI.
    """
    def __init__(self, db: Database, ctx: AppContext, bus: EventBus):
        self.db = db
        self.ctx = ctx
        self.bus = bus

    # ---------- helpers ----------
    def _select(self, sql: str, params: Tuple = ()) -> List[Tuple]:
        cur = self.db.conn.cursor()
        cur.execute(sql, params)
        return cur.fetchall()

    def _try_select1(self, queries: List[str], params: Tuple = (), col: int = 0) -> List[Any]:
        cur = self.db.conn.cursor()
        for q in queries:
            try:
                cur.execute(q, params)
                return [r[col] for r in cur.fetchall()]
            except Exception:
                continue
        return []

    def _try_row(self, queries: List[str], params: Tuple = ()) -> Optional[Tuple]:
        cur = self.db.conn.cursor()
        for q in queries:
            try:
                cur.execute(q, params)
                r = cur.fetchone()
                if r: return r
            except Exception:
                continue
        return None

    # ---------- produtos / clientes ----------
    def list_products(self) -> List[str]:
        return self._try_select1([
            "SELECT descricao FROM produtos ORDER BY 1",
            "SELECT descricao_pt FROM produtos ORDER BY 1",
            "SELECT nome FROM produtos ORDER BY 1",
        ])

    def list_clients(self) -> List[str]:
        return self._try_select1([
            "SELECT nome FROM clientes ORDER BY 1",
            "SELECT razao_social FROM clientes ORDER BY 1",
        ])

    def find_product_id(self, any_text: str) -> Optional[str]:
        row = self._try_row([
            "SELECT id FROM produtos WHERE descricao=? COLLATE NOCASE",
            "SELECT id FROM produtos WHERE descricao_pt=? COLLATE NOCASE",
            "SELECT id FROM produtos WHERE codigo=?",
        ], (any_text,))
        return str(row[0]) if row else None

    def find_client_id(self, any_text: str) -> Optional[str]:
        row = self._try_row([
            "SELECT id FROM clientes WHERE nome=? COLLATE NOCASE",
            "SELECT id FROM clientes WHERE codigo=?",
        ], (any_text,))
        return str(row[0]) if row else None

    def list_lots(self) -> List[str]:
        return self._try_select1([
            "SELECT DISTINCT lote FROM inspecoes ORDER BY 1 DESC",
            "SELECT DISTINCT lote FROM certificados ORDER BY 1 DESC",
        ])

    # ---------- inspeções ----------
    def search_inspections(self,
                           product_id: Optional[str] = None,
                           client_id: Optional[str] = None,
                           lote: Optional[str] = None,
                           date_ini: Optional[str] = None,
                           date_fim: Optional[str] = None) -> List[Dict[str, Any]]:
        cur = self.db.conn.cursor()
        sql = "SELECT * FROM inspecoes WHERE 1=1"
        params: List[Any] = []
        if product_id: sql += " AND produto_id=?"; params.append(product_id)
        if client_id:  sql += " AND cliente_id=?"; params.append(client_id)
        if lote:       sql += " AND lote=?";       params.append(lote)
        if date_ini:   sql += " AND date(data_emissao) >= date(?)"; params.append(date_ini)
        if date_fim:   sql += " AND date(data_emissao) <= date(?)"; params.append(date_fim)

        try:
            cur.execute(sql, tuple(params))
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, r)) for r in cur.fetchall()]
        except Exception:
            # fallback “genérico” (caso a tabela tenha nomes diferentes)
            try:
                cur.execute("SELECT id, produto_id, cliente_id, lote, nota, quantidade, data_emissao FROM inspecoes")
                cols = [d[0] for d in cur.description]
                return [dict(zip(cols, r)) for r in cur.fetchall()]
            except Exception:
                return []

    # ---------- certificados ----------
    def search_certificates(self,
                            codigo: Optional[str] = None,
                            cliente: Optional[str] = None,
                            nf: Optional[str] = None,
                            lote: Optional[str] = None) -> List[Dict[str, Any]]:
        cur = self.db.conn.cursor()
        base = "SELECT id, num_laudo, emissao, codigo, cliente, nota, lote, quantidade, produto_id FROM certificados WHERE 1=1"
        params: List[Any] = []
        sql = base
        if codigo:  sql += " AND codigo LIKE ?";  params.append(f"%{codigo}%")
        if cliente: sql += " AND cliente LIKE ?"; params.append(f"%{cliente}%")
        if nf:      sql += " AND nota LIKE ?";    params.append(f"%{nf}%")
        if lote:    sql += " AND lote LIKE ?";    params.append(f"%{lote}%")

        try:
            cur.execute(sql, tuple(params))
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, r)) for r in cur.fetchall()]
        except Exception:
            # Fallback com nomes alternativos
            try:
                cur.execute("SELECT id, laudo as num_laudo, emissao, codigo, cliente, nota, lote, qtd as quantidade, produto_id FROM certificados")
                cols = [d[0] for d in cur.description]
                rows = [dict(zip(cols, r)) for r in cur.fetchall()]
                # filtros em memória se necessário
                def ok(row: Dict[str, Any]) -> bool:
                    def like(field, value):
                        return (value is None) or (value.lower() in str(row.get(field,"")).lower())
                    return all([
                        like("codigo", codigo),
                        like("cliente", cliente),
                        like("nota", nf),
                        like("lote", lote),
                    ])
                return [r for r in rows if ok(r)]
            except Exception:
                return []

    def certificate_payload_from_product_lot(self, product_id: str, lote: str) -> Dict[str, Any]:
        # Produto
        prod = self._try_row([
            "SELECT descricao FROM produtos WHERE id=?",
            "SELECT descricao_pt FROM produtos WHERE id=?",
            "SELECT nome FROM produtos WHERE id=?",
        ], (product_id,))
        produto_desc = (prod[0] if prod else str(product_id))

        # Cliente (última inspeção do lote)
        client = self._try_row([
            "SELECT c.nome FROM inspecoes i LEFT JOIN clientes c ON c.id=i.cliente_id WHERE i.produto_id=? AND i.lote=? ORDER BY i.data_emissao DESC LIMIT 1",
            "SELECT cliente FROM certificados WHERE produto_id=? AND lote=? ORDER BY emissao DESC LIMIT 1",
        ], (product_id, lote))
        cliente_nome = client[0] if client else ""

        # Linhas de análise (se existirem)
        linhas: List[Dict[str, Any]] = []
        cur = self.db.conn.cursor()
        tried = False
        try:
            tried = True
            cur.execute("""
                SELECT a.descricao_pt, r.metodo, r.minimo, r.maximo, r.especificacao
                  FROM resultados r
                  LEFT JOIN analises a ON a.id=r.analise_id
                 WHERE r.produto_id=? AND r.lote=?
                 ORDER BY a.descricao_pt
            """, (product_id, lote))
            for analise, metodo, minimo, maximo, spec in cur.fetchall():
                linhas.append({
                    "analise": analise, "metodo": metodo,
                    "min": minimo, "max": maximo, "spec": spec
                })
        except Exception:
            if not tried:
                pass  # ignora

        return {
            "produto_id": product_id,
            "produto_desc": produto_desc,
            "cliente": cliente_nome,
            "lote": lote,
            "linhas": linhas,
        }
