from DataStream import DataStream
from enum import Enum
import serial
from dataclasses import dataclass, asdict
from datastreams.CRC import CRC
from time import perf_counter

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

# Serial Port End Of Transmission method.
class EOT(Enum):
    CARRIAGE        = 1
    RETURN          = 2
    CARRIAGE_RETURN = 3
    FIXED_LENGTH    = 4
    HEADER          = 5
    CRC             = 6
    HEADER_CRC      = 7
    TIMEOUT         = 8

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
class SerialPortStreamConfig():
    hwConfig:   HWConfig        = HWConfig()
    eot:        EOT             = EOT.TIMEOUT
    eotArgs:    dict[str,any]   = {}

class SerialPortStream(DataStream):
    _inputBuffer: bytearray = bytearray()

    def dataAwaiting(self) -> bool:
        return self._serial.in_waiting > 0

    def _getInputData(self) -> str|None:
        input: bytes = self._serial.read(self._serial.in_waiting)
        match self._config.eot:
            case EOT.CARRIAGE:
                return self._eotCarriage(input)

            case EOT.RETURN:
                return self._eotReturn(input)

            case EOT.CARRIAGE_RETURN:
                return self._eotCarriageReturn(input)

            case EOT.FIXED_LENGTH:
                config = EOTFixedLength(**self._config.eotArgs)
                return self._eotFixedLength(input, config)

            case EOT.HEADER:
                config = EOTHeader(**self._config.eotArgs)
                return self._eotHeader(input, config)
            
            case EOT.CRC:
                config = EOTCRC(**self._config.eotArgs)
                return self._eotCRC(input, config)
            
            case EOT.HEADER_CRC:
                config = EOTHeaderCRC(**self._config.eotArgs)
                header = self._eotHeader(input, config)
                if header is None:
                    return None
                return self._eotCRC(header, config)

            case EOT.TIMEOUT:
                config = EOTTimeout(**self._config.eotArgs)
                return self._eotTimeout(input, config)
            
            case _:
                raise Exception(f'Wrong EOT type in the serial port "{self._config.hwConfig.port}".')
        
    def __init__(self, config: SerialPortStreamConfig) -> None:
        self._config = config

        # Definitions of variables needed for different EOT modes.
        if config.eot is EOT.HEADER or config.eot is EOT.HEADER_CRC:
            # It's the start of the message.
            self.headerFound:       bool        = False
            self.currentMsgLength:  int|None    = None
        elif config.eot is EOT.TIMEOUT:
            self.lastTimeHere:      float|None  = None
            self.autoDeltaTime:     float       = self._config.hwConfig.packetTime()

        self._serial = serial.Serial(**config.hwConfig)
        self._serial.open()

    def __del__(self):
        self._serial.close()

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
