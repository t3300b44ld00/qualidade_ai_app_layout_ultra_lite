
# -*- coding: utf-8 -*-
from ..services.data_service import DataService
from .event_bus import EventBus

class AppContext:
    """Contexto compartilhado do app (serviços + event bus).
    Use: context = AppContext(db)
    """
    def __init__(self, db):
        self.db = db
        self.events = EventBus()
        self.data = DataService(db)
