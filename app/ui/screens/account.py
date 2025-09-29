from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QLineEdit,
    QPushButton, QMessageBox, QSizePolicy
)
from PyQt6.QtCore import Qt


class ChangePasswordWidget(QWidget):
    """
    Troca de senha padronizada.
    Campos compactos, centralizados e botão primário no padrão do sistema.
    """
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.user = None  # será definido por set_user

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(12)

        # cartão central para limitar a largura e padronizar visual
        card = QFrame()
        card.setObjectName("LoginCard")
        card.setMaximumWidth(560)
        card.setMinimumWidth(420)

        form = QVBoxLayout(card)
        form.setContentsMargins(16, 16, 16, 16)
        form.setSpacing(10)

        # identificação do usuário atual
        self.lbl_user = QLabel("Usuário. —  Login. —")
        self.lbl_user.setProperty("class", "Field")
        form.addWidget(self.lbl_user)

        # senha atual
        self.edt_old = QLineEdit()
        self.edt_old.setPlaceholderText("Senha atual")
        self.edt_old.setEchoMode(QLineEdit.EchoMode.Password)
        self._compact(self.edt_old)
        form.addWidget(self.edt_old)

        # nova senha
        self.edt_new = QLineEdit()
        self.edt_new.setPlaceholderText("Nova senha")
        self.edt_new.setEchoMode(QLineEdit.EchoMode.Password)
        self._compact(self.edt_new)
        form.addWidget(self.edt_new)

        # confirmar nova senha
        self.edt_confirm = QLineEdit()
        self.edt_confirm.setPlaceholderText("Confirmar nova senha")
        self.edt_confirm.setEchoMode(QLineEdit.EchoMode.Password)
        self._compact(self.edt_confirm)
        form.addWidget(self.edt_confirm)

        # botão salvar padronizado
        row_btn = QHBoxLayout()
        row_btn.addStretch(1)

        self.btn_save = QPushButton("Salvar nova senha")
        self.btn_save.setProperty("kind", "primary")
        self.btn_save.setMinimumHeight(30)
        self.btn_save.setMaximumHeight(30)
        self.btn_save.setFixedWidth(200)
        self.btn_save.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_save.clicked.connect(self._on_save)

        # Enter envia o formulário
        self.edt_confirm.returnPressed.connect(self._on_save)
        self.edt_new.returnPressed.connect(self._on_save)
        self.edt_old.returnPressed.connect(self._on_save)

        row_btn.addWidget(self.btn_save)
        row_btn.addStretch(1)
        form.addLayout(row_btn)

        # centraliza o cartão
        wrap = QHBoxLayout()
        wrap.addStretch(1)
        wrap.addWidget(card)
        wrap.addStretch(1)

        root.addLayout(wrap)
        root.addStretch(1)

    def _compact(self, line_edit: QLineEdit):
        """Aplica dimensões compactas padronizadas aos campos."""
        line_edit.setMinimumHeight(30)
        line_edit.setMaximumWidth(420)
        line_edit.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

    def set_user(self, user: dict):
        """Recebe o usuário atual para validação e update."""
        self.user = user or {}
        nome = self.user.get("nome", "—")
        login = self.user.get("login", "—")
        self.lbl_user.setText(f"Usuário. {nome}  Login. {login}")

    def _on_save(self):
        if not self.user:
            QMessageBox.warning(self, "Atenção", "Nenhum usuário autenticado.")
            return

        old = self.edt_old.text().strip()
        new = self.edt_new.text().strip()
        confirm = self.edt_confirm.text().strip()

        if not old or not new or not confirm:
            QMessageBox.information(self, "Atenção", "Preencha todos os campos.")
            return
        if new != confirm:
            QMessageBox.information(self, "Atenção", "A confirmação precisa ser igual à nova senha.")
            return
        if len(new) < 4:
            QMessageBox.information(self, "Atenção", "Use ao menos 4 caracteres.")
            return
        if new == old:
            QMessageBox.information(self, "Atenção", "A nova senha não pode ser igual à atual.")
            return

        # valida a senha atual usando a mesma rotina do login
        login = self.user.get("login")
        auth = self.db.verify_user(login, old)
        if not auth:
            QMessageBox.warning(self, "Atenção", "Senha atual incorreta.")
            return

        # grava no banco
        try:
            cur = self.db.conn.cursor()
            cur.execute("UPDATE funcionarios SET senha=? WHERE id=?", (new, self.user.get("id")))
            self.db.conn.commit()
        except Exception as e:
            self.db.conn.rollback()
            QMessageBox.warning(self, "Erro", f"Não foi possível salvar. {e}")
            return

        # limpeza e confirmação
        self.edt_old.clear()
        self.edt_new.clear()
        self.edt_confirm.clear()
        QMessageBox.information(self, "Pronto", "Senha atualizada com sucesso.")
