# scripts/fix_acessos_simple.py
# Deixa a aba Acessos funcionando sem mexer em layout e sem criar views.

from pathlib import Path
import sqlite3

DB = Path("qualidade.db")
if not DB.exists():
    raise SystemExit("qualidade.db não encontrado.")

con = sqlite3.connect(DB)
cur = con.cursor()

def table_exists(name: str) -> bool:
    cur.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND lower(name)=lower(?)", (name,))
    return cur.fetchone() is not None

def ensure_cols(tbl: str):
    def col_exists(col: str) -> bool:
        cur.execute(f"PRAGMA table_info('{tbl}')")
        return any(r[1] == col for r in cur.fetchall())
    if not col_exists("id"):
        cur.execute(f'ALTER TABLE "{tbl}" ADD COLUMN id INTEGER')
    if not col_exists("usuario_id"):
        cur.execute(f'ALTER TABLE "{tbl}" ADD COLUMN usuario_id INTEGER')
    if not col_exists("papel"):
        cur.execute(f'ALTER TABLE "{tbl}" ADD COLUMN papel TEXT')
    if not col_exists("ativo"):
        cur.execute(f'ALTER TABLE "{tbl}" ADD COLUMN ativo INTEGER DEFAULT 1')

# 1. Descobrir qual nome de tabela a sua tela está usando
candidatos = ["acessos", "Acessos", "TBL_Acessos", "tblAcessos"]
tabela = next((n for n in candidatos if table_exists(n)), None)

# 2. Se não existir nenhuma, cria "Acessos"
if tabela is None:
    tabela = "Acessos"
    cur.execute(f"""
        CREATE TABLE "{tabela}"(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER UNIQUE,
            papel TEXT,
            ativo INTEGER DEFAULT 1
        )
    """)
else:
    # garante as colunas esperadas
    ensure_cols(tabela)
    # tenta definir PRIMARY KEY se não houver
    try:
        # cria uma PK leve usando rowid, apenas se não existir PK
        cur.execute(f"CREATE UNIQUE INDEX IF NOT EXISTS idx_{tabela}_usuario ON \"{tabela}\"(usuario_id)")
    except Exception:
        pass

# 3. Popular se estiver vazio
total = cur.execute(f'SELECT COUNT(*) FROM "{tabela}"').fetchone()[0]
if total == 0:
    # tenta puxar lista de funcionários, se existir
    fontes = ["TBL_Funcionario", "funcionarios", "Funcionarios", "usuarios", "Usuarios"]
    fonte = next((n for n in fontes if table_exists(n)), None)
    if fonte:
        # tentar adivinhar colunas de id e nome
        cols = [c[1] for c in cur.execute(f"PRAGMA table_info('{fonte}')")]
        col_id = next((c for c in ["id", "ID", "ID_FUNC", "codigo", "cod"] if c in cols), None)
        col_nome = next((c for c in ["nome", "NOME", "funcionario", "Funcionario", "user_name"] if c in cols), None)
        if col_id and col_nome:
            for uid, nome in cur.execute(f'SELECT "{col_id}", "{col_nome}" FROM "{fonte}"'):
                papel = "Administrador" if str(nome or "").strip().lower().startswith("admin") else "Usuário"
                cur.execute(f'INSERT OR IGNORE INTO "{tabela}"(usuario_id, papel, ativo) VALUES (?,?,1)', (uid, papel))
    # se mesmo assim continuar vazio, cria um registro padrão
    total = cur.execute(f'SELECT COUNT(*) FROM "{tabela}"').fetchone()[0]
    if total == 0:
        cur.execute(f'INSERT INTO "{tabela}"(usuario_id, papel, ativo) VALUES (1, "Administrador", 1)')

con.commit()
# diagnóstico
dados = cur.execute(f'SELECT * FROM "{tabela}" LIMIT 10').fetchall()
con.close()
print(f'Tabela usada: {tabela}')
print('Exemplo de linhas:', dados)
