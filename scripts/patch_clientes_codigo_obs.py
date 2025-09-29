# scripts/patch_clientes_codigo_obs.py
import sqlite3, sys
DB = "qualidade.db"

def has_col(cur, table, col):
    cur.execute(f"PRAGMA table_info({table})")
    return any(r[1].lower()==col.lower() for r in cur.fetchall())

con = sqlite3.connect(DB)
cur = con.cursor()
cur.execute("PRAGMA foreign_keys=off")

# Garante colunas 'codigo' e 'observacao'
if not has_col(cur, "clientes", "codigo"):
    cur.execute("ALTER TABLE clientes ADD COLUMN codigo TEXT")
if not has_col(cur, "clientes", "observacao"):
    cur.execute("ALTER TABLE clientes ADD COLUMN observacao TEXT")

# Se existir coluna antiga 'cnpj', aproveita para popular 'codigo' quando vazio
cols = [r[1].lower() for r in cur.execute("PRAGMA table_info(clientes)").fetchall()]
if "cnpj" in cols:
    cur.execute("""
        UPDATE clientes
           SET codigo = CASE
                          WHEN codigo IS NULL OR TRIM(codigo)=''
                          THEN cnpj
                          ELSE codigo
                        END
    """)

con.commit()
con.close()
print("Patch OK: clientes -> (codigo TEXT, observacao TEXT).")
