# app/ui/utils/padding_delegate.py
from PyQt6.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem
from PyQt6.QtCore import QRect

class LeftPaddingDelegate(QStyledItemDelegate):
    """Desloca o conteúdo da célula alguns pixels para a direita (apenas visual)."""
    def __init__(self, left: int = 16, parent=None):
        super().__init__(parent)
        self.left = int(left)

    def paint(self, painter, option, index):
        opt = QStyleOptionViewItem(option)
        # reduz a largura e desloca o retângulo de pintura para a direita
        opt.rect = QRect(
            option.rect.left() + self.left,
            option.rect.top(),
            max(0, option.rect.width() - self.left),
            option.rect.height(),
        )
        super().paint(painter, opt, index)
