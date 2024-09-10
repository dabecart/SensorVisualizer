import os

from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton, QComboBox, QCheckBox, 
    QFormLayout, QFileDialog
)
from widgets.LabeledLineEdit import LabeledLineEdit
from tools.Icons import createThemedIcon

from datastreams.SerialPortStream import SerialPortStream, SerialPortStreamConfig

class DataStreamSelector(QDialog):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        self.setWindowTitle("Create a new data stream")
        layout = QVBoxLayout(self)

        self.currentDataStream: SerialPortStream|None = None

        streamTypeGroupBox = QGroupBox("Stream type")
        streamGroupBoxLayout = QHBoxLayout(streamTypeGroupBox)
        self.typeComboBox = QComboBox()
        self.typeComboBox.setStatusTip("Select the data stream type.")
        self.typeComboBox.setFixedHeight(30)
        self.typeComboBox.setMinimumContentsLength(50)
        self.typeComboBox.currentTextChanged.connect(self.addConfigFieldsForDataStream)

        streamGroupBoxLayout.addWidget(self.typeComboBox)

        streamConfigGroupBox = QGroupBox("Stream configuration")
        self.streamConfigGroupBoxLayout = QHBoxLayout(streamConfigGroupBox)

        preprocessorGroupBox = QGroupBox("Preprocessor")
        preprocessorGroupBoxLayout = QFormLayout(preprocessorGroupBox)
        self.preprocessorCheckbox = QCheckBox()
        self.preprocessorCheckbox.setChecked(False)
        
        preprocessorLayout = QHBoxLayout()
        self.preprocessorFile = LabeledLineEdit()
        self.preprocessorFile.lineEdit.textChanged.connect(self.validatePreprocessor)
        
        self.preprocessorOpenFileButton = QPushButton()
        self.preprocessorOpenFileButton.setFixedSize(24, 24)
        openFileIcon = createThemedIcon(':file-open')
        openFileIcon.setAssociatedWidget(self.preprocessorOpenFileButton)
        self.preprocessorOpenFileButton.clicked.connect(self.openPreprocessorDialog)
        layout.addWidget(self.preprocessorOpenFileButton)
        
        preprocessorLayout.addWidget(self.preprocessorFile)
        preprocessorLayout.addWidget(self.preprocessorOpenFileButton)

        preprocessorGroupBoxLayout.addRow("Use preprocessor: ", self.preprocessorCheckbox)
        preprocessorGroupBoxLayout.addRow("Preprocessor file: ", preprocessorLayout)

        # Add Create and Cancel buttons.
        buttonsLayout = QHBoxLayout()
        self.cancelButton = QPushButton('Cancel')
        self.cancelButton.clicked.connect(self.discardVariable)
        self.createButton = QPushButton('Create')
        self.createButton.clicked.connect(self.createVariable)

        buttonsLayout.addStretch()
        buttonsLayout.addWidget(self.cancelButton)
        buttonsLayout.addWidget(self.createButton)

        layout.addWidget(streamTypeGroupBox)
        layout.addWidget(streamConfigGroupBox)
        layout.addWidget(preprocessorGroupBox)
        layout.addStretch()
        layout.addLayout(buttonsLayout)

        self.typeComboBox.addItem(createThemedIcon(':stream-serial'), "Serial port")

    def addConfigFieldsForDataStream(self):
        # Clear the widgets from the streamConfigGroupBoxLayout.
        for i in reversed(range(self.streamConfigGroupBoxLayout.count())):
            self.streamConfigGroupBoxLayout.itemAt(i).widget().setParent(None)

        # For each type of data stream, create a "dummy" instance and call its addConfigurationFields
        # to add their respective items to the GUI to configure them.
        match self.typeComboBox.currentText():
            case 'Serial port':
                self.currentDataStream = SerialPortStream(SerialPortStreamConfig())
            case _:
                self.currentDataStream = None
                print(f"Cannot add config to unexpected data stream type {self.typeComboBox.currentText()} in DataStreamSelector")    
        
        if self.currentDataStream is not None:
            self.currentDataStream.addConfigurationFields(self.streamConfigGroupBoxLayout)

    def openPreprocessorDialog(self):
        filepath, _ = QFileDialog.getOpenFileName(self, 'Select preprocessor', '', 'Python Files (*.py);;All Files (*)')
        if filepath:
            self.preprocessorFile.setText(filepath)
    
    def validatePreprocessor(self):
        filepath = self.preprocessorFile.text()
        if not os.path.isfile(filepath):
            self.preprocessorFile.setError("This file does not exist.")
        elif not filepath.endswith('.py'):
            self.preprocessorFile.setError("This file is not a Python file.")
        else:
            self.preprocessorFile.clearError()
    
    def discardVariable(self):
        self.close()

    def createVariable(self):
        self.accept()

    def runAction(self, action: str, actionStack: str | None, *args):
            print(f'Action {action} is not defined on DataStreamSelector')