# scripts/print_paths.py
from app.config import DB_PATH
from app.data.db import Database

print("DB_PATH (config):", DB_PATH)

db = Database()
# mostra o arquivo físico que o SQLite abriu
print("SQLite PRAGMA database_list():", db.conn.execute("PRAGMA database_list").fetchall())
