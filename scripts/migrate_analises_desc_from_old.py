# scripts/migrate_analises_desc_from_old.py
import sqlite3
try:
    from app.config import DB_PATH
except Exception:
    DB_PATH = "app/data/qualidade.db"

SQL = """
UPDATE analises
SET
  descricao_pt = COALESCE(NULLIF(descricao_pt, ''), descricao_portugues),
  descricao_en = COALESCE(NULLIF(descricao_en, ''), descricao_ingles),
  descricao_es = COALESCE(NULLIF(descricao_es, ''), descricao_espanhol)
WHERE
  (descricao_portugues IS NOT NULL AND TRIM(descricao_portugues) <> '')
  OR (descricao_ingles IS NOT NULL AND TRIM(descricao_ingles) <> '')
  OR (descricao_espanhol IS NOT NULL AND TRIM(descricao_espanhol) <> '');
"""

def main():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute(SQL)
    con.commit()
    con.close()
    print("Migração concluída.")

if __name__ == "__main__":
    main()
