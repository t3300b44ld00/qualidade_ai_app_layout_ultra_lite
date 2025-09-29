from .screens.impressao_certificados import ImpressaoCertificadosWidget
from .screens.inspecao_resultados import ResultadosInspecaoWidget
from .screens.analise_cliente import AnaliseClienteWidget
from .screens.analise_produto import AnaliseProdutoWidget
from .screens.testes import TestesQualidadeWidget
from .appearance import load_prefs, apply_typography_everywhere
from .font_prefs_dialog import FontPrefsDialog
from .table_theme import apply_table_theme
from .button_theme import apply_button_theme
from .utils.padding_delegate import LeftPaddingDelegate
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QFrame, QMessageBox, QStackedWidget,
    QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from pathlib import Path

from ..data.db import Database
from ..ai.nlp_assistant import QnAAssistant
from ..ai.anomaly_detection import AnomalyDetector

from .crud import CrudWidget
from .screens.reports import ReportsWidget
from .screens.certificado import CertificadoWidget
from .screens.account import ChangePasswordWidget

from .screens.funcionarios import FuncionariosWidget
from .screens.acessos import AcessosWidget
from .screens.produto import ProdutoWidget

# ------- NOVO: infraestrutura compartilhada -------
from .core.event_bus import EventBus
from .core.app_context import AppContext
from .services.data_service import DataService
from .services.certificate_service import CertificateService
# --------------------------------------------------

