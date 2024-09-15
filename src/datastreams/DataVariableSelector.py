# **************************************************************************************************
# @file DataVariableSelector.py
# @brief A GUI Dialog to create or select a DataVariable to attach to a widget.
#
# @project   SensorVisualizer
# @version   1.0
# @date      2024-09-15
# @author    @dabecart
#
# @license
# This project is licensed under the MIT License - see the LICENSE file for details.
# **************************************************************************************************

from PyQt6.QtWidgets import QDialog, QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton
from widgets.FilterableLineEdit import FilterableLineEdit
from PyQt6.QtCore import QSize
from tools.Icons import createIcon

from datastreams.DataStream import DataStream
from datastreams.DataStreamSelector import DataStreamSelector
from tools.SignalBlocker import SignalBlocker
from datastreams.DataVariable import DataVariable

class DataVariableSelector(QDialog):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        self.selectedStream: DataStream|None = None

        self.setWindowTitle("Select a new variable")
        layout = QVBoxLayout(self)

        streamGroupBox = QGroupBox("Data stream")
        streamGroupBoxLayout = QHBoxLayout(streamGroupBox)
        self.streamLineEdit = FilterableLineEdit()
        self.streamLineEdit.setStatusTip("Select the data stream.")
        self.streamLineEdit.setPlaceholderText("Add a data stream first...")
        self.streamLineEdit.setFixedHeight(30)
        self.streamLineEdit.setMinimumWidth(200)
        
        self.streamLineEdit.textChanged.connect(self.streamChanged)

        streamNames: list[str] = [stream for stream in DataStream._instances.keys()]
        self.streamLineEdit.setOptions(streamNames)
        self.streamLineEdit.setEnabled(len(streamNames) > 0)

        self.newStreamButton = QPushButton(createIcon(':datasource-add', "green"), "Add new stream")
        self.newStreamButton.setStatusTip('Add a new data stream to the program.')
        self.newStreamButton.setFixedWidth(150)
        self.newStreamButton.setFixedHeight(30)
        self.newStreamButton.setIconSize(QSize(20,20))
        
        self.newStreamButton.clicked.connect(
            lambda: self.runAction('stream-new', 'undo')
        )

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

    def updateVariableLineEdit(self):
        # [stream for stream in DataVariable._instances.keys() if stream.endswith(self.selectedStream.name)]
        
        variableNames: list[str] = list(self.selectedStream.availableVbes)
        # This will automatically update the variables.
        print(variableNames)
        self.variableLineEdit.setOptions(variableNames)

    def streamChanged(self):
        if self.selectedStream is None:
            self.variableLineEdit.setEnabled(False)
            self.variableLineEdit.setPlaceholderText("Select a data stream first...")
        else:
            self.variableLineEdit.setEnabled(True)
            self.variableLineEdit.setPlaceholderText("You may input your own variable...")
            self.updateVariableLineEdit()

            self.selectedStream.newAvailableVbesSignal.connect(
                lambda: self.updateVariableLineEdit()
            )

    def discardVariable(self):
        self.close()

    def createVariable(self):
        self.accept()

    def runAction(self, action: str, actionStack: str | None, *args):
        if action == "stream-new":
            if self.selectedStream is not None:
                self.selectedStream.newAvailableVbesSignal.disconnectAll()

            self.selectedStream = DataStreamSelector(self).exec()

            if self.selectedStream is not None:
                streamNames: list[str] = [stream for stream in DataStream._instances.keys()]

                # Update the list of available streams.
                with SignalBlocker(self.streamLineEdit):
                    self.streamLineEdit.setOptions(streamNames)
                    self.streamLineEdit.setEnabled(len(streamNames) > 0)

                # Setting the text updates the variables on streamChanged().
                self.streamLineEdit.setText(self.selectedStream.name)
        else:
            print(f'Action {action} is not defined on DataVariableSelector')