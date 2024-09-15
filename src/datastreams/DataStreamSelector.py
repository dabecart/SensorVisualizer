import os, re
import traceback

from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton, QComboBox, QCheckBox, 
    QFormLayout, QFileDialog, QSpinBox, QLineEdit, QDoubleSpinBox, QMessageBox
)
from widgets.LabeledLineEdit import LabeledLineEdit
from tools.Icons import createThemedIcon

from datastreams.CRC import *
from datastreams.DataStream import EOT, Endianism
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
        self.typeComboBox.currentTextChanged.connect(self.changeConfigFieldsForStreamType)
        
        streamGroupBoxLayout.addWidget(self.typeComboBox)

        streamConfigGroupBox = QGroupBox("Stream configuration")
        self.streamConfigGroupBoxLayout = QHBoxLayout(streamConfigGroupBox)

        eotGroupBox = QGroupBox("End of Transmission/Message")
        eotGroupBoxLayout = QVBoxLayout(eotGroupBox)
        
        self.eotSelectionComboBox = QComboBox()
        self.eotSelectionComboBox.addItems(EOT.getEOTNames())
        self.eotSelectionComboBox.currentTextChanged.connect(self.changeConfigFieldsForEOTType)
        self.eotSelectionComboBox.setCurrentIndex(0)

        self.eotConfigurationLayout = QFormLayout()

        eotGroupBoxLayout.addWidget(self.eotSelectionComboBox)
        eotGroupBoxLayout.addLayout(self.eotConfigurationLayout)

        preprocessorGroupBox = QGroupBox("Preprocessor")
        preprocessorGroupBoxLayout = QFormLayout(preprocessorGroupBox)
        preprocessorCheckbox = QCheckBox()
        preprocessorCheckbox.setChecked(False)
        
        preprocessorFile = LabeledLineEdit()
        preprocessorFile.setEnabled(False)
        preprocessorFile.lineEdit.textChanged.connect(
            lambda: self.validatePreprocessor(preprocessorFile)
        )
        
        preprocessorOpenFileButton = QPushButton()
        preprocessorOpenFileButton.setEnabled(False)
        preprocessorOpenFileButton.setFixedSize(24, 24)
        openFileIcon = createThemedIcon(':file-open')
        openFileIcon.setAssociatedWidget(preprocessorOpenFileButton)
        preprocessorOpenFileButton.clicked.connect(
            lambda: self.openPreprocessorDialog(preprocessorFile)
        )
        
        preprocessorLayout = QHBoxLayout()
        preprocessorLayout.addWidget(preprocessorFile)
        preprocessorLayout.addWidget(preprocessorOpenFileButton)

        preprocessorCheckbox.stateChanged.connect(
            lambda: (
                preprocessorFile.setEnabled(preprocessorCheckbox.isChecked()),
                preprocessorOpenFileButton.setEnabled(preprocessorCheckbox.isChecked())
            )
        )

        preprocessorGroupBoxLayout.addRow("Use preprocessor: ", preprocessorCheckbox)
        preprocessorGroupBoxLayout.addRow("Preprocessor file: ", preprocessorLayout)

        # Add Create and Cancel buttons.
        buttonsLayout = QHBoxLayout()
        self.cancelButton = QPushButton('Cancel')
        self.cancelButton.clicked.connect(self.discardStream)
        self.createButton = QPushButton('Create')
        self.createButton.clicked.connect(self.createStream)

        buttonsLayout.addStretch()
        buttonsLayout.addWidget(self.cancelButton)
        buttonsLayout.addWidget(self.createButton)

        layout.addWidget(streamTypeGroupBox)
        layout.addWidget(streamConfigGroupBox)
        layout.addWidget(eotGroupBox)
        layout.addWidget(preprocessorGroupBox)
        layout.addStretch()
        layout.addLayout(buttonsLayout)

        self.typeComboBox.addItem(createThemedIcon(':stream-serial'), "Serial port")

    def changeConfigFieldsForStreamType(self):
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

    def openPreprocessorDialog(self, preprocessorFile: LabeledLineEdit):
        filepath, _ = QFileDialog.getOpenFileName(self, 'Select preprocessor', '', 'Python Files (*.py);;All Files (*)')
        if filepath:
            preprocessorFile.setText(filepath)
    
    def validatePreprocessor(self, preprocessorFile: LabeledLineEdit):
        filepath = preprocessorFile.text()
        if not os.path.isfile(filepath):
            preprocessorFile.setError("This file does not exist.")
        elif not filepath.endswith('.py'):
            preprocessorFile.setError("This file is not a Python file.")
        else:
            preprocessorFile.clearError()
    
    def changeConfigFieldsForEOTType(self):
        def validateByteString(text: str) -> bytes|None:
            # Substitute all special characters.
            text = text.replace("\n", "\\n")\
                    .replace("\r", "\\r")\
                    .replace("\t", "\\t")\
                    .replace("\b", "\\b")\
                    .replace("\f", "\\f")
            
            # Regex to find all \xHH hexadecimal characters.
            hexCharsRegex = r'\\x[0-9a-fA-F]{2}'

            def hexToBytes(match):
                # Remove the \x.
                hexValue = match.group(0)[2:]
                return bytes([int(hexValue, 16)])

            text = re.sub(hexCharsRegex, lambda match: hexToBytes(match).decode('latin1'), text)
            return text.encode('latin1')

        # Clear the widgets from the streamConfigGroupBoxLayout.
        for i in reversed(range(self.eotConfigurationLayout.count())):
            self.eotConfigurationLayout.itemAt(i).widget().setParent(None)

        # Clear the previous EOT arguments.
        self.currentDataStream._config.eotArgs.clear()

        # Converts from the text on the combo box (from getEOTNames()) to the correspondent EOT 
        # enum.
        eot: EOT = EOT(EOT.getEOTNames().index(self.eotSelectionComboBox.currentText()))
        match eot:
            case EOT.NONE, EOT.CARRIAGE, EOT.RETURN, EOT.CARRIAGE_RETURN:
                pass

            case EOT.FIXED_LENGTH:
                messageLen = QSpinBox()
                messageLen.setMinimum(0)
                messageLen.setValue(10)
                messageLen.valueChanged.connect(
                    lambda: self.setEOTArg("fixedLen", messageLen.value()))
                self.eotConfigurationLayout.addRow("Message fixed byte length:", messageLen)

                self.setEOTArg("fixedLen", 10)

            case EOT.HEADER:
                headerStartBytes = QLineEdit()
                headerStartBytes.textChanged.connect(
                    lambda: self.setEOTArg("headerStartBytes", validateByteString(headerStartBytes.text()))
                )

                headerBytesize = QSpinBox()
                headerBytesize.setMinimum(1)
                headerBytesize.setValue(10)

                lengthIndexInHeader = QSpinBox()
                lengthIndexInHeader.setMinimum(0)
                lengthIndexInHeader.setMaximum(9)
                lengthIndexInHeader.setValue(0)

                lengthFieldBytesize = QSpinBox()
                lengthFieldBytesize.setMinimum(1)
                lengthFieldBytesize.setMaximum(10)
                lengthFieldBytesize.setValue(1)

                headerBytesize.valueChanged.connect(
                    lambda: (
                        self.setEOTArg("headerBytesize", headerBytesize.value()),
                        lengthIndexInHeader.setMaximum(headerBytesize.value() - 1),
                        lengthFieldBytesize.setMaximum(headerBytesize.value() - lengthIndexInHeader.value())
                    )
                )

                lengthIndexInHeader.valueChanged.connect(
                    lambda: (
                        self.setEOTArg("lengthIndexInHeader", lengthIndexInHeader.value()),
                        lengthFieldBytesize.setMaximum(headerBytesize.value() - lengthIndexInHeader.value())
                    )        
                )

                lengthFieldBytesize.valueChanged.connect(
                    lambda: self.setEOTArg("lengthFieldBytesize", lengthFieldBytesize.value()),
                )

                headerIncludedInLength = QCheckBox("")
                headerIncludedInLength.setChecked(True)
                headerIncludedInLength.stateChanged.connect(
                    lambda: self.setEOTArg("headerIncludedInLength", headerIncludedInLength.isChecked()),
                )

                endianism = QComboBox()
                endianism.addItems(["Little endian", "Big endian"])
                endianism.setCurrentIndex(0)
                endianism.currentTextChanged.connect(
                    lambda: self.setEOTArg("endianism", Endianism.BIG if endianism.currentText() == "Big endian" else Endianism.LITTLE)
                )

                self.eotConfigurationLayout.addRow('Header start sequence:',        headerStartBytes)
                self.eotConfigurationLayout.addRow('Header byte length:',           headerBytesize)
                self.eotConfigurationLayout.addRow('"Length" field index:',         lengthIndexInHeader)
                self.eotConfigurationLayout.addRow('"Length" field byte length:',   lengthFieldBytesize)
                self.eotConfigurationLayout.addRow('Header included in length:',    headerIncludedInLength)
                self.eotConfigurationLayout.addRow('Endianism:',                    endianism)

                self.setEOTArg("headerStartBytes",       b'')
                self.setEOTArg("headerBytesize",         10)
                self.setEOTArg("lengthIndexInHeader",    0)
                self.setEOTArg("lengthFieldBytesize",    1)
                self.setEOTArg("headerIncludedInLength", True)
                self.setEOTArg("endianism",              Endianism.LITTLE)

            case EOT.CRC:
                self.setEOTArg('crc', CRC())

                messageLen = QSpinBox()
                messageLen.setMinimum(0)
                messageLen.setValue(10)
                messageLen.valueChanged.connect(
                    lambda: self.setEOTArg("messageLen", messageLen.value()))

                crc = QComboBox()
                crc_width = QComboBox()
                crc_width.addItems(["8", "16", "32", "64"])
                crc_width.currentTextChanged.connect(
                    lambda: self.setCRCArg('width', int(crc_width.currentText()))
                )
                crc_polynomial = QLineEdit()
                crc_polynomial.textChanged.connect(
                    lambda: self.setCRCArg('polynomial', crc_polynomial.text())
                )
                crc_init_value = QLineEdit()
                crc_init_value.textChanged.connect(
                    lambda: self.setCRCArg('init_value', crc_init_value.text())
                )
                crc_final_xor_value = QLineEdit()
                crc_final_xor_value.textChanged.connect(
                    lambda: self.setCRCArg('xor_value', crc_final_xor_value.text())
                )
                crc_reverse_input = QCheckBox("")
                crc_reverse_input.stateChanged.connect(
                    lambda: self.setCRCArg('reverse_input', crc_reverse_input.isChecked())
                )
                crc_reverse_output = QCheckBox("")
                crc_reverse_output.stateChanged.connect(
                    lambda: self.setCRCArg('reverse_output', crc_reverse_output.isChecked())
                )

                crc.currentTextChanged.connect(
                    lambda: self.setCRCFieldsOnTextChange(crc, 
                                                          crc_width,
                                                          crc_polynomial, 
                                                          crc_init_value, 
                                                          crc_final_xor_value, 
                                                          crc_reverse_input, 
                                                          crc_reverse_output)
                )
                crc.addItems(DEFAULT_CRC.keys())
                crc.addItem("Custom CRC...")

                crcIncludedInLength = QCheckBox("")
                crcIncludedInLength.setChecked(True)
                crcIncludedInLength.stateChanged.connect(
                    lambda: self.setEOTArg("crcIncludedInLength", crcIncludedInLength.isChecked()),
                )

                endianism = QComboBox()
                endianism.addItems(["Little endian", "Big endian"])
                endianism.setCurrentIndex(0)
                endianism.currentTextChanged.connect(
                    lambda: self.setEOTArg("endianism", Endianism.BIG if endianism.currentText() == "Big endian" else Endianism.LITTLE)
                )

                self.eotConfigurationLayout.addRow("Message length:", messageLen)
                self.eotConfigurationLayout.addRow('CRC included in length:', crcIncludedInLength)
                self.eotConfigurationLayout.addRow('CRC preset:', crc)
                self.eotConfigurationLayout.addRow('Bit width:', crc_width)
                self.eotConfigurationLayout.addRow('Polynomial:', crc_polynomial)
                self.eotConfigurationLayout.addRow('Initial value:', crc_init_value)
                self.eotConfigurationLayout.addRow('Final XOR value:', crc_final_xor_value)
                self.eotConfigurationLayout.addRow('Reverse input:', crc_reverse_input)
                self.eotConfigurationLayout.addRow('Reverse output:', crc_reverse_output)
                self.eotConfigurationLayout.addRow('Endianism:', endianism)

                self.setEOTArg('messageLen', 10)
                self.setEOTArg('crcIncludedInLength', True)
                self.setEOTArg('endianism', Endianism.LITTLE)

            case EOT.HEADER_CRC:
                self.setEOTArg('crc', CRC())

                headerStartBytes = QLineEdit()
                headerStartBytes.textChanged.connect(
                    lambda: self.setEOTArg("headerStartBytes", validateByteString(headerStartBytes.text()))
                )

                headerBytesize = QSpinBox()
                headerBytesize.setMinimum(1)
                headerBytesize.setValue(10)

                lengthIndexInHeader = QSpinBox()
                lengthIndexInHeader.setMinimum(0)
                lengthIndexInHeader.setMaximum(9)
                lengthIndexInHeader.setValue(0)

                lengthFieldBytesize = QSpinBox()
                lengthFieldBytesize.setMinimum(1)
                lengthFieldBytesize.setMaximum(10)
                lengthFieldBytesize.setValue(1)

                headerBytesize.valueChanged.connect(
                    lambda: (
                        self.setEOTArg("headerBytesize", headerBytesize.value()),
                        lengthIndexInHeader.setMaximum(headerBytesize.value() - 1),
                        lengthFieldBytesize.setMaximum(headerBytesize.value() - lengthIndexInHeader.value())
                    )
                )

                lengthIndexInHeader.valueChanged.connect(
                    lambda: (
                        self.setEOTArg("lengthIndexInHeader", lengthIndexInHeader.value()),
                        lengthFieldBytesize.setMaximum(headerBytesize.value() - lengthIndexInHeader.value())
                    )        
                )

                lengthFieldBytesize.valueChanged.connect(
                    lambda: self.setEOTArg("lengthFieldBytesize", lengthFieldBytesize.value()),
                )

                headerIncludedInLength = QCheckBox("")
                headerIncludedInLength.setChecked(True)
                headerIncludedInLength.stateChanged.connect(
                    lambda: self.setEOTArg("headerIncludedInLength", headerIncludedInLength.isChecked()),
                )

                crcIncludedInLength = QCheckBox("")
                crcIncludedInLength.setChecked(True)
                crcIncludedInLength.stateChanged.connect(
                    lambda: self.setEOTArg("crcIncludedInLength", crcIncludedInLength.isChecked()),
                )

                crc = QComboBox()
                crc_width = QComboBox()
                crc_width.addItems(["8", "16", "32", "64"])
                crc_width.currentTextChanged.connect(
                    lambda: self.setCRCArg('width', int(crc_width.currentText()))
                )
                crc_polynomial = QLineEdit()
                crc_polynomial.textChanged.connect(
                    lambda: self.setCRCArg('polynomial', crc_polynomial.text())
                )
                crc_init_value = QLineEdit()
                crc_init_value.textChanged.connect(
                    lambda: self.setCRCArg('init_value', crc_init_value.text())
                )
                crc_final_xor_value = QLineEdit()
                crc_final_xor_value.textChanged.connect(
                    lambda: self.setCRCArg('xor_value', crc_final_xor_value.text())
                )
                crc_reverse_input = QCheckBox("")
                crc_reverse_input.stateChanged.connect(
                    lambda: self.setCRCArg('reverse_input', crc_reverse_input.isChecked())
                )
                crc_reverse_output = QCheckBox("")
                crc_reverse_output.stateChanged.connect(
                    lambda: self.setCRCArg('reverse_output', crc_reverse_output.isChecked())
                )

                crc.currentTextChanged.connect(
                    lambda: self.setCRCFieldsOnTextChange(crc, 
                                                          crc_width,
                                                          crc_polynomial, 
                                                          crc_init_value, 
                                                          crc_final_xor_value, 
                                                          crc_reverse_input, 
                                                          crc_reverse_output)
                )
                crc.addItems(DEFAULT_CRC.keys())
                crc.addItem("Custom CRC...")

                endianism = QComboBox()
                endianism.addItems(["Little endian", "Big endian"])
                endianism.setCurrentIndex(0)
                endianism.currentTextChanged.connect(
                    lambda: self.setEOTArg("endianism", Endianism.BIG if endianism.currentText() == "Big endian" else Endianism.LITTLE)
                )

                self.eotConfigurationLayout.addRow('Header start sequence:',        headerStartBytes)
                self.eotConfigurationLayout.addRow('Header byte length:',           headerBytesize)
                self.eotConfigurationLayout.addRow('"Length" field index:',         lengthIndexInHeader)
                self.eotConfigurationLayout.addRow('"Length" field byte length:',   lengthFieldBytesize)
                self.eotConfigurationLayout.addRow('Header included in length:',    headerIncludedInLength)
                self.eotConfigurationLayout.addRow('CRC included in length:', crcIncludedInLength)
                self.eotConfigurationLayout.addRow('CRC preset:', crc)
                self.eotConfigurationLayout.addRow('Bit width:', crc_width)
                self.eotConfigurationLayout.addRow('Polynomial:', crc_polynomial)
                self.eotConfigurationLayout.addRow('Initial value:', crc_init_value)
                self.eotConfigurationLayout.addRow('Final XOR value:', crc_final_xor_value)
                self.eotConfigurationLayout.addRow('Reverse input:', crc_reverse_input)
                self.eotConfigurationLayout.addRow('Reverse output:', crc_reverse_output)
                self.eotConfigurationLayout.addRow('Endianism:', endianism)

                self.setEOTArg("headerStartBytes",       b'')
                self.setEOTArg("headerBytesize",         10)
                self.setEOTArg("lengthIndexInHeader",    0)
                self.setEOTArg("lengthFieldBytesize",    1)
                self.setEOTArg("headerIncludedInLength", True)
                self.setEOTArg('crcIncludedInLength',    True)
                self.setEOTArg("endianism",              Endianism.LITTLE)

            case EOT.TIMEOUT:
                automaticTimeout = QCheckBox("")
                automaticTimeout.setChecked(True)

                timeoutSpinBox = QDoubleSpinBox()
                timeoutSpinBox.setMinimum(0)
                timeoutSpinBox.setEnabled(False)

                automaticTimeout.stateChanged.connect(
                    lambda: (
                        self.setEOTArg('timeout', -1.0 if automaticTimeout.isChecked() else timeoutSpinBox.value()),
                        timeoutSpinBox.setEnabled(not automaticTimeout.isChecked())
                    )
                )

                timeoutSpinBox.valueChanged.connect(
                    lambda: self.setEOTArg('timeout', timeoutSpinBox.value())
                )

                self.eotConfigurationLayout.addRow("Automatic timeout:", automaticTimeout)
                self.eotConfigurationLayout.addRow("Timeout (s):", timeoutSpinBox)

                self.setEOTArg("timeout", -1.0)

    def setCRCFieldsOnTextChange(self,
                                 crc: QComboBox,
                                 crc_width: QComboBox,
                                 crc_polynomial: QLineEdit, 
                                 crc_init_value: QLineEdit, 
                                 crc_final_xor_value: QLineEdit, 
                                 crc_reverse_input: QCheckBox, 
                                 crc_reverse_output: QCheckBox):
        if crc.currentText() in DEFAULT_CRC:
            crc_width.setEnabled(False)
            crc_polynomial.setEnabled(False)
            crc_init_value.setEnabled(False)
            crc_final_xor_value.setEnabled(False)
            crc_reverse_input.setEnabled(False)
            crc_reverse_output.setEnabled(False)

            selectedCRC: CRC = DEFAULT_CRC[crc.currentText()]
            crc_width.setCurrentText(str(selectedCRC.width))
            crc_polynomial.setText(hex(selectedCRC.polynomial))
            crc_init_value.setText(hex(selectedCRC.init_value))
            crc_final_xor_value.setText(hex(selectedCRC.final_xor_value))
            crc_reverse_input.setChecked(selectedCRC.reverse_input)
            crc_reverse_output.setChecked(selectedCRC.reverse_output)

            self.setEOTArg('crc', selectedCRC)
        else:
            crc_width.setEnabled(True)
            crc_polynomial.setEnabled(True)
            crc_init_value.setEnabled(True)
            crc_final_xor_value.setEnabled(True)
            crc_reverse_input.setEnabled(True)
            crc_reverse_output.setEnabled(True)

    def setCRCArg(self, crcField: str, value: any):
        if type(value) is str:
            value = value.lower()
            try:
                if value.startswith('0x'):
                    if len(value) <= 2:
                        # User is in the middle of writing the hex value.
                        return
                    # Starting with 0x, Python automatically interprets the str as hex.
                    value = int(value, 0)
                else:
                    value = int(value)
            except ValueError:
                # Do not set the value if it's not valid.
                return

        setattr(self.currentDataStream._config.eotArgs['crc'], crcField, value)

    def setEOTArg(self, field: str, value: any):
        self.currentDataStream._config.eotArgs[field] = value

    def discardStream(self):
        del self.currentDataStream
        self.close()

    def exec(self):
        if super().exec() == QDialog.DialogCode.Accepted:
            return self.currentDataStream
        else:
            return None

    def createStream(self):
        try:
            self.currentDataStream.startStream()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, 'Error creating a data stream', f'Could not create data stream.\n{traceback.format_exc()}')

    def runAction(self, action: str, actionStack: str | None, *args):
            print(f'Action {action} is not defined on DataStreamSelector')