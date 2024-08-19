import sys
from PyQt6.QtWidgets import QApplication
from GUI import GUI
import qdarktheme

if __name__ == "__main__":
    app = QApplication(sys.argv)

    qss = """
    ContainerWidget {
        background-color: transparent;
    }
    """
    qdarktheme.setup_theme("auto", additional_qss=qss)

    mainWindow = GUI()
    mainWindow.show()
    sys.exit(app.exec())
