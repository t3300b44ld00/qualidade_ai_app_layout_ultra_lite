# QualidadeAI
Layout inspirado no seu sistema de Access, com cabeçalho, menus laterais e centro de login.

## Rodar
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
python -m app.main

## Migrar Access para SQLite
Requer Microsoft Access Database Engine 2016 instalado.
python app/data/migrate_from_access.py --accdb "C:\caminho\Inspecao Qualidade.accdb"
