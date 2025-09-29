# Wrapper da aba Acessos. Redireciona para a tela nova igual ao Access.
from app.ui.screens.acessos import AcessosScreen

# Mantém compatibilidade com qualquer import existente
class AcessosList(AcessosScreen):
    pass

class AcessosGrid(AcessosScreen):
    pass

class AcessosView(AcessosScreen):
    pass

class AcessosPage(AcessosScreen):
    pass

class Acessos(AcessosScreen):
    pass

def create_page(*args, **kwargs):
    return AcessosScreen(*args, **kwargs)
