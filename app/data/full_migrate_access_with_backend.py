# app/data/full_migrate_access_with_backend.py
from __future__ import annotations
import argparse
import sqlite3
from pathlib import Path
import pyodbc

def open_access(path: Path):
    conn_str = (
        r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};"
        f"DBQ={path};"
    )
    return pyodbc.connect(conn_str, autocommit=True)

def list_with_link_info(cur):
    """
    Tenta ler MSysObjects para identificar tabelas locais e vinculadas.
    Retorna lista de tuplas: (nome, tipo, connect)
    tipo pode ser LOCAL ou VINCULADA.
    connect é a string do destino para vinculadas quando disponível.
    """
    items = []
    try:
        cur.execute("""
            SELECT Name, Type, Database
            FROM MSysObjects
            WHERE Type IN (1,4,6) AND Left(Name,4) <> 'MSys'
        """)
        for name, typ, dbstr in cur.fetchall():
            if dbstr:
                items.append((name, "VINCULADA", dbstr))
            else:
                items.append((name, "LOCAL", None))
        # remove duplicados mantendo ordem
        seen = set()
        uniq = []
        for t in items:
            if t[0] not in seen:
                uniq.append(t)
                seen.add(t[0])
        return uniq
    except Exception:
        # fallback, só lista nomes
        items = []
        for row in cur.tables():
            tname = getattr(row, "table_name", None)
            if not tname or tname.startswith("MSys"):
                continue
            items.append((tname, "LOCAL", None))
        return items

def create_table_if_needed(dst_conn: sqlite3.Connection, table: str, cols: list[str]):
    col_defs = ", ".join([f'"{c}" TEXT' for c in cols])
    sql = f'CREATE TABLE IF NOT EXISTS "{table}" ({col_defs});'
    dst_conn.execute(sql)
    dst_conn.commit()

def copy_all_rows(src_cursor, dst_conn: sqlite3.Connection, table: str):
    src_cursor.execute(f'SELECT * FROM [{table}]')
    desc = src_cursor.description or []
    cols = [d[0] for d in desc]
    create_table_if_needed(dst_conn, table, cols)
    placeholders = ", ".join(["?"] * len(cols))
    rows = src_cursor.fetchall()
    if rows:
        dst_conn.executemany(f'INSERT INTO "{table}" VALUES ({placeholders})', rows)
        dst_conn.commit()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--accdb", required=True, help="caminho do arquivo .accdb principal")
    ap.add_argument("--backend", help="caminho LOCAL do back-end .accdb que substitui o da rede")
    ap.add_argument("--sqlite", default="qualidade.db", help="arquivo SQLite de saída")
    args = ap.parse_args()

    accdb = Path(args.accdb)
    if not accdb.exists():
        raise SystemExit(f"Arquivo não encontrado: {accdb}")

    # abre fonte principal
    src = open_access(accdb)
    sc = src.cursor()
    tables = list_with_link_info(sc)

    # abre destino
    outp = Path(args.sqlite)
    if outp.exists():
        outp.unlink()
    dst = sqlite3.connect(str(outp))
    dst.execute("PRAGMA foreign_keys=ON;")

    # se foi informado um back-end local, abre também
    backend_cur = None
    if args.backend:
        backend_path = Path(args.backend)
        if not backend_path.exists():
            raise SystemExit(f"Back-end informado não existe: {backend_path}")
        backend_conn = open_access(backend_path)
        backend_cur = backend_conn.cursor()
    else:
        backend_conn = None

    print("Tabelas detectadas:")
    for name, kind, connstr in tables:
        print(f"- {name}  {kind}  {connstr or ''}")

    for name, kind, _ in tables:
        try:
            if kind == "LOCAL":
                copy_all_rows(sc, dst, name)
            else:
                if backend_cur is None:
                    print(f"Pulando {name} pois é vinculada e --backend não foi informado")
                    continue
                copy_all_rows(backend_cur, dst, name)
            cnt = dst.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0]
            print(f"OK {name}  linhas {cnt}")
        except Exception as e:
            print(f"Falhou {name}  motivo {e}")

    cur = dst.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tabs = [r[0] for r in cur.fetchall()]
    print("Resumo:", tabs)
    for t in tabs:
        n = cur.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
        print(f"- {t}: {n} linhas")

    if backend_conn:
        backend_conn.close()
    src.close()
    dst.close()
    print("Migração concluída.")

if __name__ == "__main__":
    main()
