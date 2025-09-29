# scripts/setup_acessos_tables.py
# Cria a TBL_Acessos no SQLite espelhando as permissões da sua tela.
# Não altera nenhuma tela. Não muda layout.

from pathlib import Path
import sqlite3

DB = Path("qualidade.db")
if not DB.exists():
    raise SystemExit("qualidade.db não encontrado. Gere a partir do Access antes.")

con = sqlite3.connect(DB)
cur = con.cursor()

def table_exists(name: str) -> bool:
    cur.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND lower(name)=lower(?)", (name,))
    return cur.fetchone() is not None

def col_exists(table: str, col: str) -> bool:
    cur.execute(f"PRAGMA table_info('{table}')")
    return any(r[1] == col for r in cur.fetchall())

# Tabela alvo. Uma linha por funcionário.
# Colunas booleanas como INTEGER 0 ou 1.
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

# 1. Cria TBL_Acessos se não existir.
if not table_exists("TBL_Acessos"):
    defs = ", ".join([f'"{c}" {t} DEFAULT 0' for c, t in cols])
    cur.execute(f'''
        CREATE TABLE "TBL_Acessos" (
            "id" INTEGER PRIMARY KEY AUTOINCREMENT,
            "funcionario_id" INTEGER UNIQUE,
            {defs}
        )
    ''')

# 2. Garante colunas caso a tabela já exista, sem quebrar dados antigos.
for c, t in cols:
    if not col_exists("TBL_Acessos", c):
        cur.execute(f'ALTER TABLE "TBL_Acessos" ADD COLUMN "{c}" {t} DEFAULT 0')

# 3. Se existir TBL_Funcionario e um registro "Administrador",
#    cria a linha de acessos com tudo ligado caso ainda não exista.
admin_id = None
if table_exists("TBL_Funcionario"):
    row = cur.execute(
        "SELECT id FROM TBL_Funcionario WHERE lower(nome)=lower('Administrador') LIMIT 1"
    ).fetchone()
    if row:
        admin_id = row[0]

if admin_id is not None:
    exists = cur.execute(
        'SELECT 1 FROM TBL_Acessos WHERE funcionario_id=?', (admin_id,)
    ).fetchone()
    if not exists:
        col_names = ", ".join([c for c, _ in cols])
        qmarks = ", ".join(["?"] * len(cols))
        values = [1] * len(cols)  # tudo ligado
        cur.execute(
            f'INSERT INTO TBL_Acessos (funcionario_id, {col_names}) VALUES (?, {qmarks})',
            [admin_id, *values]
        )

con.commit()
con.close()
print("TBL_Acessos criada e alinhada às permissões da tela. Layout preservado.")
