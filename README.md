# MCU Data Analyzer

A professional, **industrial-grade** desktop application for analyzing MCU data over serial communication with a modern, visually refined UI.

## Features

- **Protocol Control**: Automatic START/STOP frame transmission and ACK validation
- **Real-time Data Capture**: Continuous 500-byte chunk reception in background thread
- **Data Structuring**: Organized frame-by-frame timing analysis
- **CSV Export**: Professional export with time scaling per frame
- **Modern UI**: Dark theme with accent colors, card-style panels, visual indicators
- **Professional Design**: Industrial-grade appearance with status feedback
- **Threading-Safe**: Non-blocking UI with background data acquisition

## Architecture

```
project/
├── gui_app.py              # Main Tkinter application (UI logic)
├── serial_handler.py       # Serial communication & threading
├── data_manager.py         # Data storage & CSV export
├── protocol.py             # Frame building/parsing
├── config.py               # Colors, fonts, constants
├── throughput_tool.py      # Legacy protocol test utilities
└── requirements.txt        # Dependencies
```

## Requirements

- Windows (Python 3.8+)
- pyserial 3.5
- COM port connected to MCU
- Tkinter (included with Python on Windows)

## Setup

### Create Virtual Environment

```powershell
cd D:\Throughput_Analyzer
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Running the Application

```powershell
python gui_app.py
```

### First Time

1. Select COM port from dropdown (auto-detected)
2. Set baud rate (default 57600)
3. Click **Connect**
4. When ready, click **Start Analysis**
5. MCU will send continuous 500-byte chunks
6. Monitor `Chunks Received` metric
7. Click **Stop Analysis** when done
8. Click **Export CSV** to save results

## Protocol Frames

| Frame       | Hex Bytes       | Purpose                          |
|-------------|-----------------|----------------------------------|
| START       | FE FE FE 50 ... | Signal MCU to begin transmission |
| STOP        | FE FE FE 51 ... | Signal MCU to stop transmission  |
| STOP ACK    | FE FE FE 51 00  | Confirm stop (success status)    |

## Data Structure

### In-Memory Format
```python
{
    chunk_number: [
        (frame_index, time_taken_for_frame),
        (frame_index, time_taken_for_frame),
        ...  # 500 frames per chunk
    ]
}
```

### CSV Export Format
| Frame 1 | Frame 2 | Frame 3 | ... | Frame 500 |
|---------|---------|---------|-----|-----------|
| 0.012   | 0.024   | 0.018   | ... | 0.015     |
| 0.011   | 0.023   | 0.017   | ... | 0.014     |

**Values**: time_per_frame × 20 (scaling factor)

## UI Components

### Left Panel (Connection)
- **COM Port Selector**: Dropdown with auto-detection
- **Baud Rate**: Configurable (9600, 19200, 57600, 115200)
- **Status Indicator**: Color-coded connection state
- **Connect Button**: Establish serial connection

### Right Panel (Analysis)
- **Start/Stop/Export Buttons**: Control data acquisition
- **Metrics Display**: Real-time chunk counter
- **Status Log**: Scrollable message history

### Visual Design
- **Dark Theme**: Professional, easy on the eyes
- **Color Coding**:
  - Blue: Connected, active operations
  - Green: Operation success
  - Orange: Warnings
  - Red: Errors
  - Gray: Disconnected

## Technical Highlights

- **Threading**: Background serial I/O prevents UI freezing
- **Queue-Based Updates**: Thread-safe UI queue for data/status changes
- **Error Handling**: Graceful fallback for connection/data errors
- **Modular Architecture**: Separate concerns (UI, protocol, data, serial)
- **Type Hints**: Clear function signatures for maintainability

## Troubleshooting

### COM Port Not Showing
- Check Device Manager for connected devices
- Ensure drivers are installed for your serial adapter
- Try unplugging/replugging the device

### "Not connected" Error
- Click **Connect** first
- Verify COM port and baud rate match device settings
- Check serial cable is properly seated

### Data Not Received
- Verify MCU is sending 500-byte chunks
- Check baud rate matches device (default 57600)
- Inspect status log for error messages

## Dependencies

- **pyserial**: Serial port communication
- **tkinter**: GUI framework (bundled with Python)

## Example Workflow

1. Flash MCU with firmware that responds to START/STOP frames
2. Connect USB serial adapter to PC
3. Launch application: `python gui_app.py`
4. Select COM port and click Connect
5. Click Start Analysis
6. Let MCU transmit for desired duration
7. Click Stop Analysis (MCU responds with ACK)
8. Export data as CSV for analysis in Excel/Python/etc.

## Protocol Compliance

✅ START frame: FE FE FE 50 FE FE FE  
✅ STOP frame: FE FE FE 51 FE FE FE  
✅ ACK validation: Command=0x51, Status=0x00 for success  
✅ Data chunks: 500 bytes per transmission  
✅ Timing: Per-frame measurement with scaling  

---

**Status**: Production-ready prototype  
**Last Updated**: April 2026  
**License**: MIT
