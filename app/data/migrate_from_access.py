import argparse, sqlite3
from pathlib import Path
try:
    import pyodbc
except Exception:
    pyodbc = None

try:
    import pandas as pd
    HAS_PANDAS = True
except Exception:
    HAS_PANDAS = False

ACCESS_DRIVER_CANDIDATES = [
    "{Microsoft Access Driver (*.mdb, *.accdb)}",
    "{Microsoft Access Driver (*.mdb)}",
]

def find_access_driver():
    for d in ACCESS_DRIVER_CANDIDATES:
        try:
            conn = pyodbc.connect(f"DRIVER={d};DBQ=:memory:", autocommit=True, timeout=1)
        except Exception:
            continue
        else:
            conn.close()
            return d
    return "{Microsoft Access Driver (*.mdb, *.accdb)}"

def list_tables(conn):
    cur = conn.cursor()
    return [row.table_name for row in cur.tables(tableType="TABLE")]

def migrate_with_pandas(cn, sqlite_path):
    print("Usando pandas para migrar")
    import pandas as pd
    sq = sqlite3.connect(sqlite_path)
    for t in list_tables(cn):
        df = pd.read_sql(f"SELECT * FROM [{t}]", cn)
        df.to_sql(t, sq, index=False, if_exists="replace")
        print(f"Tabela {t} migrada. Linhas {len(df)}")
    sq.commit()
    sq.close()

def migrate_pure_pyodbc(cn, sqlite_path):
    print("Migração sem pandas. Tipos convertidos para TEXT por compatibilidade.")
    sq = sqlite3.connect(sqlite_path)
    cur = cn.cursor()
    for t in list_tables(cn):
        cols = [col.column_name for col in cur.columns(table=t)]
        cols_sql = ", ".join([f'"{c}" TEXT' for c in cols])
        sq.execute(f'CREATE TABLE IF NOT EXISTS "{t}" ({cols_sql});')
        rows = cur.execute(f"SELECT * FROM [{t}]").fetchall()
        if rows:
            placeholders = ",".join(["?"]*len(cols))
            sq.executemany(f'INSERT INTO "{t}" VALUES ({placeholders})', [tuple(r) for r in rows])
        print(f"Tabela {t} migrada. Linhas {len(rows)}")
    sq.commit()
    sq.close()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--accdb", required=True)
    ap.add_argument("--sqlite", default=str(Path(__file__).resolve().parent / "qualidade.db"))
    args = ap.parse_args()

    if pyodbc is None:
        raise SystemExit('Instale pyodbc para usar a migração do Access. Abra um novo venv com Python 3.11 e rode: pip install pyodbc==5.1.0')
    driver = find_access_driver()
    print("Driver", driver)
    cn = pyodbc.connect(f"DRIVER={driver};DBQ={args.accdb};")
    sqpath = Path(args.sqlite)
    if sqpath.exists():
        sqpath.unlink()
    if HAS_PANDAS:
        migrate_with_pandas(cn, str(sqpath))
    else:
        migrate_pure_pyodbc(cn, str(sqpath))
    cn.close()
    print("Migração concluída.")

if __name__ == "__main__":
    main()
