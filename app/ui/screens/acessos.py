from __future__ import annotations

from typing import Optional, Dict

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QCheckBox, QMessageBox, QGridLayout, QLineEdit
)

# importa o mapa de permissões diretamente do db
from ...data.db import PERMS


PERM_LABELS = {
    "cad_func": "Cadastrar Funcionários",
    "def_acessos": "Definir Acessos",
    "cad_clientes": "Cadastrar Clientes",
    "cad_registros": "Cadastrar Registros",
    "cad_analises": "Cadastrar Análises",
    "cad_produtos": "Cadastrar Produtos",
    "cad_fabrica": "Cadastrar Fábrica",
    "cad_analise_prod": "Cadastrar Análise por Produto",
    "cad_analise_cli": "Cadastrar Análise por Cliente",
    "imp_rotulos": "Imprimir Rótulos",
    "inserir_resultados": "Inserir Resultados das Análises",
    "emitir_certificados": "Emitir Certificados",
    "imprimir_certificados": "Imprimir Certificados",
    "consultas_gerais": "Consultas Gerais",
    "liberacao_especial": "Liberação Especial",
}


class AcessosWidget(QFrame):
    """
    Tela de Acessos com padrão visual unificado:
      - Combobox para selecionar o usuário (login)
      - Conjunto de checkboxes para as permissões
      - Botões: Novo, Salvar, Excluir
    A tabela utilizada é 'acessos', indexada por 'login'.
    """

    def __init__(self, db, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.db = db
        self.setObjectName("TableCard")

        self._build_ui()
        self._load_users()
        self._load_for_login(self.cmb_user.currentText())

    # ---------------- UI ----------------

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        # Barra superior (ferramentas)
        tools = QFrame()
        tl = QHBoxLayout(tools)
        tl.setContentsMargins(0, 0, 0, 0)
        tl.setSpacing(8)

        self.btn_new = QPushButton("Novo")
        self.btn_save = QPushButton("Salvar")
        self.btn_del = QPushButton("Excluir"); self.btn_del.setProperty("kind", "danger")
        tl.addWidget(self.btn_new)
        tl.addWidget(self.btn_save)
        tl.addWidget(self.btn_del)
        tl.addSpacing(12)

        tl.addWidget(QLabel("Administrador"))
        self.cmb_user = QComboBox()
        self.cmb_user.setMinimumWidth(280)
        tl.addWidget(self.cmb_user, 1)

        root.addWidget(tools)

        # grade de permissões
        grid = QGridLayout()
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(8)

        self.checks: Dict[str, QCheckBox] = {}
        row = 0
        col = 0
        for key in PERMS:
            lbl = PERM_LABELS.get(key, key)
            chk = QCheckBox(lbl)
            self.checks[key] = chk
            grid.addWidget(chk, row, col, alignment=Qt.AlignmentFlag.AlignLeft)
            col += 1
            if col >= 2:   # 2 colunas
                col = 0
                row += 1

        perm_box = QFrame()
        perm_box.setLayout(grid)
        root.addWidget(perm_box, 1)

        # sinais
        self.cmb_user.currentTextChanged.connect(self._load_for_login)
        self.btn_new.clicked.connect(self._on_new)
        self.btn_save.clicked.connect(self._on_save)
        self.btn_del.clicked.connect(self._on_delete)

    # ---------------- dados ----------------

    def _load_users(self):
        """Preenche a combo com os logins existentes na tabela funcionarios."""
        self.cmb_user.clear()
        cur = self.db.conn.cursor()
        try:
            cur.execute("SELECT login, COALESCE(nome,'') AS nome FROM funcionarios WHERE login IS NOT NULL ORDER BY login")
            rows = cur.fetchall()
        except Exception:
            rows = []
        for r in rows:
            display = f"{r['login']}"
            if r["nome"]:
                display = f"{r['login']}  [{r['nome']}]"
            self.cmb_user.addItem(display, r["login"])
        if self.cmb_user.count() == 0:
            self.cmb_user.addItem("admin [Administrador]", "admin")

    def _current_login(self) -> str:
        return self.cmb_user.currentData() or self.cmb_user.currentText().split()[0]

    def _load_for_login(self, _display_login: str):
        """Carrega as flags para o login atual."""
        login = self._current_login()
        cur = self.db.conn.cursor()
        try:
            cur.execute("SELECT * FROM acessos WHERE LOWER(login)=LOWER(?)", (login,))
            row = cur.fetchone()
        except Exception:
            row = None

        if not row:
            # zera checks
            for k in PERMS:
                self.checks[k].setChecked(False)
            return

        for k in PERMS:
            self.checks[k].setChecked(bool(row[k]))

    # ---------------- ações ----------------

    def _on_new(self):
        """Limpa as permissões da tela (não apaga do banco)."""
        for k in PERMS:
            self.checks[k].setChecked(False)

    def _on_save(self):
        login = self._current_login()
        flags = {k: (1 if self.checks[k].isChecked() else 0) for k in PERMS}

        cur = self.db.conn.cursor()
        # tenta UPDATE primeiro
        set_sql = ", ".join([f"{k}=?" for k in PERMS])
        try:
            cur.execute(f"UPDATE acessos SET {set_sql} WHERE LOWER(login)=LOWER(?)",
                        tuple(flags[k] for k in PERMS) + (login,))
            if cur.rowcount == 0:
                # não existia => INSERT
                cols = ", ".join(["login"] + PERMS)
                ph = ", ".join(["?"] * (1 + len(PERMS)))
                cur.execute(
                    f"INSERT INTO acessos ({cols}) VALUES ({ph})",
                    (login, *[flags[k] for k in PERMS])
                )
        except Exception as e:
            self.db.conn.rollback()
            QMessageBox.warning(self, "Acessos", f"Falha ao salvar permissões:\n{e}")
            return

        self.db.conn.commit()
        QMessageBox.information(self, "Acessos", "Permissões salvas com sucesso.")

    def _on_delete(self):
        login = self._current_login()
        if QMessageBox.question(self, "Acessos",
                                f"Remover permissões cadastradas para '{login}'?") != QMessageBox.StandardButton.Yes:
            return
        cur = self.db.conn.cursor()
        try:
            cur.execute("DELETE FROM acessos WHERE LOWER(login)=LOWER(?)", (login,))
            self.db.conn.commit()
        except Exception as e:
            QMessageBox.warning(self, "Acessos", f"Falha ao excluir permissões:\n{e}")
            return
        self._on_new()
        QMessageBox.information(self, "Acessos", "Permissões removidas.")
