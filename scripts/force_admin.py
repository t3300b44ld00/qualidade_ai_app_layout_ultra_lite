# scripts/force_admin.py
import argparse
from app.data.db import Database

def main():
    ap = argparse.ArgumentParser(description="Força/atualiza a senha do admin.")
    ap.add_argument("-u", "--user", default="admin", help="login do admin (padrão: admin)")
    ap.add_argument("-p", "--password", required=True, help="nova senha para o admin")
    args = ap.parse_args()

    db = Database()
    db.set_admin_password(args.password, args.user)
    print(f"Admin criado/atualizado com sucesso: login={args.user}")

if __name__ == "__main__":
    main()
