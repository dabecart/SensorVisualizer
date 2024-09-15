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

from enum import Enum
from datastreams.CRC import CRC

from PyQt6.QtWidgets import QVBoxLayout

# End Of Transmission method.
class EOT(Enum):
    NONE            = 0
    CARRIAGE        = 1
    RETURN          = 2
    CARRIAGE_RETURN = 3
    FIXED_LENGTH    = 4
    HEADER          = 5
    CRC             = 6
    HEADER_CRC      = 7
    TIMEOUT         = 8

    @classmethod
    def getEOTNames(cls) -> list[str]:
        return ["None", 
                "Carriage (\\r)", 
                "Return (\\n)", 
                "Carriage+Return (\\r\\n)",
                "Fixed length",
                "Header",
                "CRC",
                "Header+CRC",
                "Timeout"]

class Endianism(Enum):
    LITTLE          = 1
    BIG             = 2

    def parseInt(self, input: bytes, signed: bool):
        if self is Endianism.LITTLE:
             return int.from_bytes(input, "little", signed)   
        elif self is Endianism.BIG:
             return int.from_bytes(input, "big", signed)   
        else:
            raise Exception("Bad value on Endianism!")            

@dataclass
class EOTFixedLength:
    fixedLen: int   = -1

@dataclass
class EOTHeader:
    # Sequence that indicates the start of a header. If empty, all characters can be a start of 
    # header.
    headerStartBytes:       bytes       = b''
    # Byte count of the header.
    headerBytesize:         int         = -1
    # Where in the header is the field for its length.
    lengthIndexInHeader:    int         = -1
    # How long is the length field in the header.
    lengthFieldBytesize:    int         = -1
    # Does the length field include the header?
    headerIncludedInLength: bool        = True
    endianism:              Endianism   = Endianism.LITTLE

@dataclass
class EOTCRC:
    crc:                    CRC         = CRC()
    messageLen:             int         = -1
    # Does the length field include the CRC bytes?
    crcIncludedInLength:    bool        = True
    endianism:              Endianism   = Endianism.LITTLE

@dataclass
class EOTHeaderCRC:
    # Sequence that indicates the start of a header. If empty, all characters can be a start of 
    # header.
    headerStartBytes:       bytes       = b''
    # Byte count of the header.
    headerBytesize:         int         = -1
    # Where in the header is the field for its length.
    lengthIndexInHeader:    int         = -1
    # How long is the length field in the header.
    lengthFieldBytesize:    int         = -1
    # Does the length field include the header?
    headerIncludedInLength: bool        = True
    # Does the length field include the CRC bytes?
    crcIncludedInLength:    bool        = True
    # The CRC will always be the last characters of the message.
    crc:                    CRC         = CRC()
    endianism:              Endianism   = Endianism.LITTLE

@dataclass
class EOTTimeout:
    # A negative timeout means the timeout is automatically calculated depending on the baudrate.
    timeout: float = -1.0

