# scripts/setup_tipos_acesso.py
# Cria TBL_TipoAcesso com as mesmas permissões da tela do Access

from pathlib import Path
import sqlite3

DB = Path("qualidade.db")
if not DB.exists():
    raise SystemExit("qualidade.db não encontrado na pasta do projeto.")

con = sqlite3.connect(DB)
cur = con.cursor()

def table_exists(name: str) -> bool:
    cur.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND lower(name)=lower(?)", (name,))
    return cur.fetchone() is not None

def col_exists(tbl: str, col: str) -> bool:
    cur.execute(f"PRAGMA table_info('{tbl}')")
    return any(r[1] == col for r in cur.fetchall())

cols = [
    ("CadastrarFuncionarios", "INTEGER"),
    ("DefinirAcessos", "INTEGER"),
    ("CadastrarClientes", "INTEGER"),
    ("CadastrarRegistros", "INTEGER"),
    ("CadastrarAnalises", "INTEGER"),
    ("CadastrarProdutos", "INTEGER"),
    ("CadastrarFabrica", "INTEGER"),
    ("AtualizarDados", "INTEGER"),
    ("CadastrarAnalisePorProduto", "INTEGER"),
    ("CadastrarAnalisePorCliente", "INTEGER"),
    ("ImprimirRotulos", "INTEGER"),
    ("InserirResultadosAnalises", "INTEGER"),
    ("EmitirCertificados", "INTEGER"),
    ("ImprimirCertificados", "INTEGER"),
    ("ConsultasGerais", "INTEGER"),
    ("LiberacaoEspecial", "INTEGER"),
]

# cria ou ajusta a tabela
if not table_exists("TBL_TipoAcesso"):
    defs = ", ".join([f'"{c}" {t} DEFAULT 0' for c, t in cols])
    cur.execute(f'''
        CREATE TABLE "TBL_TipoAcesso" (
            "id" INTEGER PRIMARY KEY AUTOINCREMENT,
            "nome" TEXT UNIQUE,
            {defs}
        )
    ''')
else:
    for c, t in cols:
        if not col_exists("TBL_TipoAcesso", c):
            cur.execute(f'ALTER TABLE "TBL_TipoAcesso" ADD COLUMN "{c}" {t} DEFAULT 0')

# popula um perfil Administrador com tudo marcado, se não existir
row = cur.execute('SELECT 1 FROM TBL_TipoAcesso WHERE lower(nome)=lower("Administrador")').fetchone()
if not row:
    col_names = ", ".join([c for c, _ in cols])
    qmarks = ", ".join(["?"] * len(cols))
    cur.execute(
        f'INSERT INTO TBL_TipoAcesso (nome, {col_names}) VALUES (?, {qmarks})',
        ["Administrador"] + [1] * len(cols)
    )

con.commit()
con.close()
print("TBL_TipoAcesso criada e pronta.")
