from dataclasses import dataclass, asdict
from crc import Calculator, Configuration

@dataclass
# Default values of CCITT CRC-8.
class CRC:
    # Bit width.
    width:              int     = 8
    polynomial:         int     = 0x07
    init_value:         int     = 0x00
    final_xor_value:    int     = 0x00
    reverse_input:      bool    = False
    reverse_output:     bool    = False

    # The input must not contain the CRC.
    def checksum(self, input: bytes, inputCRC: int) -> bool:
        calc = Calculator(Configuration(**asdict(self)), optimized=True)
        return calc.verify(input, inputCRC)

# vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
# Some predefined CRC codes.
# vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
CRC_8_CCITT = CRC(
    width=8,
    polynomial=0x07,
    init_value=0x00,
    final_xor_value=0x00,
    reverse_input=False,
    reverse_output=False,
)

CRC_8_SAEJ1850 = CRC(
    width=8,
    polynomial=0x1D,
    init_value=0xFF,
    final_xor_value=0xFF,
    reverse_input=False,
    reverse_output=False,
)

CRC_8_SAEJ1850_ZERO = CRC(
    width=8,
    polynomial=0x1D,
    init_value=0x00,
    final_xor_value=0x00,
    reverse_input=False,
    reverse_output=False,
)

CRC_8_AUTOSAR = CRC(
    width=8,
    polynomial=0x2F,
    init_value=0xFF,
    final_xor_value=0xFF,
    reverse_input=False,
    reverse_output=False,
)

CRC_8_BLUETOOTH = CRC(
    width=8,
    polynomial=0xA7,
    init_value=0x00,
    final_xor_value=0x00,
    reverse_input=True,
    reverse_output=True,
)

CRC_8_MAXIM_DOW = CRC(
    width=8,
    polynomial=0x31,
    init_value=0,
    final_xor_value=0,
    reverse_input=True,
    reverse_output=True,
)

CRC_16_CCITT = CRC(
    width=16,
    polynomial=0x1021,
    init_value=0xFFFF,
    final_xor_value=0x0000,
    reverse_input=False,
    reverse_output=False,
)

CRC_16_XMODEM = CRC(
    width=16,
    polynomial=0x1021,
    init_value=0x0000,
    final_xor_value=0x0000,
    reverse_input=False,
    reverse_output=False,
)

CRC_16_GSM = CRC(
    width=16,
    polynomial=0x1021,
    init_value=0x0000,
    final_xor_value=0xFFFF,
    reverse_input=False,
    reverse_output=False,
)

CRC_16_PROFIBUS = CRC(
    width=16,
    polynomial=0x1DCF,
    init_value=0xFFFF,
    final_xor_value=0xFFFF,
    reverse_input=False,
    reverse_output=False,
)

CRC_16_MODBUS = CRC(
    width=16,
    polynomial=0x8005,
    init_value=0xFFFF,
    final_xor_value=0x0000,
    reverse_input=True,
    reverse_output=True,
)

CRC_16_KERMIT = CRC(
    width=16,
    polynomial=0x1021,
    init_value=0x0000,
    final_xor_value=0x0000,
    reverse_input=True,
    reverse_output=True,
)

CRC_32_CRC32 = CRC(
    width=32,
    polynomial=0x04C11DB7,
    init_value=0xFFFFFFFF,
    final_xor_value=0xFFFFFFFF,
    reverse_input=True,
    reverse_output=True,
)

CRC_32_AUTOSAR = CRC(
    width=32,
    polynomial=0xF4ACFB13,
    init_value=0xFFFFFFFF,
    final_xor_value=0xFFFFFFFF,
    reverse_input=True,
    reverse_output=True,
)

CRC_32_BZIP2 = CRC(
    width=32,
    polynomial=0x04C11DB7,
    init_value=0xFFFFFFFF,
    final_xor_value=0xFFFFFFFF,
    reverse_input=False,
    reverse_output=False,
)

CRC_32_POSIX = CRC(
    width=32,
    polynomial=0x04C11DB7,
    init_value=0x00000000,
    final_xor_value=0xFFFFFFFF,
    reverse_input=False,
    reverse_output=False,
)

CRC_64_ECMA = CRC(
    width=64,
    polynomial=0x42F0E1EBA9EA3693,
    init_value=0x0000000000000000,
    final_xor_value=0x0000000000000000,
    reverse_input=False,
    reverse_output=False,
)