@dataclass
class DataStream(ABC):
    # Dictionary with all the DataStream instances.
    _instances      : ClassVar[dict[str, DataStream]] = {}

    @staticmethod
    def nameAvailable(name: str) -> bool:
        return name not in DataStream._instances

    preprocessor:   str|None  = None
    name:           str|None  = None
    _inputBuffer:   bytearray = bytearray()

    # This function should return a bytearray of raw data, which may or may not be already 
    # processed.
    @abstractmethod
    def _getInputData(self) -> bytearray|None:
        pass

    # Returns True if there's data awaiting to be processed.
    @abstractmethod
    def dataAwaiting(self) -> bool:
        pass

    @abstractmethod
    def addConfigurationFields(self, contentLayout: QVBoxLayout):
        pass

    # The _start method will initialize the hardware interfaces with its set configuration. It will
    # also set the final name of the stream.
    @abstractmethod
    def _start(self):
        pass

    def startStream(self):
        self._start()

        if self.name is None:
            raise Exception("Cannot set DataStream name to None.")

        if self.name not in self.__class__._instances:
            self.__class__._instances[self.name] = self
        else:
            raise Exception("Trying to add a DataStream with an already used name.")

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
        
    def _trimTillEOTBytes(self, input: bytes, eotBytes: bytes) -> bytearray|None:
        # This method takes into account if input is empty (returns -1) or if eotBytes is empty 
        # (returns 0).
        index = input.find(eotBytes)
        if index != -1:
            # Cut with all the message plus the eotBytes.
            trimPosition = len(self._inputBuffer) + index + len(eotBytes)

            self._inputBuffer.extend(input)
            ret = self._inputBuffer[:trimPosition]
            del self._inputBuffer[:trimPosition]
            return ret
        else:
            self._inputBuffer.extend(input)
            return None

    def _eotCarriage(self, input: bytes) -> bytearray|None:
        return self._trimTillEOTBytes(input, b'\r')

    def _eotReturn(self, input: bytes) -> bytearray|None:
        return self._trimTillEOTBytes(input, b'\n')

    def _eotCarriageReturn(self, input: bytes) -> bytearray|None:
        return self._trimTillEOTBytes(input, b'\r\n')
    
    def _eotFixedLength(self, input: bytes, config: EOTFixedLength) -> bytearray|None:
        fixedLength = config.fixedLen
        if fixedLength <= 0:
            raise Exception(f'The EOTFixedLength of the serial port "{self._config.hwConfig.port}" is not valid.')
        
        self._inputBuffer.extend(input)
        if len(self._inputBuffer) >= fixedLength:
            ret = self._inputBuffer[:fixedLength]
            del self._inputBuffer[:fixedLength]
            return ret
        
    def _eotHeader(self, input: bytes, config: EOTHeader|EOTHeaderCRC) -> bytearray|None:
        if config.headerBytesize <= 0 or config.lengthIndexInHeader < 0 \
           or config.lengthIndexInHeader >= config.headerBytesize \
           or config.lengthFieldBytesize <= 0:
            raise Exception(f'The EOTHeader of the serial port "{self._config.hwConfig.port}" is not valid.')

        if len(input) <= 0: return None

        if not self.headerFound:
            # Currently finding header...
            index = input.find(config.headerStartBytes)
            if index >= 0:
                self.headerFound = True
                # Trim until the header.
                self._inputBuffer.extend(input[index:])
                # Restart the input in case it can enter the next if statement from this call.
                input = b''

        if self.currentMsgLength is None:
            # Header found. Finding length of message in header.
            self._inputBuffer.extend(input)
            # Restart the input in case it can enter the next if statement from this call.
            input = b''

            if len(self._inputBuffer) >= config.headerBytesize:
                # Enough bytes to parse the header.
                self.currentMsgLength = config.endianism(
                    self._inputBuffer[
                        config.lengthIndexInHeader:
                        config.lengthIndexInHeader+config.lengthFieldBytesize])
                if not config.headerIncludedInLength:
                    # Add the header length to the message length.
                    self.currentMsgLength += config.headerBytesize
                if type(config) is EOTHeaderCRC and not config.crcIncludedInLength:
                    # Add the CRC length to the message length.
                    self.currentMsgLength += config.crc.width // 8
        
        if self.currentMsgLength is not None:
            # Read bytes until the length of the buffer is greater or equal to the currentMsgLength.
            self._inputBuffer.extend(input)
            # Restart the input in case it can enter the next if statement from this call.
            input = b''

            if len(self._inputBuffer) >= self.currentMsgLength:
                ret = self._inputBuffer[:self.currentMsgLength]
                
                # Restart buffer but keeping the new message bytes.
                del self._inputBuffer[:self.currentMsgLength]
                self.headerFound = False
                self.currentMsgLength = None
                return ret

        return None
    
    def _eotCRC(self, input: bytes, config: EOTCRC|EOTHeaderCRC) -> bytearray|None:
        crcBytesize = config.crc.width // 8
        if len(input) < crcBytesize:
            return None 

        if type(config) is EOTCRC:
            fixedLength = config.messageLen
            if fixedLength <= 0:
                raise Exception(f'The EOTFixedLength of the serial port "{self._config.hwConfig.port}" is not valid.')
            if not config.crcIncludedInLength:
                fixedLength += crcBytesize

            self._inputBuffer.extend(input)
            if len(self._inputBuffer) >= fixedLength:
                input = self._inputBuffer[:fixedLength]
                del self._inputBuffer[:fixedLength]
            else:
                return None

        input = input[:-crcBytesize]
        inputCrc = config.endianism.parseInt(input[-crcBytesize:], False)
        if config.crc.checksum(input, inputCrc):
            return bytearray(input)
        else:
            return None
        
    def _eotTimeout(self, input: bytes, config: EOTTimeout) -> bytearray|None:
        self._inputBuffer.extend(input)
        if self.lastTimeHere is None:
            self.lastTimeHere = perf_counter()
        else:
            if len(input) <= 0:
                # No data has arrived.
                delta = perf_counter() - self.lastTimeHere
                if config.timeout < 0:
                    # Auto timeout based on the serial port.
                    deltaLimit = self.autoDeltaTime
                else:
                    deltaLimit = config.timeout
                
                if delta >= deltaLimit:
                    # Timeout! 
                    ret = self._inputBuffer[:]
                    # Restart the timer and clear the buffer.
                    self.lastTimeHere = None
                    self._inputBuffer.clear()
                    return ret
            else:
                # Restart the timer.
                self.lastTimeHere = perf_counter()
        
        return None

    def _processEOT(self, eotArgs: dict[str,any], input: bytes) -> bytearray|None:
        match self._config.eot:
            case EOT.CARRIAGE:
                return self._eotCarriage(input)

            case EOT.RETURN:
                return self._eotReturn(input)

            case EOT.CARRIAGE_RETURN:
                return self._eotCarriageReturn(input)

            case EOT.FIXED_LENGTH:
                config = EOTFixedLength(**eotArgs)
                return self._eotFixedLength(input, config)

            case EOT.HEADER:
                config = EOTHeader(**eotArgs)
                return self._eotHeader(input, config)
            
            case EOT.CRC:
                config = EOTCRC(**eotArgs)
                return self._eotCRC(input, config)
            
            case EOT.HEADER_CRC:
                config = EOTHeaderCRC(**eotArgs)
                header = self._eotHeader(input, config)
                if header is None:
                    return None
                return self._eotCRC(header, config)

            case EOT.TIMEOUT:
                config = EOTTimeout(**eotArgs)
                return self._eotTimeout(input, config)
            case _:
                raise Exception(f'Wrong EOT type in _processEOT()')
        