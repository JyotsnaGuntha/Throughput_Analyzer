"""
Protocol summary:
- Start frame: FE FE FE 50 FE FE FE
- Stop frame: FE FE FE 51 FE FE FE
- Stop ACK frame: FE FE FE 51 00 FE FE FE

ACK parser checks:
1. First 3 bytes and last 3 bytes must be FE FE FE.
2. Command byte must be 0x51.
3. Status byte must be 0x00 for success.
   - 0x00: stopped without errors
   - non-zero: error, return failure
"""
import time
import random


START_DELIM = b"\xFE\xFE\xFE"
END_DELIM = b"\xFE\xFE\xFE"
START_COMMAND = 50
STOP_COMMAND = 51


def build_start_frame() -> bytes:
    return START_DELIM + bytes([START_COMMAND]) + END_DELIM


def build_stop_frame() -> bytes:
    return START_DELIM + bytes([STOP_COMMAND]) + END_DELIM


def parse_stop_ack(frame: bytes) -> tuple:
    if len(frame) != 8:
        return ("Invalid frame length", False)

    if frame[:3] != START_DELIM or frame[-3:] != END_DELIM:
        return ("Invalid frame delimiters", False)

    if frame[3] != STOP_COMMAND:
        return ("Invalid command byte", False)

    if frame[4] == 0x00:
        return ("Stop ACK received: Success", True)

    return ("Stop ACK received: Failure", False)


def print_frame(frame: bytes, name: str):
    print(f"\n{name}")
    print("Raw Bytes :", frame)
    print("Hex       :", frame.hex().upper())
    print("Length    :", len(frame))

if __name__ == "__main__":
    print("Starting Analyzer...")
    # run_throughput_test()
    start_frame = build_start_frame()
    stop_frame = build_stop_frame()

    print_frame(start_frame, "START FRAME")
    print_frame(stop_frame, "STOP FRAME")