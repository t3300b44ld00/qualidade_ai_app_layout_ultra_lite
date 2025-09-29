from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional, Dict, Any


class Database:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(path))
        self.conn.row_factory = sqlite3.Row
        self.ensure_schema()

    @classmethod
    def ensure(cls, path: Path) -> "Database":
        return cls(path)

    def ensure_schema(self) -> None:
        cur = self.conn.cursor()

        # Tabelas básicas
        cur.execute("""
            CREATE TABLE IF NOT EXISTS funcionarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT,
                login TEXT UNIQUE,
                senha TEXT,
                papel TEXT DEFAULT 'user',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS grupos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS produtos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo TEXT,
                nome TEXT,
                cliente_id INTEGER,
                grupo_id INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(cliente_id) REFERENCES clientes(id),
                FOREIGN KEY(grupo_id)   REFERENCES grupos(id)
            )
        """)

        # Usuário admin padrão
        cur.execute("SELECT id FROM funcionarios WHERE login = 'admin'")
        if cur.fetchone() is None:
            cur.execute(
                "INSERT INTO funcionarios (nome, login, senha, papel) VALUES (?,?,?,?)",
                ("Administrador", "admin", "admin", "admin"),
            )

        self.conn.commit()

    # Autenticação
    def verify_user(self, login: str, senha: str) -> bool:
        cur = self.conn.cursor()
        cur.execute("SELECT id FROM funcionarios WHERE login = ? AND senha = ?", (login, senha))
        return cur.fetchone() is not None

    def get_user_by_login(self, login: str) -> Optional[Dict[str, Any]]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM funcionarios WHERE login = ?", (login,))
        row = cur.fetchone()
        return dict(row) if row else None
