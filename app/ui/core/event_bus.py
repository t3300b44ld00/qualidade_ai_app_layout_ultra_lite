from PyQt6.QtCore import QObject, pyqtSignal

class EventBus(QObject):
    # Seleções globais
    productSelected   = pyqtSignal(object)  # product_id
    clientSelected    = pyqtSignal(object)  # client_id

    # Persistências
    analysisProductSaved = pyqtSignal(object)  # product_id
    analysisClientSaved  = pyqtSignal(object)  # client_id
    inspectionSaved      = pyqtSignal(object)  # inspection_id
    certificateIssued    = pyqtSignal(object)  # certificate_id

    # Requisições utilitárias (render/impressão/PDF)
    requestPrint = pyqtSignal(str, str)  # html, title
    requestPdf   = pyqtSignal(str, str)  # html, filepath
