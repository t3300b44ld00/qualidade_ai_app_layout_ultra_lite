from __future__ import annotations

import re
import hashlib
from typing import List, Optional, Dict

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QComboBox, QMessageBox
)

# Mapeamentos papel ⇄ texto
ROLE_DISPLAY_TO_DB = {
    "Administrador": "admin",
    "Operador": "operador",
    "Usuário": "usuario",
    "Qualidade": "qualidade",
}
ROLE_DB_TO_DISPLAY = {v: k for k, v in ROLE_DISPLAY_TO_DB.items()}


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _slug_login_from(nome: str) -> str:
    """ Cria login simplificado com base no nome. """
    s = nome.strip().lower()
    s = re.sub(r"[áàâãä]", "a", s)
    s = re.sub(r"[éèêë]", "e", s)
    s = re.sub(r"[íìîï]", "i", s)
    s = re.sub(r"[óòôõö]", "o", s)
    s = re.sub(r"[úùûü]", "u", s)
    s = re.sub(r"[ç]", "c", s)
    s = re.sub(r"[^a-z0-9 ]+", "", s)
    parts = [p for p in s.split() if p]
    if not parts:
        return "user"
    if len(parts) == 1:
        return parts[0]
    return f"{parts[0]}.{parts[-1]}"


class FuncionariosWidget(QFrame):
    """
    Tela de Funcionários padronizada:

    Colunas: Nome | Registro | Tipo de Acesso | Senha
    - 'Tipo de Acesso' é um Combo por linha.
    - 'Senha' vazia => não altera a senha no UPDATE.
    """

    def __init__(self, db, read_only: bool = False, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.db = db
        self.read_only = read_only

        self.setObjectName("TableCard")
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        # Barra de ferramentas
        tools = QFrame()
        tl = QHBoxLayout(tools)
        tl.setContentsMargins(0, 0, 0, 0)
        tl.setSpacing(8)

        self.btn_new = QPushButton("Novo")
        self.btn_save = QPushButton("Salvar")
        self.btn_del = QPushButton("Excluir"); self.btn_del.setProperty("kind", "danger")
        self.btn_loc = QPushButton("Localizar"); self.btn_loc.setProperty("kind", "outline")

        if self.read_only:
            for b in (self.btn_new, self.btn_save, self.btn_del):
                b.setEnabled(False)

        tl.addWidget(self.btn_new)
        tl.addWidget(self.btn_save)
        tl.addWidget(self.btn_del)

        tl.addSpacing(12)
        tl.addWidget(QLabel("Buscar"))
        self.ed_filter = QLineEdit()
        self.ed_filter.setPlaceholderText("Digite para filtrar")
        self.ed_filter.setClearButtonEnabled(True)
        tl.addWidget(self.ed_filter, 1)
        tl.addWidget(self.btn_loc)

        root.addWidget(tools)

        # Tabela
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Nome", "Registro", "Tipo de Acesso", "Senha"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(self.table.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(self.table.EditTrigger.NoEditTriggers)  # widgets por célula
        root.addWidget(self.table, 1)

        self._row_ids: List[Optional[int]] = []

        # sinais
        self.btn_new.clicked.connect(self._on_new)
        self.btn_save.clicked.connect(self._on_save)
        self.btn_del.clicked.connect(self._on_delete)
        self.ed_filter.textChanged.connect(self._apply_filter)
        self.btn_loc.clicked.connect(self._focus_first_match)

        self._load()

    # -------------------- dados --------------------

    def _load(self):
        self.table.setRowCount(0)
        self._row_ids.clear()
        cur = self.db.conn.cursor()
        try:
            cur.execute("""
                SELECT id, nome, IFNULL(registro,''), IFNULL(papel,'usuario'), senha
                  FROM funcionarios
              ORDER BY nome COLLATE NOCASE
            """)
            rows = cur.fetchall()
        except Exception as e:
            QMessageBox.warning(self, "Funcionários", f"Erro ao carregar dados:\n{e}")
            rows = []

        for (fid, nome, registro, papel_db, _senha) in rows:
            self._append_row(fid,
                             nome or "",
                             registro or "",
                             ROLE_DB_TO_DISPLAY.get((papel_db or "usuario").lower(), "Usuário"),
                             "")
        self._resize_cols()

    def _append_row(self, fid: Optional[int], nome: str, registro: str,
                    papel_display: str, senha_plain: str):
        r = self.table.rowCount()
        self.table.insertRow(r)
        self._row_ids.append(fid)

        ed_nome = QLineEdit(nome)
        self.table.setCellWidget(r, 0, ed_nome)

        ed_reg = QLineEdit(registro)
        ed_reg.setMaxLength(20)
        self.table.setCellWidget(r, 1, ed_reg)

        cb_papel = QComboBox()
        cb_papel.addItems(["Administrador", "Operador", "Usuário", "Qualidade"])
        if papel_display not in ROLE_DISPLAY_TO_DB:
            papel_display = "Usuário"
        cb_papel.setCurrentText(papel_display)
        self.table.setCellWidget(r, 2, cb_papel)

        ed_pwd = QLineEdit(senha_plain)
        ed_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        ed_pwd.setPlaceholderText("••••••")
        self.table.setCellWidget(r, 3, ed_pwd)

        for c in range(4):
            self.table.setItem(r, c, QTableWidgetItem(""))

    def _collect_row(self, r: int) -> Dict[str, str]:
        nome: str = self.table.cellWidget(r, 0).text().strip()
        registro: str = self.table.cellWidget(r, 1).text().strip()
        papel_display: str = self.table.cellWidget(r, 2).currentText().strip()
        papel_db: str = ROLE_DISPLAY_TO_DB.get(papel_display, "usuario")
        senha_plain: str = self.table.cellWidget(r, 3).text()
        return {
            "nome": nome,
            "registro": registro,
            "papel_db": papel_db,
            "senha_plain": senha_plain,
        }

    # -------------------- ações --------------------

    def _on_new(self):
        self._append_row(None, "", "", "Usuário", "")
        self._resize_cols()
        self.table.scrollToBottom()

    def _on_delete(self):
        sel = self.table.selectionModel().selectedRows()
        if not sel:
            return
        if QMessageBox.question(self, "Excluir", "Deseja excluir o(s) registro(s) selecionado(s)?") != QMessageBox.StandardButton.Yes:
            return

        cur = self.db.conn.cursor()
        for m in sel:
            r = m.row()
            fid = self._row_ids[r]
            if fid is not None:
                try:
                    cur.execute("DELETE FROM funcionarios WHERE id = ?", (fid,))
                except Exception as e:
                    QMessageBox.warning(self, "Excluir", f"Falha ao excluir id={fid}:\n{e}")
                    continue
            self.table.removeRow(r)
            self._row_ids.pop(r)

        self.db.conn.commit()

    def _on_save(self):
        cur = self.db.conn.cursor()

        for r in range(self.table.rowCount()):
            fid = self._row_ids[r]
            data = self._collect_row(r)

            if not data["nome"]:
                QMessageBox.warning(self, "Salvar", "Informe o nome do funcionário.")
                return

            login = self._default_login_for_row(cur, r, data)
            pwd_hash = _sha256(data["senha_plain"]) if data["senha_plain"] else None

            try:
                if fid is None:
                    if pwd_hash is None:
                        pwd_hash = _sha256("1234")
                    cur.execute(
                        """
                        INSERT INTO funcionarios (nome, registro, login, senha, papel)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (data["nome"], data["registro"], login, pwd_hash, data["papel_db"]),
                    )
                    self._row_ids[r] = cur.lastrowid
                else:
                    if pwd_hash is None:
                        cur.execute(
                            """
                            UPDATE funcionarios
                               SET nome=?, registro=?, login=?, papel=?
                             WHERE id=?
                            """,
                            (data["nome"], data["registro"], login, data["papel_db"], fid),
                        )
                    else:
                        cur.execute(
                            """
                            UPDATE funcionarios
                               SET nome=?, registro=?, login=?, senha=?, papel=?
                             WHERE id=?
                            """,
                            (data["nome"], data["registro"], login, pwd_hash, data["papel_db"], fid),
                        )
            except Exception as e:
                QMessageBox.warning(self, "Salvar", f"Erro ao salvar linha {r+1}:\n{e}")
                return

        self.db.conn.commit()
        QMessageBox.information(self, "Salvar", "Registros salvos com sucesso.")
        self._load()

    def _default_login_for_row(self, cur, r: int, data: Dict[str, str]) -> str:
        login = data["registro"].strip() or _slug_login_from(data["nome"])
        base = login
        i = 1
        while True:
            cur.execute("SELECT 1 FROM funcionarios WHERE LOWER(login)=LOWER(?) AND id <> IFNULL(?, -1)",
                        (login, self._row_ids[r]))
            if not cur.fetchone():
                break
            i += 1
            login = f"{base}{i}"
        return login

    # -------------------- util --------------------

    def _apply_filter(self, text: str):
        text = (text or "").strip().lower()
        for r in range(self.table.rowCount()):
            nome = self.table.cellWidget(r, 0).text().lower()
            reg = self.table.cellWidget(r, 1).text().lower()
            self.table.setRowHidden(r, not (text in nome or text in reg))

    def _focus_first_match(self):
        text = self.ed_filter.text().strip().lower()
        for r in range(self.table.rowCount()):
            if self.table.isRowHidden(r):
                continue
            nome = self.table.cellWidget(r, 0).text().lower()
            reg = self.table.cellWidget(r, 1).text().lower()
            if text in nome or text in reg:
                self.table.selectRow(r)
                self.table.scrollToItem(self.table.item(r, 0))
                break

    def _resize_cols(self):
        self.table.resizeColumnsToContents()
        self.table.setColumnWidth(0, max(self.table.columnWidth(0), 320))
        self.table.setColumnWidth(1, max(self.table.columnWidth(1), 120))
        self.table.setColumnWidth(2, max(self.table.columnWidth(2), 180))
