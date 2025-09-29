# scripts/fix_analises_schema.py
import sqlite3, sys
try:
    from app.config import DB_PATH
except Exception:
    # ajuste se precisar apontar o caminho manualmente
    DB_PATH = "app/data/qualidade.db"

def get_cols(cur, table):
    return [r[1] for r in cur.execute(f"PRAGMA table_info({table})")]

def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cols = get_cols(cur, "analises")
    print("DB_PATH:", DB_PATH)
    print("analises ->", cols)

    # colunas esperadas
    expected = [
        "descricao_pt", "descricao_en", "descricao_es",
        "metodo", "tipo", "frequencia", "medicao"
    ]

    changed = False
    for col in expected:
        if col not in cols:
            cur.execute(f"ALTER TABLE analises ADD COLUMN {col} TEXT")
            changed = True

    # se existir coluna antiga 'descricao', copia para descricao_pt
    if "descricao" in cols:
        cur.execute("""
            UPDATE analises
               SET descricao_pt = COALESCE(descricao_pt, descricao)
             WHERE descricao IS NOT NULL
               AND (descricao_pt IS NULL OR descricao_pt = '')
        """)
        changed = True

    conn.commit()
    print("Alterações aplicadas:", changed)
    print("analises ->", get_cols(cur, "analises"))
    conn.close()

if __name__ == "__main__":
    main()
