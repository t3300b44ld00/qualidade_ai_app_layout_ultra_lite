
    def apply_permissions(self):
        # chamada original já definia admin e limpava cache de páginas
        self._perms_cache = self.db.get_permissions(self.current_user["id"]) if self.current_user else {}
        self._enforce_menu_permissions()

    def _enforce_menu_permissions(self):
        # Admin vê tudo
        if self._is_admin():
            for b in [self.btn_func, self.btn_acessos, self.btn_clientes, self.btn_grupo,
                      self.btn_analise, self.btn_produto, self.btn_teste, self.btn_analise_prod,
                      self.btn_analise_cli, self.btn_result, self.btn_cert, self.btn_print,
                      self.btn_rel, self.btn_account, self.btn_update]:
                b.setEnabled(True)
                b.setVisible(True)
            return

        def allowed(code): 
            return bool(self._perms_cache.get(code, 0))

        # Visibilidade por código
        self.btn_func.setVisible(allowed("func"))
        self.btn_clientes.setVisible(allowed("cli"))
        self.btn_grupo.setVisible(allowed("fab"))
        self.btn_analise.setVisible(allowed("anal"))
        self.btn_produto.setVisible(allowed("prod"))
        self.btn_teste.setVisible(allowed("res"))
        self.btn_analise_prod.setVisible(allowed("an_prod"))
        self.btn_analise_cli.setVisible(allowed("an_cli"))
        self.btn_result.setVisible(allowed("reg"))
        self.btn_cert.setVisible(allowed("cert_emit"))
        self.btn_print.setVisible(allowed("cert_print"))
        self.btn_rel.setVisible(allowed("rel"))
        # Acessos fica oculto para não-admin
        self.btn_acessos.setVisible(False)
        # Conta e Atualizar ficam visíveis para todos
        self.btn_account.setVisible(True)
        self.btn_update.setVisible(True)