class ScaledImage(QLabel):
    def __init__(self, image_path: str, min_h: int = 260, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._orig = QPixmap(image_path)
        self.setMinimumHeight(min_h)
        if not self._orig.isNull():
            self.setPixmap(self._orig)
        else:
            self.setText("Imagem do dashboard não encontrada")
            self.setStyleSheet("color: #7a7a7a;")

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if not self._orig.isNull():
            self.setPixmap(
                self._orig.scaled(
                    self.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Controle da Qualidade | Inspeção em Linha")
        self.resize(1280, 800)

        self.db = Database()
        self._ensure_grupos_espanhol_column()
        self._ensure_analises_codigo_column()

        # ------- NOVO infra -------
        self.bus = EventBus(self)
        self.ctx = AppContext()
        self.services = DataService(self.db, self.ctx, self.bus)
        self.cert_service = CertificateService()
        # conectar impressão/pdf globais
        self.bus.requestPrint.connect(self.cert_service.print_html)
        self.bus.requestPdf.connect(self.cert_service.save_pdf)
        # --------------------------

        self.assistant = QnAAssistant(self.db)
        self.anomaly = AnomalyDetector(self.db)
        self.current_user = None

        self.page_wrappers: dict[str, QWidget] = {}

        root = QWidget()
        root_layout = QVBoxLayout(root)
        root.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setCentralWidget(root)

        # -------------------- HEADER --------------------
        header = QFrame(objectName="Header")
        header.setMaximumHeight(120)
        header.setMinimumHeight(90)

        hbox = QHBoxLayout(header)
        hbox.setContentsMargins(12, 8, 12, 8)
        hbox.setSpacing(8)

        logo = QLabel()
        LOGO_H = 180
        logo_path = Path(__file__).resolve().parents[2] / "assets" / "logo_enepol.png"
        if logo_path.exists():
            pix = QPixmap(str(logo_path)).scaledToHeight(
                LOGO_H, Qt.TransformationMode.SmoothTransformation
            )
            logo.setPixmap(pix)
        hbox.addWidget(logo, alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        # título e subtítulo centralizados
        hbox.addStretch(1)
        title_box = QVBoxLayout()
        title = QLabel("CONTROLE DA QUALIDADE", objectName="Title")
        subtitle = QLabel("Inspeção em Linha", objectName="Subtitle")
        title_box.addWidget(title, alignment=Qt.AlignmentFlag.AlignHCenter)
        title_box.addWidget(subtitle, alignment=Qt.AlignmentFlag.AlignHCenter)
        subtitle.setStyleSheet("QLabel#Subtitle { font-size:17px; font-weight:700; color:#9AA0A6; }")
        hbox.addLayout(title_box)
        hbox.addStretch(1)

        self.btn_logout = QPushButton("Sair da conta")
        self.btn_logout.setProperty("kind", "outline")
        self.btn_logout.setVisible(False)
        self.btn_logout.clicked.connect(self.logout)
        self.btn_logout.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        hbox.addWidget(self.btn_logout, alignment=Qt.AlignmentFlag.AlignRight)

        # -------------------- LAYOUT PRINCIPAL --------------------
        container = QFrame(objectName="Container")
        cbox = QHBoxLayout(container)

        self.left = QFrame(objectName="Side")
        self.left.setMinimumWidth(190)
        self.left.setMaximumWidth(260)
        left_box = QVBoxLayout(self.left)

        self.btn_func = QPushButton("Funcionários"); self.btn_func.setProperty("class", "SideBtn")
        self.btn_acessos = QPushButton("Acessos"); self.btn_acessos.setProperty("class", "SideBtn")
        self.btn_clientes = QPushButton("Clientes"); self.btn_clientes.setProperty("class", "SideBtn")
        self.btn_grupo = QPushButton("Grupo"); self.btn_grupo.setProperty("class", "SideBtn")
        self.btn_analise = QPushButton("Análise"); self.btn_analise.setProperty("class", "SideBtn")
        self.btn_produto = QPushButton("Produto"); self.btn_produto.setProperty("class", "SideBtn")
        self.btn_teste = QPushButton("Teste Qualidade"); self.btn_teste.setProperty("class", "SideBtn")

        for b in [self.btn_func, self.btn_acessos, self.btn_clientes, self.btn_grupo,
                  self.btn_analise, self.btn_produto, self.btn_teste]:
            b.setMinimumHeight(28); b.setMaximumHeight(28)
            b.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            b.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            left_box.addWidget(b)
        left_box.addStretch(1)

        center = QFrame()
        center.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        mid = QVBoxLayout(center)
        self.pages = QStackedWidget()
        self.pages.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        mid.addWidget(self.pages)

        self.right = QFrame(objectName="Side")
        self.right.setMinimumWidth(190)
        self.right.setMaximumWidth(260)
        right_box = QVBoxLayout(self.right)

        self.btn_analise_prod = QPushButton("Análise/Produto"); self.btn_analise_prod.setProperty("class", "SideBtn")
        self.btn_analise_prod.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_analise_prod.clicked.connect(lambda: self.open_page("analise_produto", "Análise/Produto"))

        self.btn_analise_cli  = QPushButton("Análise/Cliente"); self.btn_analise_cli.setProperty("class", "SideBtn")
        self.btn_analise_cli.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_analise_cli.clicked.connect(lambda: self.open_page("analise_cliente", "Análise/Cliente"))

        self.btn_result = QPushButton("Resultado Inspeção"); self.btn_result.setProperty("class", "SideBtn")
        self.btn_cert   = QPushButton("Emite Certificado"); self.btn_cert.setProperty("class", "SideBtn")
        self.btn_print  = QPushButton("Imprime Certificado"); self.btn_print.setProperty("class", "SideBtn")
        self.btn_rel    = QPushButton("Consultas/Relatórios"); self.btn_rel.setProperty("class", "SideBtn")
        self.btn_account= QPushButton("Trocar Senha"); self.btn_account.setProperty("class", "SideBtn")
        self.btn_appearance = QPushButton("Aparência"); self.btn_appearance.setProperty("class", "SideBtn")
        self.btn_update = QPushButton("Atualizar Dados"); self.btn_update.setProperty("class", "SideBtn")

        for b in [self.btn_analise_prod, self.btn_analise_cli, self.btn_result,
                  self.btn_cert, self.btn_print, self.btn_rel, self.btn_account,
                  self.btn_appearance, self.btn_update]:
            b.setMinimumHeight(28); b.setMaximumHeight(28)
            b.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            b.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            right_box.addWidget(b)
        right_box.addStretch(1)

        cbox.addWidget(self.left, 0)
        cbox.addWidget(center, 1)
        cbox.addWidget(self.right, 0)

        self.left.setVisible(False)
        self.right.setVisible(False)

        root_layout.addWidget(header)
        root_layout.addWidget(container)

        qss = Path(__file__).resolve().parent / "style.qss"
        if qss.exists():
            with open(qss, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())

        self.page_dashboard = self._build_dashboard_page()
        self.pages.addWidget(self.page_dashboard)

        # ações laterais
        self.btn_func.clicked.connect     (lambda: self.open_page("funcionarios", "Funcionários"))
        self.btn_acessos.clicked.connect  (lambda: self.open_page("acessos", "Acessos"))
        self.btn_clientes.clicked.connect (lambda: self.open_page("clientes", "Clientes"))
        self.btn_grupo.clicked.connect    (lambda: self.open_page("grupo", "Grupo"))
        self.btn_produto.clicked.connect  (lambda: self.open_page("produto", "Produto"))
        self.btn_analise.clicked.connect  (lambda: self.open_page("analises", "Análise"))
        self.btn_teste.clicked.connect    (lambda: self.open_page("testes", "Teste Qualidade"))
        self.btn_result.clicked.connect   (lambda: self.open_page("inspecoes", "Resultado Inspeção"))
        self.btn_rel.clicked.connect      (lambda: self.open_page("relatorios", "Consultas e Relatórios"))
        self.btn_cert.clicked.connect     (lambda: self.open_page("certificado", "Emissão de Certificado"))
        self.btn_print.clicked.connect    (lambda: self.open_page("impressao_certificados", "Impressão de Certificados"))
        self.btn_account.clicked.connect  (lambda: self.open_page("account", "Trocar Senha"))
        self.btn_appearance.clicked.connect(self._open_font_dialog)
        self.btn_update.clicked.connect   (self._update_data)

        self._build_login_page()
        self._set_menus_enabled(False)

        apply_button_theme(self)
        apply_table_theme(self, editable=True)
        apply_typography_everywhere(self, load_prefs())

        self.showMaximized()

    # -------------------- Dashboard --------------------
    def _find_dashboard_image(self) -> Path | None:
        assets_dir = Path(__file__).resolve().parents[2] / "assets"
        candidates = [
            assets_dir / "enepol_banner.png",
            assets_dir / "enepol_banner.jpg",
            assets_dir / "dashboard_enepol.png",
            assets_dir / "dashboard_enepol.jpg",
            assets_dir / "dashboard.png",
            assets_dir / "dashboard.jpg",
            assets_dir / "home.png",
            assets_dir / "home.jpg",
            assets_dir / "banner.png",
            assets_dir / "banner.jpg",
        ]
        for p in candidates:
            if p.exists():
                return p
        pics = []
        for ext in ("png", "jpg", "jpeg", "webp", "bmp"):
            pics.extend((assets_dir).glob(f"*.{ext}"))
        if pics:
            try:
                pics.sort(key=lambda p: p.stat().st_size, reverse=True)
            except Exception:
                pass
            return pics[0]
        return None

    def _build_dashboard_page(self):
        dash = QFrame()
        vb = QVBoxLayout(dash)
        vb.setContentsMargins(8, 8, 8, 8)
        vb.setSpacing(8)

        bar = QFrame(objectName="PageBar")
        hb = QHBoxLayout(bar)
        lbl = QLabel("Principal", objectName="PageTitle")
        hb.addWidget(lbl); hb.addStretch(1)
        vb.addWidget(bar)

        hero = QFrame(objectName="Card")
        hl = QVBoxLayout(hero)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(0)

        img_path = self._find_dashboard_image()
        if img_path:
            self._hero_img = ScaledImage(str(img_path), min_h=320, parent=hero)
        else:
            self._hero_img = ScaledImage("", min_h=320, parent=hero)

        hl.addWidget(self._hero_img)
        vb.addWidget(hero, 1)
        return dash

    # -------------------- Login --------------------
    def _build_login_page(self):
        self.page_home = QFrame()
        ph = QVBoxLayout(self.page_home)
        ph.setContentsMargins(24, 24, 24, 24)

        form_card = QFrame(objectName="LoginCard")
        form_card.setMaximumWidth(420)
        form_card.setMinimumWidth(320)
        form = QVBoxLayout(form_card)
        form.setSpacing(8)

        lbl_login = QLabel("Login"); lbl_login.setProperty("class", "Field")
        self.cmb_login = QComboBox(); self.cmb_login.setEditable(True)
        self.cmb_login.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self._load_users_for_login()
        self.cmb_login.lineEdit().setPlaceholderText("Digite seu login")

        lbl_senha = QLabel("Senha"); lbl_senha.setProperty("class", "Field")
        self.txt_senha = QLineEdit(); self.txt_senha.setPlaceholderText("Senha")
        self.txt_senha.setEchoMode(QLineEdit.EchoMode.Password)

        form.addWidget(lbl_login); form.addWidget(self.cmb_login)
        form.addSpacing(6)
        form.addWidget(lbl_senha); form.addWidget(self.txt_senha)

        btn_row = QHBoxLayout()
        self.btn_entrar = QPushButton("Entrar"); self.btn_entrar.setProperty("kind", "primary")
        self.btn_entrar.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn_sair = QPushButton("Sair"); btn_sair.setProperty("kind", "outline")
        btn_sair.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn_sair.clicked.connect(self.close)
        btn_row.addStretch(1); btn_row.addWidget(self.btn_entrar); btn_row.addSpacing(8); btn_row.addWidget(btn_sair); btn_row.addStretch(1)

        ph.addStretch(1)
        ph.addWidget(form_card, alignment=Qt.AlignmentFlag.AlignHCenter)
        ph.addSpacing(10)
        ph.addLayout(btn_row)
        ph.addStretch(2)

        self.btn_entrar.clicked.connect(self.on_login)
        self.txt_senha.returnPressed.connect(self.on_login)
        if self.cmb_login.isEditable():
            self.cmb_login.lineEdit().returnPressed.connect(self.on_login)

        self.pages.insertWidget(0, self.page_home)
        self.pages.setCurrentWidget(self.page_home)

    def _load_users_for_login(self):
        self.cmb_login.clear()
        self.cmb_login.lineEdit().setPlaceholderText("Digite seu login")
        cur = self.db.conn.cursor()
        try:
            cur.execute("SELECT login FROM funcionarios WHERE LOWER(login) <> 'admin' ORDER BY login")
            users = [r[0] for r in cur.fetchall()]
        except Exception:
            users = []
        self.cmb_login.addItems(users)

    # -------------------- Páginas --------------------
    def _build_page_widget(self, key: str) -> QWidget:
        # helper para construir com/sem injeção
        def new(widget_cls):
            try:
                return widget_cls(self.db, self.bus, self.services, self.cert_service)
            except TypeError:
                try:
                    return widget_cls(self.db, self.bus, self.services)
                except TypeError:
                    try:
                        return widget_cls(self.db)
                    except TypeError:
                        return widget_cls()

        if key == "funcionarios":
            return FuncionariosWidget(self.db, read_only=not self._is_admin())

        if key == "acessos":
            return AcessosWidget(self.db)

        if key == "clientes":
            return CrudWidget(self.db, "clientes", [
                ("codigo", "Código"),
                ("nome", "Nome"),
                ("cnpj", "CNPJ"),
                ("contato", "Contato"),
                ("observacao", "Observação"),
            ])

        if key == "grupo":
            w = CrudWidget(
                self.db,
                "grupos",
                [
                    ("nome", "Descrição em Português"),
                    ("descricao", "Descrição em Ingles"),
                    ("descricao_es", "Descrição em Espanhol"),
                ],
            )
            try:
                for col in (1, 2):
                    w.table.setItemDelegateForColumn(col, LeftPaddingDelegate(16, w.table))
            except Exception:
                pass
            return w

        if key == "produto":
            return ProdutoWidget(self)

        if key == "analises":
            w = CrudWidget(self.db, "analises", [
                ("codigo",       "Código"),
                ("descricao_pt", "Descrição Português"),
                ("descricao_en", "Descrição Inglês"),
                ("descricao_es", "Descrição Espanhol"),
                ("metodo",       "Método"),
                ("tipo",         "Tipo"),
                ("frequencia",   "Frequência"),
                ("medicao",      "Medição"),
            ])
            try:
                w.table.setColumnWidth(0, 110)
                w.table.setColumnWidth(1, 260)
                w.table.setColumnWidth(2, 230)
                w.table.setColumnWidth(3, 230)
                w.table.setColumnWidth(4, 240)
                w.table.setColumnWidth(5, 120)
                w.table.setColumnWidth(6, 110)
                w.table.setColumnWidth(7, 160)
            except Exception:
                pass
            return w

        if key == "testes":
            return TestesQualidadeWidget(self.db)

        if key == "analise_produto":
            return new(AnaliseProdutoWidget)

        if key == "analise_cliente":
            return new(AnaliseClienteWidget)

        if key == "inspecoes":
            return new(ResultadosInspecaoWidget)

        if key == "impressao_certificados":
            return new(ImpressaoCertificadosWidget)

        if key == "relatorios":
            try:
                return ReportsWidget(self.db, self.bus, self.services)
            except TypeError:
                return ReportsWidget(self.db)

        if key == "certificado":
            return CertificadoWidget(self.db)

        if key == "account":
            w = ChangePasswordWidget(self.db)
            if self.current_user:
                w.set_user(self.current_user)
            return w

        return QWidget()

    def _wrap_page(self, title: str, inner_widget: QWidget) -> QWidget:
        inner_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(inner_widget)
        frame = QFrame()
        vb = QVBoxLayout(frame)
        bar = QFrame(objectName="PageBar")
        hb = QHBoxLayout(bar)
        lbl = QLabel(title, objectName="PageTitle")
        btn_back = QPushButton("Voltar à Principal"); btn_back.setProperty("kind", "outline")
        btn_back.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn_back.clicked.connect(lambda: self.pages.setCurrentWidget(self.page_dashboard))
        hb.addWidget(lbl); hb.addStretch(1); hb.addWidget(btn_back)
        vb.addWidget(bar)
        vb.addWidget(scroll)

        apply_table_theme(frame, editable=True)
        self._decorate_action_buttons(frame)
        return frame

    def open_page(self, key: str, title: str):
        if not self.current_user:
            QMessageBox.information(self, "Atenção", "Faça login para acessar o sistema.")
            return
        if key in ("funcionarios", "acessos") and not self._is_admin():
            QMessageBox.information(self, "Permissão", "Somente o admin pode acessar esta área.")
            return

        if key not in self.page_wrappers:
            inner = self._build_page_widget(key)
            wrapper = self._wrap_page(title, inner)
            self.page_wrappers[key] = wrapper
            self.pages.addWidget(wrapper)

        if key == "account":
            old = self.page_wrappers.pop(key, None)
            if old:
                self.pages.removeWidget(old)
                old.deleteLater()
            inner = self._build_page_widget(key)
            wrapper = self._wrap_page(title, inner)
            self.page_wrappers[key] = wrapper
            self.pages.addWidget(wrapper)

        self.pages.setCurrentWidget(self.page_wrappers[key])
        apply_table_theme(self.page_wrappers[key], editable=True)
        self._decorate_action_buttons(self.page_wrappers[key])
        apply_typography_everywhere(self.page_wrappers[key], load_prefs())

    def _decorate_action_buttons(self, root: QWidget):
        for btn in root.findChildren(QPushButton):
            txt = btn.text().strip().lower()
            if txt in {"novo", "salvar", "adicionar", "inserir", "gravar", "consultar", "importar csv", "importar (access)"}:
                btn.setProperty("kind", "primary" if txt in {"salvar", "consultar"} else "outline")
            if txt in {"excluir", "apagar", "remover", "deletar"}:
                btn.setProperty("kind", "danger")
            btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        apply_button_theme(root)

    # -------------------- Preferências --------------------
    def _open_font_dialog(self):
        dlg = FontPrefsDialog(self, self)
        if dlg.exec():
            pass

    # -------------------- Login / Logout --------------------
    def on_login(self):
        user = self.cmb_login.currentText().strip()
        pwd = self.txt_senha.text().strip()
        if not user or not pwd:
            QMessageBox.information(self, "Atenção", "Informe login e senha.")
            return
        auth = self.db.verify_user(user, pwd)
        if not auth:
            QMessageBox.warning(self, "Acesso negado", "Login ou senha inválidos.")
            return

        self.current_user = auth
        self.ctx.current_user = auth  # << grava no contexto
        self.apply_permissions()
        self.btn_logout.setVisible(True)
        self.left.setVisible(True)
        self.right.setVisible(True)

        self.pages.removeWidget(self.page_home)
        self.page_home.deleteLater()
        self.pages.setCurrentWidget(self.page_dashboard)

        QMessageBox.information(self, "Bem-vindo", f"Acesso liberado para {auth['nome']}.")

        apply_table_theme(self, editable=True)
        apply_button_theme(self)
        apply_typography_everywhere(self, load_prefs())

    def logout(self):
        self.current_user = None
        self.ctx.current_user = None
        self._set_menus_enabled(False)
        self.btn_logout.setVisible(False)
        self.left.setVisible(False)
        self.right.setVisible(False)

        for w in list(self.page_wrappers.values()):
            self.pages.removeWidget(w)
            w.deleteLater()
        self.page_wrappers.clear()
        self._build_login_page()

    # -------------------- Permissões --------------------
    def _is_admin(self) -> bool:
        if not self.current_user:
            return False
        return (self.current_user.get("papel", "") or "").lower() == "admin"

    def apply_permissions(self):
        self._set_menus_enabled(True)
        self.btn_func.setVisible(self._is_admin())
        self.btn_acessos.setVisible(self._is_admin())
        if "funcionarios" in self.page_wrappers:
            old = self.page_wrappers.pop("funcionarios")
            self.pages.removeWidget(old)
            old.deleteLater()

    def _set_menus_enabled(self, enabled: bool):
        for b in [self.btn_func, self.btn_acessos, self.btn_clientes, self.btn_grupo,
                  self.btn_analise, self.btn_produto, self.btn_teste,
                  self.btn_analise_prod, self.btn_analise_cli, self.btn_result,
                  self.btn_cert, self.btn_print, self.btn_rel, self.btn_account,
                  self.btn_appearance, self.btn_update]:
            b.setEnabled(enabled)

    # -------------------- Utilidades --------------------
    def _update_data(self):
        from ..config import DB_PATH
        try:
            self.db.conn.commit()
            QMessageBox.information(self, "Dados", f"Banco pronto em {DB_PATH}")
        except Exception as e:
            QMessageBox.warning(self, "Dados", f"Falha ao atualizar dados. {e}")

    def _ensure_grupos_espanhol_column(self):
        try:
            cur = self.db.conn.cursor()
            cur.execute("PRAGMA table_info(grupos)")
            cols = [r[1].lower() for r in cur.fetchall()]
            if "descricao_es" not in cols and "descricao_espanhol" not in cols:
                cur.execute("ALTER TABLE grupos ADD COLUMN descricao_es TEXT")
                self.db.conn.commit()
        except Exception:
            pass

    def _ensure_analises_codigo_column(self):
        try:
            cur = self.db.conn.cursor()
            cur.execute("PRAGMA table_info(analises)")
            cols = [r[1].lower() for r in cur.fetchall()]
            if "codigo" not in cols:
                cur.execute("ALTER TABLE analises ADD COLUMN codigo TEXT")
                self.db.conn.commit()
        except Exception:
            pass
