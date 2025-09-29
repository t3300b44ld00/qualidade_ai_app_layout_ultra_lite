# scripts/fix_clientes_schema.py
import sqlite3
from app.config import DB_PATH

def ensure_column(cur, table, col, decl="TEXT"):
    cur.execute(f"PRAGMA table_info({table})")
    cols = {r[1].lower() for r in cur.fetchall()}
    if col.lower() not in cols:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {col} {decl}")
        return True
    return False

def main():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    changed = False
    changed |= ensure_column(cur, "clientes", "codigo", "TEXT")
    changed |= ensure_column(cur, "clientes", "observacao", "TEXT")
    con.commit()
    cur.execute("PRAGMA table_info(clientes)")
    print("DB_PATH:", DB_PATH)
    print("clientes ->", [r[1] for r in cur.fetchall()])
    print("Alterações aplicadas:", changed)
    con.close()

if __name__ == "__main__":
    main()
