# app/data/full_migrate_access.py
from __future__ import annotations
import argparse, sqlite3, math, datetime
from pathlib import Path

try:
    import pyodbc
except Exception as e:
    raise SystemExit("pyodbc não está instalado. Rode: pip install pyodbc") from e


def list_tables(cursor) -> list[str]:
    """Lista tabelas visíveis no Access, ignorando MSys*."""
    tables = []
    # 1) Via catálogo do ODBC
    for row in cursor.tables():
        t = getattr(row, "table_name", None)
        tt = getattr(row, "table_type", None)
        if not t:
            continue
        if t.startswith("MSys"):
            continue
        if tt and tt.upper() in {"TABLE", "VIEW"}:
            tables.append(t)

    tables = sorted(set(tables))
    if tables:
        return tables

    # 2) Fallback via MSysObjects, se habilitado
    try:
        cursor.execute("SELECT Name FROM MSysObjects WHERE Type IN (1,4,6) AND Left(Name,4) <> 'MSys'")
        tables = [r[0] for r in cursor.fetchall()]
        tables = sorted(set(tables))
    except Exception:
        tables = []
    return tables


def map_sqlite_type(sample_values: list) -> str:
    """
    Mapeia tipo SQLite com base em valores de amostra.
    Heurística simples:
      - todos ints -> INTEGER
      - algum float -> REAL
      - algum datetime/date/time -> TEXT ISO ou NUMERIC, aqui usaremos TEXT
      - senão -> TEXT
    """
    has_float = False
    all_int = True
    has_dt = False

    for v in sample_values:
        if v is None:
            continue
        if isinstance(v, bool):
            # trata bool como int
            continue
        if isinstance(v, (int,)):
            continue
        if isinstance(v, (float,)):
            has_float = True
            all_int = False
        elif isinstance(v, (datetime.date, datetime.datetime, datetime.time)):
            has_dt = True
            all_int = False
        else:
            all_int = False

    if has_dt:
        return "TEXT"
    if has_float:
        return "REAL"
    if all_int:
        return "INTEGER"
    return "TEXT"


def migrate_table(src_cursor, dst_conn, table: str):
    # pega metadados e uma amostra para decidir tipos
    src_cursor.execute(f"SELECT * FROM [{table}]")
    desc = src_cursor.description or []
    cols = [d[0] for d in desc]

    # amostra de até 200 linhas
    rows_sample = src_cursor.fetchmany(200)
    types = []
    for i, col in enumerate(cols):
        sample_vals = [r[i] for r in rows_sample if len(r) > i]
        types.append(map_sqlite_type(sample_vals))

    # cria tabela de destino
    col_defs = ", ".join([f'"{c}" {t}' for c, t in zip(cols, types)])
    dst_conn.execute(f'CREATE TABLE IF NOT EXISTS "{table}" ({col_defs});')
    dst_conn.commit()

    # se já lemos amostra, precisamos inserir também as amostras
    placeholders = ", ".join(["?"] * len(cols))
    if rows_sample:
        dst_conn.executemany(f'INSERT INTO "{table}" VALUES ({placeholders})', rows_sample)

    # insere o resto
    while True:
        more = src_cursor.fetchmany(1000)
        if not more:
            break
        dst_conn.executemany(f'INSERT INTO "{table}" VALUES ({placeholders})', more)
    dst_conn.commit()


def migrate(accdb_path: Path, sqlite_path: Path):
    # abre fonte
    conn_str = (
        r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};"
        rf"DBQ={accdb_path};"
    )
    src = pyodbc.connect(conn_str, autocommit=True)
    sc = src.cursor()

    # recria destino
    if sqlite_path.exists():
        sqlite_path.unlink()
    dst = sqlite3.connect(str(sqlite_path))
    dst.execute("PRAGMA foreign_keys = ON;")

    # lista tabelas
    tables = list_tables(sc)
    if not tables:
        print("Aviso, nenhuma tabela listada. Verifique permissões do Access.")
        src.close()
        dst.close()
        return

    print(f"Tabelas encontradas: {tables}")

    # migra cada tabela
    for t in tables:
        try:
            migrate_table(sc, dst, t)
            # contagem para log
            cur = dst.cursor()
            cur.execute(f'SELECT COUNT(*) FROM "{t}"')
            n = cur.fetchone()[0]
            print(f"OK {t}  linhas {n}")
        except Exception as e:
            print(f"Falhou {t}  motivo {e}")

    # resumo final
    cur = dst.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    all_tables = [r[0] for r in cur.fetchall()]
    print("Resumo das tabelas no SQLite:", all_tables)
    for t in all_tables:
        cur.execute(f'SELECT COUNT(*) FROM "{t}"')
        print(f"- {t}: {cur.fetchone()[0]} linhas")

    src.close()
    dst.close()
    print("Migração concluída.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--accdb", required=True, help="Caminho do arquivo .accdb")
    ap.add_argument("--sqlite", default="qualidade.db", help="Arquivo SQLite de saída")
    args = ap.parse_args()
    migrate(Path(args.accdb), Path(args.sqlite))


if __name__ == "__main__":
    main()
