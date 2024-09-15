import serial.tools
import serial.tools.list_ports

import serial
from dataclasses import dataclass, field

from datastreams.DataStream import *

from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QFormLayout, QComboBox, QCheckBox
)
from widgets.FilterableLineEdit import FilterableIntLineEdit

# Configuration fields for the Serial library.
@dataclass
class HWConfig():
    port:       str     =   ""
    baudrate:   int     =   9600
    bytesize:   int     =   serial.EIGHTBITS
    parity:     int     =   serial.PARITY_NONE
    stopbits:   float   =   serial.STOPBITS_ONE
    xonxoff:    bool    =   False
    rtscts:     bool    =   False
    dsrdtr:     bool    =   False

    # Returns the time for a packet.
    def packetTime(self) -> float:
        outBits = self.bytesize + (self.parity!=serial.PARITY_NONE) + self.stopbits
        return outBits / self.baudrate

@dataclass
class SerialPortStreamConfig():
    hwConfig:   HWConfig        = field(default_factory=lambda: HWConfig())
    eot:        EOT             = EOT.TIMEOUT
    eotArgs:    dict[str,any]   = field(default_factory=lambda: {})

class SerialPortStream(DataStream):
    # Inherited.
    def dataAwaiting(self) -> bool:
        return self._serial.in_waiting > 0

    def _getInputData(self) -> bytearray|None:
        input: bytes = self._serial.read(self._serial.in_waiting)
        return self._processEOT(self._config.eotArgs, input)

    def __init__(self, config: SerialPortStreamConfig) -> None:
        super().__init__()
        
        self._config: SerialPortStreamConfig = config
        # While configuring it, this will be None.
        self._serial: serial.Serial|None = None

        # Definitions of variables needed for different EOT modes.
        if config.eot is EOT.HEADER or config.eot is EOT.HEADER_CRC:
            # It's the start of the message.
            self.headerFound:       bool        = False
            self.currentMsgLength:  int|None    = None
        elif config.eot is EOT.TIMEOUT:
            self.lastTimeHere:      float|None  = None
            self.autoDeltaTime:     float       = self._config.hwConfig.packetTime()

    def __del__(self):
        if type(self._serial) is serial.Serial:
            self._serial.close()

    @classmethod
    def listAllPorts(cls) -> list[str]:
        serialPorts = serial.tools.list_ports.comports()
        return ["{}: {} [{}]".format(port, desc, hwid) for port, desc, hwid in sorted(serialPorts)]
    
    # Inherited.
    def _start(self):
        self.name = "Serial: " + self._config.hwConfig.port

        # It will raise an exception if there's any error.
        self._serial = serial.Serial(**(self._config.hwConfig.__dict__))
            
    # Inherited.
    def addConfigurationFields(self, contentLayout: QVBoxLayout):
        serialLayout = QFormLayout()
        contentLayout.addLayout(serialLayout)

        portNameSelector = QComboBox()
        portNameSelector.currentTextChanged.connect(
            lambda: self.getSerialPortNameFromCombo_(portNameSelector)
        )
        portNameSelector.addItems(self.__class__.listAllPorts())

        baudrateSelector = FilterableIntLineEdit()
        baudrateSelector.setOptions([4800, 9600, 19200, 38400, 57600, 115200, 230400, 460800, 921600])
        baudrateSelector.textChanged.connect(
            lambda: self.getBaudRateFromTextField_(baudrateSelector)
        )
        baudrateSelector.setText("9600")

        bytesizeCombo = QComboBox()
        bytesizeCombo.currentTextChanged.connect(
            lambda: self.getBytesizeFromCombo_(bytesizeCombo)
        )
        bytesizeCombo.addItems(["5", "6", "7", "8"])
        bytesizeCombo.setCurrentIndex(3)

        parityCombo = QComboBox()
        parityCombo.currentTextChanged.connect(
            lambda: self.getParityFromCombo_(parityCombo)
        )
        parityCombo.addItems(["None", "Even", "Odd", "Mark", "Space"])
        parityCombo.setCurrentIndex(0)

        stopbitsCombo = QComboBox()
        stopbitsCombo.currentTextChanged.connect(
            lambda: self.getStopbitsFromCombo_(stopbitsCombo)
        )
        stopbitsCombo.addItems(["1", "1.5", "2"])
        stopbitsCombo.setCurrentIndex(0)

        xonxoffCheckbox = QCheckBox("XON/XOFF")
        xonxoffCheckbox.stateChanged.connect(
            lambda: self.getFlowControlFromCheckbox_xonxoff_(xonxoffCheckbox)
        )
        
        rtsctsCheckbox = QCheckBox("RTS/CTS")
        rtsctsCheckbox.stateChanged.connect(
            lambda: self.getFlowControlFromCheckbox_rtscts_(rtsctsCheckbox)
        )
        
        dsrdtrCheckbox = QCheckBox("DSR/DTR")
        dsrdtrCheckbox.stateChanged.connect(
            lambda: self.getFlowControlFromCheckbox_dsrdtr_(dsrdtrCheckbox)
        )

        serialHwEOTLayout = QHBoxLayout()
        serialHwEOTLayout.addWidget(xonxoffCheckbox)
        serialHwEOTLayout.addWidget(rtsctsCheckbox)
        serialHwEOTLayout.addWidget(dsrdtrCheckbox)

        serialLayout.addRow("Port:", portNameSelector)
        serialLayout.addRow("Baudrate:", baudrateSelector)
        serialLayout.addRow("Byte size:", bytesizeCombo)
        serialLayout.addRow("Parity:", parityCombo)
        serialLayout.addRow("Stop bits:", stopbitsCombo)
        serialLayout.addRow("Flow control:", serialHwEOTLayout)

    def getSerialPortNameFromCombo_(self, comboBox: QComboBox):
        self._config.hwConfig.port = comboBox.currentText().split(':')[0]

    def getBaudRateFromTextField_(self, intLineEdit: FilterableIntLineEdit):
        self._config.hwConfig.baudrate = intLineEdit.getInt()

    def getBytesizeFromCombo_(self, comboBox: QComboBox):
        self._config.hwConfig.bytesize = int(comboBox.currentText())

    def getParityFromCombo_(self, comboBox: QComboBox):
        match comboBox.currentText():
            case "None":    self._config.hwConfig.parity = serial.PARITY_NONE
            case "Even":    self._config.hwConfig.parity = serial.PARITY_EVEN
            case "Odd":     self._config.hwConfig.parity = serial.PARITY_ODD
            case "Mark":    self._config.hwConfig.parity = serial.PARITY_MARK
            case "Space":   self._config.hwConfig.parity = serial.PARITY_SPACE
            case _:         raise Exception("Unidentified parity on Combo in SerialPortStream")

    def getStopbitsFromCombo_(self, comboBox: QComboBox):
        self._config.hwConfig.stopbits = int(comboBox.currentText())

    def getFlowControlFromCheckbox_xonxoff_(self, xonxoff: QCheckBox):
        self._config.hwConfig.xonxoff   = xonxoff.isChecked()

    def getFlowControlFromCheckbox_rtscts_(self, rtscts: QCheckBox):
        self._config.hwConfig.rtscts    = rtscts.isChecked()

    def getFlowControlFromCheckbox_dsrdtr_(self, dsrdtr: QCheckBox):
        self._config.hwConfig.dsrdtr    = dsrdtr.isChecked()
        