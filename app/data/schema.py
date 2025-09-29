from __future__ import annotations
import sqlite3
import hashlib

def _sha256(x: str) -> str:
    return hashlib.sha256(x.encode("utf-8")).hexdigest()

def ensure_schema(conn: sqlite3.Connection):
    cur = conn.cursor()

    # Funcionários (inclui registro)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS funcionarios (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            nome     TEXT NOT NULL,
            registro TEXT DEFAULT '',
            login    TEXT UNIQUE NOT NULL,
            senha    TEXT NOT NULL,
            papel    TEXT NOT NULL DEFAULT 'usuario'
        )
    """)

    # garante coluna 'registro' se DB for antigo
    cur.execute("PRAGMA table_info(funcionarios)")
    cols = {r[1] for r in cur.fetchall()}
    if "registro" not in cols:
        cur.execute("ALTER TABLE funcionarios ADD COLUMN registro TEXT DEFAULT ''")

    # cria admin se não existir
    cur.execute("SELECT id FROM funcionarios WHERE LOWER(login)='admin'")
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO funcionarios (nome, registro, login, senha, papel)
            VALUES (?, ?, ?, ?, ?)
        """, ("Administrador", "000001", "admin", _sha256("admin"), "admin"))

    # ---- Outras tabelas do seu app (mantidas) ----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS acessos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            papel TEXT NOT NULL,
            ativo INTEGER NOT NULL DEFAULT 1
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cnpj TEXT, contato TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS grupos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            descricao TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT, nome TEXT,
            cliente_id INTEGER, grupo_id INTEGER
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS analises (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produto_id INTEGER,
            parametro TEXT,
            limite_min REAL, limite_max REAL,
            unidade TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS testes_qualidade (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produto_id INTEGER,
            resultado TEXT,
            observacoes TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS inspecoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item TEXT, responsavel TEXT,
            status TEXT, observacoes TEXT
        )
    """)

    conn.commit()
