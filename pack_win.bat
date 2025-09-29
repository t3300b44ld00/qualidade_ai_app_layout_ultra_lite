@echo off
python -m venv .venv
call .\.venv\Scripts\activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
pyinstaller app.spec
echo Pronto. Veja dist\QualidadeAI
