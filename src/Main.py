import sys
from PyQt6.QtWidgets import QApplication
from GUI import GUI
import qdarktheme

if __name__ == "__main__":
    app = QApplication(sys.argv)

    qdarktheme.setup_theme("auto")

    mainWindow = GUI()
    mainWindow.show()
    sys.exit(app.exec())
