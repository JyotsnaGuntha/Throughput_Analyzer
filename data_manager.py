"""
Data management and CSV export for MCU analysis.
"""
import csv
from typing import Dict, List, Tuple
from config import CHUNK_SIZE, CSV_TIME_MULTIPLIER


class DataManager:
    """Manages data collection and export."""

    def __init__(self):
        self.data: Dict[int, List[Tuple[int, float]]] = {}
        self.lock = None  # Will be set to threading.Lock() in main app

    def reset(self):
        """Clear all stored data."""
        self.data.clear()

    def add_chunk(self, chunk_number: int, frame_timings: List[Tuple[int, float]]):
        """
        Add one chunk of frame timing data.
        Structures as: {chunk_number: [(frame_idx, time_per_frame), ...]}
        """
        frame_map = {}
        for frame_idx, delta in frame_timings:
            if 1 <= frame_idx <= CHUNK_SIZE:
                frame_map[frame_idx] = float(delta)

        self.data[chunk_number] = [
            (frame_idx, frame_map.get(frame_idx, 0.0))
            for frame_idx in range(1, CHUNK_SIZE + 1)
        ]

    def get_chunk_count(self) -> int:
        """Return the number of chunks received."""
        return len(self.data)

    def export_csv(self, filepath: str) -> bool:
        """
        Export data to CSV with columns: Frame 1, Frame 2, ..., Frame 500
        Each row is one chunk, values are time_per_frame × 20

        Returns True if successful, False otherwise.
        """
        try:
            if not self.data:
                return False

            with open(filepath, 'w', newline='') as csvfile:
                # Headers: Frame 1, Frame 2, ..., Frame 500
                headers = [f"Frame {i}" for i in range(1, CHUNK_SIZE + 1)]
                writer = csv.DictWriter(csvfile, fieldnames=headers)
                writer.writeheader()

                # Write rows for each chunk
                for chunk_num in sorted(self.data.keys()):
                    row_data = {}
                    frames = self.data[chunk_num]

                    # Create a mapping of frame_index -> time_value
                    frame_times = {frame_idx: time_val for frame_idx, time_val in frames}

                    # Fill row with scaled time values
                    for frame_num in range(1, CHUNK_SIZE + 1):
                        header = f"Frame {frame_num}"
                        time_val = frame_times.get(frame_num, 0.0)
                        scaled_val = time_val * CSV_TIME_MULTIPLIER
                        row_data[header] = f"{scaled_val:.6f}"

                    writer.writerow(row_data)

            return True
        except Exception as e:
            print(f"CSV export error: {e}")
            return False

    def get_summary(self) -> Dict:
        """Get summary statistics of collected data."""
        total_frames = sum(len(frames) for frames in self.data.values())
        return {
            "chunks": len(self.data),
            "total_frames": total_frames,
        }
