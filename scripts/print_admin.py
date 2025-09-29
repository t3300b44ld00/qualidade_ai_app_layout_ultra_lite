# scripts/print_admin.py
from app.data.db import Database

db = Database()
cur = db.conn.cursor()
cur.execute("SELECT id, nome, login, papel, substr(senha,1,16)||'...' AS senha_preview FROM funcionarios WHERE lower(login)='admin'")
row = cur.fetchone()
print(dict(row) if row else "admin não existe")
