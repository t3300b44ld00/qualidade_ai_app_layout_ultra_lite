from pathlib import Path
import sqlite3

db_path = Path("qualidade.db")
if not db_path.exists():
    raise SystemExit("qualidade.db não encontrado na pasta do projeto.")

con = sqlite3.connect(str(db_path))
cur = con.cursor()
cur.execute("PRAGMA foreign_keys=ON;")

def col_exists(table, col):
    cur.execute(f"PRAGMA table_info('{table}')")
    return any(r[1] == col for r in cur.fetchall())

def ensure_col(table, col, decl):
    if not col_exists(table, col):
        cur.execute(f'ALTER TABLE "{table}" ADD COLUMN "{col}" {decl}')

def tbl_exists(name):
    cur.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND lower(name)=lower(?)", (name,))
    return cur.fetchone() is not None

# garantir tabelas mínimas
if not tbl_exists("clientes"):
    cur.execute("""CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")

if not tbl_exists("produtos"):
    cur.execute("""CREATE TABLE IF NOT EXISTS produtos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        codigo TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")

# clientes, colunas esperadas
ensure_col("clientes", "codigo", "TEXT")
ensure_col("clientes", "observacao", "TEXT")

# produtos, colunas usadas pela UI
ensure_col("produtos", "cliente_id", "INTEGER")
ensure_col("produtos", "grupo_id", "INTEGER")
ensure_col("produtos", "produto_id", "INTEGER")

# espelhar id em produto_id quando estiver nulo
cur.execute("UPDATE produtos SET produto_id = id WHERE produto_id IS NULL")

con.commit()
con.close()
print("Patch OK no SQLite.")
