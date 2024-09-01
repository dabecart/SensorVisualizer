from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, ClassVar
from collections import deque
from time import time

from PyQt6.QtWidgets import QDialog, QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton
from widgets.FilterableLineEdit import FilterableLineEdit
from PyQt6.QtCore import QSize
from tools.Icons import createIcon

from datastreams.DataStream import DataStream, DataStreamSelector

@dataclass
class DataVariable():
    # A data variable is keyed by its name and source.
    _instances: ClassVar[dict[str, DataVariable]]       = {}

    @staticmethod
    def getVariable(vbeName: str, sourceName: str) -> DataVariable|None:
        keyName: str = DataVariable._generateKeyName(vbeName, sourceName)
        return DataVariable._instances.get(keyName, None)

    _MAX_RECORD_LENGTH: ClassVar[int]                   = 100

    # Name of the variable.
    name:       str|None                                = None
    # Name of the source of this variable.
    source:     str|None                                = None
    # Type of the variable.
    varType:    type|None                               = None
    # The last sent value.
    _value:     any|None                                = None
    # FIFO list with all the last _MAX_RECORD_LENGTH values.
    lastValues: deque[any|None]                         = deque(maxlen=_MAX_RECORD_LENGTH)
    # Store the times the lastValues were received.
    times:      deque[float]                            = deque(maxlen=_MAX_RECORD_LENGTH)
    # List of functions that update the widget associated with this variable.
    hooks:      list[Callable[[DataVariable], None]]    = field(default_factory = lambda: [])

    def __post_init__(self):
        if self.keyName in DataVariable._instances:
            raise Exception(f"There is a duplicated DataVariable: {self.keyName}")

        DataVariable._instances[self.keyName] = self

    @property
    def value(self) -> any|None:
        return self._value
    
    @value.setter
    def value(self, newVal: any|None):
        # Try to cast the new value if (type) is not None.
        if self.source is not None:
            newVal = self.source(newVal)

        # Update values.
        self._value = newVal
        self.lastValues.append(newVal)
        self.times.append(time())

        # Call the hooks.
        for hook in self.hooks:
            hook(self)

    @property
    def keyName(self) -> str:
        return DataVariable._generateKeyName(self.name, self.source)
    
    @staticmethod
    def _generateKeyName(vbeName: str, sourceName: str) -> str:
        return vbeName + "@" + sourceName
    
class DataVariableSelector(QDialog):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        self.setWindowTitle("Select a new variable")
        layout = QVBoxLayout(self)

        streamGroupBox = QGroupBox("Data stream")
        streamGroupBoxLayout = QHBoxLayout(streamGroupBox)
        self.streamLineEdit = FilterableLineEdit()
        self.streamLineEdit.setStatusTip("Select the data stream.")
        self.streamLineEdit.setPlaceholderText("Add a data stream first...")
        self.streamLineEdit.setFixedHeight(30)
        self.streamLineEdit.setMinimumWidth(200)

        streamNames: list[str] = [stream for stream in DataStream._instances.keys()]
        self.streamLineEdit.setOptions(streamNames)
        self.streamLineEdit.textChanged.connect(self.streamChanged)

        self.newStreamButton = QPushButton(createIcon(':datasource-add', "green"), "Add new stream")
        self.newStreamButton.setStatusTip('Add a new data stream to the program.')
        self.newStreamButton.clicked.connect(lambda: self.runAction('stream-new', 'undo'))
        self.newStreamButton.setFixedWidth(150)
        self.newStreamButton.setFixedHeight(30)
        self.newStreamButton.setIconSize(QSize(20,20))

        streamGroupBoxLayout.addWidget(self.streamLineEdit)
        streamGroupBoxLayout.addWidget(self.newStreamButton)

        variableGroupBox = QGroupBox("Variable")
        variableGroupBoxLayout = QHBoxLayout(variableGroupBox)
        self.variableLineEdit = FilterableLineEdit()
        self.variableLineEdit.setStatusTip("Select the variable's name.")
        self.variableLineEdit.setPlaceholderText("Select a data stream first...")
        self.variableLineEdit.setFixedHeight(30)
        self.variableLineEdit.setMinimumWidth(200)
        self.variableLineEdit.setEnabled(False)

        variableGroupBoxLayout.addWidget(self.variableLineEdit)

        # Add Create and Cancel buttons.
        buttonsLayout = QHBoxLayout()
        self.cancelButton = QPushButton('Cancel')
        self.cancelButton.clicked.connect(self.discardVariable)
        self.createButton = QPushButton('Create')
        self.createButton.clicked.connect(self.createVariable)

        buttonsLayout.addStretch()
        buttonsLayout.addWidget(self.cancelButton)
        buttonsLayout.addWidget(self.createButton)

        layout.addWidget(streamGroupBox)
        layout.addWidget(variableGroupBox)
        layout.addStretch()
        layout.addLayout(buttonsLayout)

    def streamChanged(self, sourceName: str):
        if sourceName in DataStream._instances:
            self.variableLineEdit.setEnabled(True)
            variableNames: list[str] =  \
                [stream for stream in DataVariable._instances.keys() if stream.endswith(sourceName)]
            self.variableLineEdit.setOptions(variableNames)

    def discardVariable(self):
        self.close()

    def createVariable(self):
        self.accept()

    def runAction(self, action: str, actionStack: str | None, *args):
        if action == "stream-new":
            DataStreamSelector(self).exec()
        elif action == "stream-change":
            pass
        else:
            print(f'Action {action} is not defined on DataVariableSelector')

