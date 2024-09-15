# **************************************************************************************************
# @file SignalEmitter.py
# @brief Tool to emit signals without having to inherit from QObject a whole class.
#
# @project   SensorVisualizer
# @version   1.0
# @date      2024-09-15
# @author    @dabecart
#
# @license
# This project is licensed under the MIT License - see the LICENSE file for details.
# **************************************************************************************************

from PyQt6.QtCore import pyqtSignal, QObject

class SignalEmitter(QObject):
    signal = pyqtSignal()

    def emit(self):
        self.signal.emit()

    def connect(self, func):
        self.signal.connect(func)
    
    def disconnect(self, func):
        self.signal.disconnect(func)
    
    def disconnectAll(self):
        self.signal.disconnect()