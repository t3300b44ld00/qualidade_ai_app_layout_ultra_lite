import sqlite3
con = sqlite3.connect("qualidade.db")
tabelas = [r[0] for r in con.execute(
    "SELECT name FROM sqlite_master WHERE type='table' AND name='TBL_TipoAcesso'"
)]
print("Tem TBL_TipoAcesso:", tabelas)
linhas = con.execute("SELECT nome FROM TBL_TipoAcesso").fetchall() if tabelas else []
print("Perfis:", linhas)
con.close()
