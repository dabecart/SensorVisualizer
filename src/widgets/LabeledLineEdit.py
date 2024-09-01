from PyQt6.QtWidgets import (
    QWidget, QLineEdit, QLabel, QHBoxLayout)
from PyQt6.QtCore import pyqtSignal

class LabeledLineEdit(QWidget):
    def __init__(self, label_text="", parent=None, validator=None):
        super().__init__(parent)
        
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.lineEdit = QLineEdit(self)
        if validator is not None:
            self.lineEdit.setValidator(validator)

        self.errorLabel = QLabel("", self)
        self.errorLabel.setStyleSheet("color: red; margin: 0px;")
        
        self.layout.addWidget(self.lineEdit)
        self.layout.addWidget(self.errorLabel)
        self.setLayout(self.layout)

        # Hide error label initially
        self.errorLabel.hide()  

    def setError(self, error_text):
        self.lineEdit.setStyleSheet("background-color: red;")
        self.errorLabel.setText(error_text)
        self.errorLabel.show()

    def clearError(self):
        self.lineEdit.setStyleSheet("")
        self.errorLabel.hide()

    def text(self):
        return self.lineEdit.text()

    def setText(self, text):
        self.lineEdit.setText(text)

    def textChanged(self) -> pyqtSignal:
        return self.lineEdit.textChanged