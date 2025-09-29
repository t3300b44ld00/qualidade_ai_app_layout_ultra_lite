
# -*- coding: utf-8 -*-
"""Pequeno barramento de eventos in-process.
Telas podem publicar/assinar eventos para sincronizar dados.
"""
from collections import defaultdict
from typing import Callable, Dict, List

class EventBus:
    def __init__(self) -> None:
        self._subs: Dict[str, List[Callable]] = defaultdict(list)

    def subscribe(self, event: str, callback: Callable) -> None:
        if callback not in self._subs[event]:
            self._subs[event].append(callback)

    def publish(self, event: str, **payload) -> None:
        for cb in list(self._subs.get(event, [])):
            try:
                cb(**payload)
            except Exception:
                # Não derruba o app se um subscriber falhar
                import traceback
                traceback.print_exc()
