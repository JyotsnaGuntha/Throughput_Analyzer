"""
Protocol frame building and parsing for MCU communication.
Frame format: FE FE FE [COMMAND] [DATA] FE FE FE
"""

START_DELIM = b"\xFE\xFE\xFE"
END_DELIM = b"\xFE\xFE\xFE"
START_COMMAND = 0x50
STOP_COMMAND = 0x51


def build_start_frame() -> bytes:
    """
    Build START frame: FE FE FE 50 FE FE FE
    Signals the MCU to begin continuous data transmission.
    """
    return START_DELIM + bytes([START_COMMAND]) + END_DELIM


def build_stop_frame() -> bytes:
    """
    Build STOP frame: FE FE FE 51 FE FE FE
    Signals the MCU to stop data transmission.
    """
    return START_DELIM + bytes([STOP_COMMAND]) + END_DELIM


def parse_stop_ack(frame: bytes) -> tuple:
    """
    Parse STOP ACK frame: FE FE FE 51 00 FE FE FE
    Returns (message: str, success: bool)

    Validation checks:
    1. Frame length must be 8 bytes
    2. First 3 bytes must be FE FE FE
    3. Last 3 bytes must be FE FE FE
    4. Command byte (frame[3]) must be 0x51
    5. Status byte (frame[4]):
       - 0x00: Success (stopped without errors)
       - non-zero: Error code
    """
    if len(frame) != 8:
        return ("Invalid frame length", False)

    if frame[:3] != START_DELIM or frame[-3:] != END_DELIM:
        return ("Invalid frame delimiters", False)

    if frame[3] != STOP_COMMAND:
        return ("Invalid command byte", False)

    if frame[4] == 0x00:
        return ("Stop ACK received: Success", True)

    return (f"Stop ACK received: Error code {frame[4]:02X}", False)


def is_valid_data_frame(data: bytes) -> bool:
    """Check if received data looks like valid frame(s)."""
    return len(data) > 0
