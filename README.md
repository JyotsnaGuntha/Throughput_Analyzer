# Throughput Analyzer

A Python utility to measure serial firmware transfer throughput using framed packets and ACK-based retries.

## Requirements

- Windows (PowerShell)
- Python 3.8+
- Serial device connected (correct COM port)

## Setup

```powershell
cd D:\Throughput_Analyzer
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Run

1. Open `throughput_tool.py` and set the correct COM port in the `__main__` block (for example, `COM3`).
2. Run:

```powershell
python throughput_tool.py
```

## What It Does

- Builds protocol frames with CRC16
- Sends data chunks over serial
- Waits for ACK (`0x41`) with retry logic
- Prints final throughput summary:
  - Time taken
  - Data moved
  - Effective speed (KB/s)
  - Retry count
  - Link quality estimate

## Dependency

Pinned in `requirements.txt`:

- `pyserial==3.5`
