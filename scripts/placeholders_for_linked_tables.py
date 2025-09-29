# scripts/placeholders_for_linked_tables.py
from pathlib import Path
import sqlite3

DB = Path("qualidade.db")
if not DB.exists():
    raise SystemExit("qualidade.db não encontrado. Rode a migração do que for possível antes.")

con = sqlite3.connect(DB)
cur = con.cursor()

def ensure_table(name: str, cols: list[tuple[str, str]]):
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,))
    if cur.fetchone():
        return
    defs = ", ".join([f'"{c}" {t}' for c, t in cols])
    cur.execute(f'CREATE TABLE "{name}" ({defs});')

# Placeholders para as tabelas que falharam por dependerem do back-end
# Colunas são mínimas, servem para o app abrir e para testes de interface

common_audit = [("created_at", "TEXT")]

# Cadastros
ensure_table("TBL_Cliente", [("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
                             ("nome", "TEXT"),
                             ("codigo", "TEXT"),
                             ("observacao", "TEXT")] + common_audit)

ensure_table("TBL_Produto", [("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
                             ("nome", "TEXT"),
                             ("codigo", "TEXT"),
                             ("cliente_id", "INTEGER"),
                             ("grupo_id", "INTEGER"),
                             ("produto_id", "INTEGER")] + common_audit)

ensure_table("TBL_Funcionario", [("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
                                 ("nome", "TEXT"),
                                 ("login", "TEXT"),
                                 ("senha", "TEXT"),
                                 ("papel", "TEXT")] + common_audit)

ensure_table("TBL_Planta", [("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
                            ("nome", "TEXT")] + common_audit)

ensure_table("TBL_Segmento", [("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
                              ("nome", "TEXT")] + common_audit)

# Acessos e segurança
ensure_table("TBL_Acessos", [("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
                              ("funcionario_id", "INTEGER"),
                              ("tela", "TEXT"),
                              ("permite", "INTEGER")] + common_audit)

# Tabelas de especificação, ensaio e resultados
ensure_table("TBL_Analise", [("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
                             ("produto_id", "INTEGER"),
                             ("descricao", "TEXT")] + common_audit)

ensure_table("TBL_AnaliseProduto", [("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
                                    ("produto_id", "INTEGER"),
                                    ("analise_id", "INTEGER"),
                                    ("valor", "TEXT")] + common_audit)

ensure_table("TBL_Ensaio", [("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
                            ("nome", "TEXT"),
                            ("unidade", "TEXT")] + common_audit)

ensure_table("TBL_EnsaioCliente", [("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
                                   ("cliente_id", "INTEGER"),
                                   ("ensaio_id", "INTEGER"),
                                   ("tolerancia", "TEXT")] + common_audit)

ensure_table("TBL_EnsaioNumber", [("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
                                  ("resultado_id", "INTEGER"),
                                  ("valor", "REAL")] + common_audit)

ensure_table("TBL_EnsaioText", [("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
                                ("resultado_id", "INTEGER"),
                                ("valor", "TEXT")] + common_audit)

ensure_table("TBL_Resultado", [("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
                               ("produto_id", "INTEGER"),
                               ("lote", "TEXT"),
                               ("status", "TEXT")] + common_audit)

# Certificados e descrição
ensure_table("TBL_Certificado", [("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
                                 ("resultado_id", "INTEGER"),
                                 ("codigo", "TEXT")] + common_audit)

ensure_table("TBL_Descricao", [("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
                               ("texto", "TEXT")] + common_audit)

# Outras vistas, tabelas auxiliares e contadores
ensure_table("TBL_Contador", [("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
                              ("chave", "TEXT"),
                              ("valor", "INTEGER")] + common_audit)

ensure_table("TBL_Cores", [("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
                           ("nome", "TEXT")] + common_audit)

ensure_table("TBL_Teste", [("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
                           ("nome", "TEXT")] + common_audit)

ensure_table("TBL_TesteQualidade", [("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
                                    ("produto_id", "INTEGER"),
                                    ("resultado_id", "INTEGER")] + common_audit)

ensure_table("TBL_UnidadeEmbarque", [("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
                                     ("descricao", "TEXT")] + common_audit)

ensure_table("tblBasico", [("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
                           ("chave", "TEXT"),
                           ("valor", "TEXT")] + common_audit)

ensure_table("tblFrequencia", [("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
                               ("descricao", "TEXT")] + common_audit)

ensure_table("tblMedicao", [("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
                            ("resultado_id", "INTEGER"),
                            ("valor", "REAL")] + common_audit)

ensure_table("tblTabelas", [("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
                            ("nome", "TEXT")] + common_audit)

# As duas que você citou antes
ensure_table("cstEspecificacao", [("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
                                  ("produto_id", "INTEGER"),
                                  ("descricao", "TEXT")] + common_audit)

ensure_table("cstLoteRetem", [("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
                              ("produto_id", "INTEGER"),
                              ("motivo", "TEXT")] + common_audit)

con.commit()
con.close()
print("Placeholders criados, se não existiam.")
