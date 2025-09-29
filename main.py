from __future__ import annotations
import sys
from PyQt6.QtWidgets import QApplication
from .ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()  # MainWindow já chama showMaximized() internamente
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
