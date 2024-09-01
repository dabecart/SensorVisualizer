# To type DataStream inside _instances.
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import ClassVar

import shlex, os, subprocess
from time import perf_counter
from datetime import datetime
import re
from collections import defaultdict
from base64 import b64decode

from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton, QComboBox, QCheckBox, 
    QFormLayout, QFileDialog
)
from widgets.LabeledLineEdit import LabeledLineEdit
from tools.Icons import createIcon

@dataclass
class DataStream(ABC):
    # Dictionary with all the DataStream instances.
    _instances      : ClassVar[dict[str, DataStream]] = {}

    @staticmethod
    def nameAvailable(name: str) -> bool:
        return name not in DataStream._instances

    preprocessor   : str|None  = None
    name           : str|None  = None

    def __post_init__(self):
        if self.name is None:
            raise Exception("Cannot set DataStream name to None.")

        if self.name not in self.__class__._instances:
            self.__class__._instances[self.name] = self
        else:
            raise Exception("Trying to add a DataStream with an already used name.")

    # This function should return a bytearray of raw data, which may or may not be already 
    # processed.
    @abstractmethod
    def _getInputData(self) -> bytearray|None:
        pass

    # Returns True if there's data awaiting to be processed.
    @abstractmethod
    def dataAwaiting(self) -> bool:
        pass

    def getDataFields(self) -> dict[str, any]|None:
        # Fetch the input data from the source.
        input: bytearray|None = self._getInputData()

        # No data to process.
        if input is None:
            return None

        # Call the preprocessor if any.
        if self.preprocessor is not None:
            processOutput = self._executeCommand(self.preprocessor + ' "' + input + '"', None)
            input = processOutput.get("output", input)

        # Final filter: input must be an UTF-8 string by this point.
        if type(input) is bytearray or type(input) is bytes:
            input = input.decode("utf-8")

        # Parse the input as a dictionary.
        return self._parseDict(input)

    def _executeCommand(self, cmd: str, cwd: str|None) -> dict[str, any]:
        commandArgs = shlex.split(cmd)
        # So that the windowed application doesn't open a terminal to run the code on Windows (nt).
        # Taken from here:
        # https://code.activestate.com/recipes/409002-launching-a-subprocess-without-a-console-window/
        
        tOfExec = datetime.now().strftime("%d/%m/%Y %H:%M:%S.%f")
        if os.name == 'nt':
            startupInfo = subprocess.STARTUPINFO()
            startupInfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            startTime = perf_counter()
            runResult = subprocess.run(commandArgs,
                                    stdout   = subprocess.PIPE, 
                                    stderr   = subprocess.PIPE,
                                    cwd      = cwd,
                                    startupinfo = startupInfo)
            executionTime = perf_counter() - startTime
        else:
            startTime = perf_counter()
            runResult = subprocess.run(commandArgs,
                                    stdout   = subprocess.PIPE, 
                                    stderr   = subprocess.PIPE,
                                    cwd      = cwd)
            executionTime = perf_counter() - startTime

        # Taken from here: 
        # https://stackoverflow.com/questions/24849998/how-to-catch-exception-output-from-python-subprocess-check-output
        if runResult.stderr:
            raise subprocess.CalledProcessError(
                returncode = runResult.returncode,
                cmd = runResult.args,
                stderr = runResult.stderr
            )
        
        return {"output"        : runResult.stdout.decode('utf-8'),
                "return"        : runResult.returncode,
                "execDelta"     : executionTime,
                "execTime"      : tOfExec}
    
    def _parseDict(self, input: str) -> dict[str, any]:
        # Substitute all special characters.
        input = input.replace("\n", "\\n")\
                     .replace("\r", "\\r")\
                     .replace("\t", "\\t")\
                     .replace("\b", "\\b")\
                     .replace("\f", "\\f")

        # Regex: starts with {, ends with }
        dictRegex = r'\{([^{}]*)\}'
        dicts = re.findall(dictRegex, input)
        
        # Initialize a defaultdict to handle multiple values for the same key.
        resultDict = defaultdict(list)
        
        dictStr: str
        for dictStr in dicts:
            # Regex to match key-value pairs ->  name : value,
            keyValueRegex = r'(\w+)\s*:\s*(.+?)(?=,\s*\w+\s*:|$)'
            matches = re.findall(keyValueRegex, dictStr)

            key: str
            value: str
            for key, value in matches:
                # Convert value to the appropriate type.
                if value.isdigit():
                    value = int(value)
                else:
                    try:
                        value = float(value)
                    except ValueError:
                        # Remove the trailing '' and "".
                        if (value.startswith('b"') and value.endswith('"')) or \
                        (value.startswith("b'") and value.endswith("'")):
                            # Remove the head and tail.
                            value = value[2:-1]
                            value = b64decode(value)
                        else:
                            value = value.strip('\'"')
                            # Reconvert again the special characters.
                            value = value.replace("\\n", "\n")\
                                        .replace("\\r", "\r")\
                                        .replace("\\t", "\t")\
                                        .replace("\\b", "\b")\
                                        .replace("\\f", "\f")

                # Append value to the list of values for this key.
                resultDict[key].append(value)

            # Convert lists with a single item back to a single value.
            for key in resultDict:
                if len(resultDict[key]) == 1:
                    resultDict[key] = resultDict[key][0]

            return dict(resultDict)
        
class DataStreamSelector(QDialog):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        self.setWindowTitle("Create a new data stream")
        layout = QVBoxLayout(self)

        streamTypeGroupBox = QGroupBox("Stream type")
        streamGroupBoxLayout = QHBoxLayout(streamTypeGroupBox)
        self.typeComboBox = QComboBox()
        self.typeComboBox.setStatusTip("Select the data stream type.")
        self.typeComboBox.setFixedHeight(30)
        self.typeComboBox.setMinimumContentsLength(50)

        streamGroupBoxLayout.addWidget(self.typeComboBox)

        streamConfigGroupBox = QGroupBox("Stream configuration")
        streamConfigGroupBoxLayout = QHBoxLayout(streamConfigGroupBox)

        preprocessorGroupBox = QGroupBox("Preprocessor")
        preprocessorGroupBoxLayout = QFormLayout(preprocessorGroupBox)
        self.preprocessorCheckbox = QCheckBox()
        self.preprocessorCheckbox.setChecked(False)
        
        preprocessorLayout = QHBoxLayout()
        self.preprocessorFile = LabeledLineEdit()
        self.preprocessorFile.lineEdit.textChanged.connect(self.validatePreprocessor)
        
        self.preprocessorOpenFileButton = QPushButton()
        self.preprocessorOpenFileButton.setFixedSize(24, 24)
        openFileIcon = createIcon(':file-open', self.parent)
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
        layout.addStretch()
        layout.addLayout(buttonsLayout)

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

