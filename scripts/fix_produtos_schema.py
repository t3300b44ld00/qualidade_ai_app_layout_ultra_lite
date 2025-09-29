# scripts/fix_produtos_schema.py
import os, sqlite3

try:
    from app.config import DB_PATH
except Exception:
    DB_PATH = os.path.join("app", "data", "qualidade.db")

COLUMNS = {
    "codigo": "TEXT",
    "nome": "TEXT",
    "familia": "TEXT",
    "cor": "TEXT",
    "segmento": "TEXT",
    "reavaliar_dias": "INTEGER DEFAULT 0",
    "direto_extrusao": "INTEGER DEFAULT 0",  # 0/1
    "localizacao_padrao": "TEXT",
    "fabricado_em": "TEXT",  # ISO yyyy-mm-dd
    "lote_padrao": "TEXT",
    "revisao_num": "TEXT",
    "revisao_data": "TEXT",  # ISO yyyy-mm-dd
    "descricao_pt": "TEXT",
    "descricao_en": "TEXT",
    "descricao_es": "TEXT",
    "aplicacoes_pt": "TEXT",
    "aplicacoes_en": "TEXT",
    "aplicacoes_es": "TEXT",
    "historico_revisoes": "TEXT",
}

def main():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    info = cur.execute("PRAGMA table_info(produtos)").fetchall()
    have = {r[1] for r in info}

    added = []
    for col, ctype in COLUMNS.items():
        if col not in have:
            cur.execute(f"ALTER TABLE produtos ADD COLUMN {col} {ctype}")
            added.append(col)

    con.commit()
    print("DB_PATH:", DB_PATH)
    print("produtos -> colunas adicionadas:", added if added else "nenhuma (já ok)")
    cols_now = [r[1] for r in cur.execute("PRAGMA table_info(produtos)").fetchall()]
    print("colunas atuais:", cols_now)
    con.close()

if __name__ == "__main__":
    main()
