# scripts/relax_analises_parametro.py
import os
import sqlite3

try:
    from app.config import DB_PATH
except Exception:
    DB_PATH = os.path.join("app", "data", "qualidade.db")

def main():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    info = cur.execute("PRAGMA table_info(analises)").fetchall()
    # (cid, name, type, notnull, dflt_value, pk)
    need = False
    for cid, name, coltype, notnull, dflt, pk in info:
        if name == "parametro":
            need = (notnull == 1 and (dflt is None or dflt == "None"))
            break

    if not need:
        print("Nada a fazer: 'parametro' já não bloqueia inserts.")
        con.close()
        return

    cur.execute("BEGIN")

    # renomeia a tabela atual
    cur.execute("ALTER TABLE analises RENAME TO analises_old")

    # recria a tabela, mas com parametro TEXT DEFAULT '' (sem NOT NULL)
    cur.execute("""
        CREATE TABLE analises (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produto_id INTEGER,
            parametro TEXT DEFAULT '',
            limite_min REAL,
            limite_max REAL,
            unidade TEXT,
            codigo TEXT,
            descricao_portugues TEXT,
            descricao_ingles TEXT,
            descricao_espanhol TEXT,
            metodo TEXT,
            tipo TEXT,
            frequencia TEXT,
            medicao TEXT,
            az TEXT,
            descricao_pt TEXT,
            descricao_en TEXT,
            descricao_es TEXT
        )
    """)

    # copia os dados
    cur.execute("""
        INSERT INTO analises(
            id, produto_id, parametro, limite_min, limite_max, unidade, codigo,
            descricao_portugues, descricao_ingles, descricao_espanhol,
            metodo, tipo, frequencia, medicao, az, descricao_pt, descricao_en, descricao_es
        )
        SELECT
            id, produto_id, COALESCE(parametro, ''),
            limite_min, limite_max, unidade, codigo,
            descricao_portugues, descricao_ingles, descricao_espanhol,
            metodo, tipo, frequencia, medicao, az, descricao_pt, descricao_en, descricao_es
        FROM analises_old
    """)

    cur.execute("DROP TABLE analises_old")
    con.commit()
    con.close()
    print("OK: 'parametro' agora tem DEFAULT '' e não impede salvar.")

if __name__ == "__main__":
    main()
