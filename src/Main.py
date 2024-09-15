# **************************************************************************************************
# @file Main.py
# @brief Entry point for the SensorVisualizer. 
#
# @project   SensorVisualizer
# @version   1.0
# @date      2024-09-15
# @author    @dabecart
#
# @license
# This project is licensed under the MIT License - see the LICENSE file for details.
# **************************************************************************************************

import sys
from PyQt6.QtWidgets import QApplication
from GUI import GUI
import qdarktheme

import threading
import os

def setHighPriorityOnOS():
    if os.name == 'nt':  
        # Windows
        import win32api, win32process, win32con
        pid = os.getpid()
        handle = win32api.OpenProcess(win32con.PROCESS_ALL_ACCESS, True, pid)
        win32process.SetPriorityClass(handle, win32process.REALTIME_PRIORITY_CLASS)
    else:
        # Unix
        os.nice(-10)  

if __name__ == "__main__":
    threading.Thread(target=setHighPriorityOnOS).start()
    
    # GUI initialization.
    app = QApplication(sys.argv)
    qdarktheme.setup_theme("auto")
    mainWindow = GUI()
    mainWindow.show()

    # Run the program.
    sys.exit(app.exec())