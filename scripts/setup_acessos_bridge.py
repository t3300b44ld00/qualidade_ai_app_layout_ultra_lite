# scripts/setup_acessos_bridge.py
# Deixa o SQLite compatível com a aba Acessos sem alterar a UI.

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

def first_existing_table(candidates: list[str]) -> str | None:
    for n in candidates:
        if table_exists(n):
            return n
    return None

# 1) Tabela base utilizada internamente
cur.execute("""
CREATE TABLE IF NOT EXISTS Acessos(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER UNIQUE,
    papel TEXT,
    ativo INTEGER DEFAULT 1
)
""")

# 2) Popular a partir da tabela de funcionários que existir
fonte_func = first_existing_table(["TBL_Funcionario", "funcionarios", "Usuarios", "usuarios"])
if fonte_func:
    # tenta achar colunas de id e nome com nomes mais comuns
    cols = [c[1] for c in cur.execute(f"PRAGMA table_info('{fonte_func}')")]
    cand_id = next((c for c in ["id", "ID_FUNC", "ID", "codigo", "cod"] if c in cols), None)
    cand_nome = next((c for c in ["nome", "NOME", "funcionario", "Funcionario", "user_name"] if c in cols), None)
    if cand_id and cand_nome:
        linhas = cur.execute(f'SELECT "{cand_id}", "{cand_nome}" FROM "{fonte_func}"').fetchall()
        for uid, nome in linhas:
            papel = "Administrador" if str(nome or "").strip().lower().startswith("admin") else "Usuário"
            cur.execute(
                "INSERT OR IGNORE INTO Acessos(usuario_id, papel, ativo) VALUES(?,?,1)",
                (uid, papel),
            )

# 3) Criar views espelho com triggers para atender nomes diferentes que a tela possa usar
def ensure_view_bridge(view_name: str):
    cur.execute(f'CREATE VIEW IF NOT EXISTS "{view_name}" AS SELECT id, usuario_id, papel, ativo FROM Acessos;')
    # INSERT
    cur.execute(f"""
    CREATE TRIGGER IF NOT EXISTS "{view_name}_ins"
    INSTEAD OF INSERT ON "{view_name}"
    BEGIN
      INSERT INTO Acessos(id, usuario_id, papel, ativo)
      VALUES (NEW.id, NEW.usuario_id, NEW.papel, COALESCE(NEW.ativo, 1));
    END;""")
    # UPDATE
    cur.execute(f"""
    CREATE TRIGGER IF NOT EXISTS "{view_name}_upd"
    INSTEAD OF UPDATE ON "{view_name}"
    BEGIN
      UPDATE Acessos
         SET usuario_id=NEW.usuario_id, papel=NEW.papel, ativo=NEW.ativo
       WHERE id=OLD.id;
    END;""")
    # DELETE
    cur.execute(f"""
    CREATE TRIGGER IF NOT EXISTS "{view_name}_del"
    INSTEAD OF DELETE ON "{view_name}"
    BEGIN
      DELETE FROM Acessos WHERE id=OLD.id;
    END;""")

for nome in ["acessos", "Acessos", "TBL_Acessos", "tblAcessos"]:
    ensure_view_bridge(nome)

con.commit()
# diagnóstico rápido
total = cur.execute("SELECT COUNT(*) FROM Acessos").fetchone()[0]
con.close()
print(f"Bridge criado. Registros em Acessos: {total}. Layout preservado.")
