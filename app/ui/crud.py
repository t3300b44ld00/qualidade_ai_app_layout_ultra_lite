from __future__ import annotations

from typing import List, Tuple, Optional
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QTableWidget, QTableWidgetItem, QMessageBox, QWidget
)


class CrudWidget(QFrame):
    """
    CRUD genérico com padrão visual unificado.

    - Botões: Novo, Salvar, Excluir, Localizar (com campo de busca)
    - Tabela com colunas definidas pelo chamador
    - Suporte a INSERT/UPDATE/DELETE
    - Detecção automática do identificador (usa 'id' se existir; caso contrário usa rowid)
    """

    def __init__(self,
                 db,
                 table_name: str,
                 columns: List[Tuple[str, str]],
                 read_only: bool = False,
                 parent: Optional[QWidget] = None):
        """
        :param db: Database()
        :param table_name: nome da tabela no SQLite
        :param columns: lista [(coluna_db, "Rótulo"), ...]
        :param read_only: se True, desabilita edição/inserção/remoção
        """
        super().__init__(parent)
        self.db = db
        self.table_name = table_name
        self.columns = columns
        self.read_only = read_only

        self.setObjectName("TableCard")
        self._row_ids: List[Optional[int]] = []   # guarda id/rowid das linhas

        self._detect_id_field()
        self._build_ui()
        self._load()

    # ------------------------ UI ------------------------

    def _build_ui(self):
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
        self.table = QTableWidget(0, len(self.columns))
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(self.table.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(self.table.EditTrigger.DoubleClicked |
                                   self.table.EditTrigger.EditKeyPressed |
                                   self.table.EditTrigger.AnyKeyPressed)

        headers = [c[1] for c in self.columns]
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setStretchLastSection(True)
        root.addWidget(self.table, 1)

        # Sinais
        self.btn_new.clicked.connect(self._on_new)
        self.btn_save.clicked.connect(self._on_save)
        self.btn_del.clicked.connect(self._on_delete)
        self.ed_filter.textChanged.connect(self._apply_filter)
        self.btn_loc.clicked.connect(self._focus_first_match)

    # ------------------------ Dados ------------------------

    def _detect_id_field(self):
        """Descobre se a tabela tem coluna 'id'. Se não tiver, usa 'rowid'."""
        cur = self.db.conn.cursor()
        try:
            cur.execute(f'PRAGMA table_info("{self.table_name}")')
            cols = [r[1].lower() for r in cur.fetchall()]
        except Exception:
            cols = []
        self._id_field = "id" if "id" in cols else "rowid"

    def _select_sql(self) -> str:
        cols_sql = ", ".join([f'"{c[0]}"' for c in self.columns])
        if self._id_field == "rowid":
            return f'SELECT rowid AS _id, {cols_sql} FROM "{self.table_name}"'
        else:
            return f'SELECT "{self._id_field}" AS _id, {cols_sql} FROM "{self.table_name}"'

    def _load(self):
        self.table.setRowCount(0)
        self._row_ids.clear()

        cur = self.db.conn.cursor()
        try:
            cur.execute(self._select_sql())
            rows = cur.fetchall()
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Falha ao carregar dados de '{self.table_name}'.\n{e}")
            rows = []

        for row in rows:
            _id = row[0]
            values = [str(x) if x is not None else "" for x in row[1:]]
            self._append_row(_id, values)

        self._resize_cols()

    def _append_row(self, row_id: Optional[int], values: list[str]):
        r = self.table.rowCount()
        self.table.insertRow(r)
        self._row_ids.append(row_id)

        for c, txt in enumerate(values):
            it = QTableWidgetItem(txt)
            it.setFlags(it.flags() | Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(r, c, it)

    def _collect_row(self, r: int) -> list[str]:
        vals = []
        for c in range(len(self.columns)):
            it = self.table.item(r, c)
            vals.append(it.text().strip() if it else "")
        return vals

    # ------------------------ Ações ------------------------

    def _on_new(self):
        self._append_row(None, [""] * len(self.columns))
        self._resize_cols()
        self.table.scrollToBottom()

    def _on_delete(self):
        sel = self.table.selectionModel().selectedRows()
        if not sel:
            return
        if QMessageBox.question(self, "Excluir",
                                "Deseja excluir o(s) registro(s) selecionado(s)?") != QMessageBox.StandardButton.Yes:
            return

        cur = self.db.conn.cursor()
        rows_to_remove = sorted([m.row() for m in sel], reverse=True)

        for r in rows_to_remove:
            rid = self._row_ids[r]
            if rid is not None:
                try:
                    cur.execute(f'DELETE FROM "{self.table_name}" WHERE {self._id_field}=?', (rid,))
                except Exception as e:
                    QMessageBox.warning(self, "Excluir", f"Falha ao excluir linha {r+1}:\n{e}")
                    continue
            self.table.removeRow(r)
            self._row_ids.pop(r)

        self.db.conn.commit()

    def _on_save(self):
        cur = self.db.conn.cursor()
        col_names = [c[0] for c in self.columns]

        for r in range(self.table.rowCount()):
            rid = self._row_ids[r]
            values = self._collect_row(r)

            # INSERT
            if rid is None:
                placeholders = ", ".join(["?"] * len(col_names))
                cols_sql = ", ".join([f'"{c}"' for c in col_names])
                try:
                    cur.execute(
                        f'INSERT INTO "{self.table_name}" ({cols_sql}) VALUES ({placeholders})',
                        tuple(values)
                    )
                    self._row_ids[r] = cur.lastrowid
                except Exception as e:
                    QMessageBox.warning(self, "Salvar", f"Falha ao inserir linha {r+1}:\n{e}")
                    self.db.conn.rollback()
                    return
            # UPDATE
            else:
                set_sql = ", ".join([f'"{c}"=?' for c in col_names])
                try:
                    cur.execute(
                        f'UPDATE "{self.table_name}" SET {set_sql} WHERE {self._id_field}=?',
                        tuple(values) + (rid,)
                    )
                except Exception as e:
                    QMessageBox.warning(self, "Salvar", f"Falha ao atualizar linha {r+1}:\n{e}")
                    self.db.conn.rollback()
                    return

        self.db.conn.commit()
        QMessageBox.information(self, "Salvar", "Registros salvos com sucesso.")
        self._load()

    # ------------------------ Util ------------------------

    def _apply_filter(self, text: str):
        text = (text or "").strip().lower()
        for r in range(self.table.rowCount()):
            visible = False
            for c in range(self.table.columnCount()):
                it = self.table.item(r, c)
                txt = (it.text() if it else "").lower()
                if text in txt:
                    visible = True
                    break
            self.table.setRowHidden(r, not visible)

    def _focus_first_match(self):
        text = self.ed_filter.text().strip().lower()
        if not text:
            return
        for r in range(self.table.rowCount()):
            if self.table.isRowHidden(r):
                continue
            for c in range(self.table.columnCount()):
                it = self.table.item(r, c)
                if it and text in it.text().lower():
                    self.table.selectRow(r)
                    self.table.scrollToItem(it)
                    return

    def _resize_cols(self):
        self.table.resizeColumnsToContents()
        if self.table.columnCount() >= 1:
            self.table.setColumnWidth(0, max(self.table.columnWidth(0), 240))
        if self.table.columnCount() >= 2:
            self.table.setColumnWidth(1, max(self.table.columnWidth(1), 160))
