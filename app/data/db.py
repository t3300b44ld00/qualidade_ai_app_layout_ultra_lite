from __future__ import annotations
import sqlite3
from pathlib import Path
import hashlib

try:
    from ..config import DB_PATH as CONFIG_DB_PATH
except Exception:
    CONFIG_DB_PATH = None

DEFAULT_DB_PATH = Path(__file__).resolve().parent / "qualidade.db"


def _resolve_db_path() -> Path:
    return Path(CONFIG_DB_PATH) if CONFIG_DB_PATH else DEFAULT_DB_PATH


def _sha256(p: str) -> str:
    return hashlib.sha256(p.encode("utf-8")).hexdigest()


# <<< NOVO: mapa exportado com todas as permissões >>>
PERMS = [
    "cad_func", "def_acessos", "cad_clientes", "cad_registros",
    "cad_analises", "cad_produtos", "cad_fabrica",
    "cad_analise_prod", "cad_analise_cli",
    "imp_rotulos", "inserir_resultados",
    "emitir_certificados", "imprimir_certificados",
    "consultas_gerais", "liberacao_especial"
]


class Database:
    def __init__(self) -> None:
        self.db_path = _resolve_db_path()
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.ensure_schema()
        self.ensure_admin()

    # ---------------- schema & migrações ----------------

    def ensure_schema(self) -> None:
        cur = self.conn.cursor()

        # funcionarios
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS funcionarios (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                nome     TEXT NOT NULL DEFAULT '',
                registro TEXT,
                login    TEXT UNIQUE,
                senha    TEXT NOT NULL,
                papel    TEXT NOT NULL DEFAULT 'usuario'
            )
            """
        )

        # acessos
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS acessos (
                login TEXT PRIMARY KEY,
                cad_func INTEGER DEFAULT 0,
                def_acessos INTEGER DEFAULT 0,
                cad_clientes INTEGER DEFAULT 0,
                cad_registros INTEGER DEFAULT 0,
                cad_analises INTEGER DEFAULT 0,
                cad_produtos INTEGER DEFAULT 0,
                cad_fabrica INTEGER DEFAULT 0,
                cad_analise_prod INTEGER DEFAULT 0,
                cad_analise_cli INTEGER DEFAULT 0,
                imp_rotulos INTEGER DEFAULT 0,
                inserir_resultados INTEGER DEFAULT 0,
                emitir_certificados INTEGER DEFAULT 0,
                imprimir_certificados INTEGER DEFAULT 0,
                consultas_gerais INTEGER DEFAULT 0,
                liberacao_especial INTEGER DEFAULT 0
            )
            """
        )

        # --- MIGRAÇÕES: garante colunas ausentes ---

        # funcionarios: registro, papel, login
        cur.execute('PRAGMA table_info("funcionarios")')
        fcols = {r[1].lower() for r in cur.fetchall()}
        if "registro" not in fcols:
            cur.execute('ALTER TABLE funcionarios ADD COLUMN registro TEXT')
        if "papel" not in fcols:
            cur.execute("ALTER TABLE funcionarios ADD COLUMN papel TEXT DEFAULT 'usuario'")
        if "login" not in fcols:
            cur.execute('ALTER TABLE funcionarios ADD COLUMN login TEXT')
            cur.execute('CREATE UNIQUE INDEX IF NOT EXISTS ux_funcionarios_login ON funcionarios(login)')

        # acessos: login único
        cur.execute('PRAGMA table_info("acessos")')
        acols = {r[1].lower() for r in cur.fetchall()}
        if "login" not in acols:
            cur.execute('ALTER TABLE acessos ADD COLUMN login TEXT')
        cur.execute('CREATE UNIQUE INDEX IF NOT EXISTS ux_acessos_login ON acessos(login)')

        self.conn.commit()

        # Preenche login se vier vazio
        cur.execute('UPDATE funcionarios SET login = COALESCE(login, LOWER(nome)) WHERE login IS NULL')
        self.conn.commit()

    # ---------------- admin & auth ----------------

    def ensure_admin(self) -> None:
        cur = self.conn.cursor()

        # admin em funcionarios
        cur.execute("SELECT id, senha FROM funcionarios WHERE lower(login)='admin'")
        row = cur.fetchone()
        if not row:
            cur.execute(
                "INSERT INTO funcionarios (nome, registro, login, senha, papel) VALUES (?,?,?,?,?)",
                ("Administrador", "01", "admin", _sha256("1234"), "admin"),
            )
        else:
            cur.execute("UPDATE funcionarios SET papel='admin', nome=COALESCE(nome,'Administrador') WHERE id=?",
                        (row["id"],))

        # acessos do admin (tudo liberado)
        cols = ", ".join(PERMS)
        vals = ", ".join(["1"] * len(PERMS))
        cur.execute(
            f"INSERT OR IGNORE INTO acessos (login,{cols}) VALUES ('admin',{vals})"
        )

        self.conn.commit()

    def verify_user(self, user_input: str, password: str):
        """Autentica por login/nome/registro. Aceita senha SHA-256 (hash) ou texto puro."""
        cur = self.conn.cursor()
        hp = _sha256(password)

        for col in ("login", "nome", "registro"):
            try:
                cur.execute(
                    f"""
                    SELECT id, nome, papel, login, senha
                      FROM funcionarios
                     WHERE {col}=? COLLATE NOCASE
                     LIMIT 1
                    """,
                    (user_input,)
                )
                row = cur.fetchone()
                if not row:
                    continue
                stored = row["senha"] or ""
                ok = (stored == hp) or (stored == password)
                if not ok:
                    return None
                return {"id": row["id"], "nome": row["nome"], "login": row["login"], "papel": row["papel"]}
            except Exception:
                continue
        return None

    # util
    def set_admin_password(self, new_password: str, login: str = "admin") -> None:
        cur = self.conn.cursor()
        cur.execute("SELECT id FROM funcionarios WHERE lower(login)=?", (login.lower(),))
        row = cur.fetchone()
        if row:
            cur.execute(
                "UPDATE funcionarios SET senha=?, papel='admin', nome=COALESCE(nome,'Administrador') WHERE id=?",
                (_sha256(new_password), row["id"]),
            )
        else:
            cur.execute(
                "INSERT INTO funcionarios (nome, login, senha, papel) VALUES (?,?,?,?)",
                ("Administrador", login, _sha256(new_password), "admin"),
            )
        self.conn.commit()
