# scripts/setup_acessos_minimal.py
# Alinha o SQLite com a tela Acessos sem mudar layout.

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

# 1) Tabela exatamente como a tela usa
cur.execute("""
CREATE TABLE IF NOT EXISTS Acessos(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER UNIQUE,
    papel TEXT,
    ativo INTEGER DEFAULT 1
)
""")

# 2) Preenche a partir de TBL_Funcionario se existir
if table_exists("TBL_Funcionario"):
    for uid, nome in cur.execute("SELECT id, nome FROM TBL_Funcionario"):
        papel = "Administrador" if (nome or "").strip().lower().startswith("admin") else "Usuário"
        cur.execute(
            "INSERT OR IGNORE INTO Acessos(usuario_id, papel, ativo) VALUES(?,?,1)",
            (uid, papel),
        )

con.commit()
con.close()
print("Tabela Acessos criada e preenchida. Layout preservado.")
