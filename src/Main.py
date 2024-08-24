import threading
from datastreams.DataListener import dataRoutine

import sys
from PyQt6.QtWidgets import QApplication
from GUI import GUI
import qdarktheme

if __name__ == "__main__":
    # Stream initialization.
    killPill = threading.Event()
    thread = threading.Thread(target=dataRoutine, args=(killPill,))

    # GUI initialization.
    app = QApplication(sys.argv)
    qdarktheme.setup_theme("auto")
    mainWindow = GUI()
    mainWindow.show()

    thread.start()
    execRet = app.exec()
    
    # End the program, send kill signal.
    killPill.set()
    thread.join()
    sys.exit(execRet)