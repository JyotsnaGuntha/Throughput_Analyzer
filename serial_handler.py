"""
Serial communication handler with threading support.
"""
import threading
import time
from typing import Callable, List, Optional, Tuple
import serial
import serial.tools.list_ports
from config import DEFAULT_BAUDRATE, DEFAULT_TIMEOUT, CHUNK_SIZE
from protocol import build_start_frame, build_stop_frame, parse_stop_ack


class SerialHandler:
    """Manages serial port communication in a background thread."""

    def __init__(self, on_data_received: Callable, on_status_changed: Callable):
        self.port = None
        self.baudrate = DEFAULT_BAUDRATE
        self.ser: Optional[serial.Serial] = None
        self.running = False
        self.thread: Optional[threading.Thread] = None

        # Callbacks
        self.on_data_received = on_data_received
        self.on_status_changed = on_status_changed

    @staticmethod
    def list_ports() -> list:
        """Return list of available COM ports."""
        ports = []
        for port_info in serial.tools.list_ports.comports():
            ports.append(port_info.device)
        return sorted(ports)

    def connect(self, port: str, baudrate: int = DEFAULT_BAUDRATE) -> bool:
        """
        Open serial connection.
        Returns True if successful, False otherwise.
        """
        try:
            self.port = port
            self.baudrate = baudrate
            self.ser = serial.Serial(port, baudrate, timeout=DEFAULT_TIMEOUT)
            self.on_status_changed("connected", f"Connected to {port}")
            return True
        except Exception as e:
            self.on_status_changed("error", f"Connection failed: {str(e)}")
            return False

    def disconnect(self):
        """Close serial connection."""
        if self.ser and self.ser.is_open:
            self.ser.close()
        self.on_status_changed("disconnected", "Disconnected")

    def start_analysis(self) -> bool:
        """Begin data acquisition in background thread."""
        if not self.ser or not self.ser.is_open:
            self.on_status_changed("error", "Not connected to serial port")
            return False

        try:
            # Send START frame
            start_frame = build_start_frame()
            self.ser.write(start_frame)
            self.ser.flush()
            self.on_status_changed("running", "Analysis started, receiving data...")

            # Start background thread
            self.running = True
            self.thread = threading.Thread(target=self._data_acquisition_loop, daemon=True)
            self.thread.start()
            return True
        except Exception as e:
            self.on_status_changed("error", f"Start failed: {str(e)}")
            return False

    def stop_analysis(self) -> bool:
        """Stop data acquisition and validate ACK."""
        if not self.running:
            return False

        try:
            # Send STOP frame
            stop_frame = build_stop_frame()
            self.ser.write(stop_frame)
            self.ser.flush()

            # Wait for ACK frame with a robust sliding window read.
            ack_data = self._read_stop_ack(timeout_seconds=2.0)
            msg, success = parse_stop_ack(ack_data)

            self.running = False
            if self.thread:
                self.thread.join(timeout=2)

            if success:
                self.on_status_changed("stopped", msg)
                return True
            else:
                self.on_status_changed("error", msg)
                return False

        except Exception as e:
            self.running = False
            self.on_status_changed("error", f"Stop failed: {str(e)}")
            return False

    def _read_stop_ack(self, timeout_seconds: float = 2.0) -> bytes:
        if not self.ser or not self.ser.is_open:
            return b""

        deadline = time.perf_counter() + timeout_seconds
        window = bytearray()

        while time.perf_counter() < deadline:
            byte = self.ser.read(1)
            if not byte:
                continue

            window += byte
            if len(window) > 8:
                window = window[-8:]

            if len(window) == 8:
                _, ok = parse_stop_ack(bytes(window))
                if ok:
                    return bytes(window)

        return bytes(window)

    def _data_acquisition_loop(self):
        """Background thread loop for receiving data chunks."""
        chunk_number = 1
        while self.running and self.ser and self.ser.is_open:
            try:
                chunk_bytes, frame_timings = self._read_full_chunk_with_timing()
                if len(chunk_bytes) == CHUNK_SIZE:
                    self.on_data_received(chunk_number, chunk_bytes, frame_timings)
                    chunk_number += 1
                elif len(chunk_bytes) > 0:
                    self.on_status_changed(
                        "error",
                        f"Partial chunk received ({len(chunk_bytes)}/{CHUNK_SIZE}); discarded"
                    )
            except Exception as e:
                self.running = False
                self.on_status_changed("error", f"Data read error: {str(e)}")
                break

    def _read_full_chunk_with_timing(self) -> Tuple[bytes, List[Tuple[int, float]]]:
        if not self.ser or not self.ser.is_open:
            return b"", []

        chunk_data = bytearray()
        frame_timings: List[Tuple[int, float]] = []
        previous_ts = None

        while self.running and len(chunk_data) < CHUNK_SIZE:
            one = self.ser.read(1)
            if not one:
                break

            now = time.perf_counter()
            chunk_data.append(one[0])

            if previous_ts is None:
                delta = 0.0
            else:
                delta = now - previous_ts
            previous_ts = now

            frame_timings.append((len(chunk_data), delta))

        return bytes(chunk_data), frame_timings