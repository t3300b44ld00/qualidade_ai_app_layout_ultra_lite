# scripts/reset_admin.py
import hashlib
from app.data.db import Database

NOVA_SENHA = "admin"   # troque aqui pelo que quiser

db = Database()
h = hashlib.sha256(NOVA_SENHA.encode("utf-8")).hexdigest()

cur = db.conn.cursor()
cur.execute("UPDATE funcionarios SET senha=? WHERE LOWER(login)='admin'", (h,))
if cur.rowcount == 0:
    # se por algum motivo não existir, recria o admin
    cur.execute("""
        INSERT INTO funcionarios (nome, registro, login, senha, papel)
        VALUES ('Administrador', '000001', 'admin', ?, 'admin')
    """, (h,))
db.conn.commit()
print("Senha do admin atualizada com sucesso.")
