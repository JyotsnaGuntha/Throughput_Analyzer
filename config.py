"""
Configuration and theming for the MCU Data Analyzer GUI.
"""

THEMES = {
    "dark": {
        "bg_app": "#0D1117",
        "bg_header": "#161B22",
        "bg_panel": "#141A23",
        "bg_card": "#1E2532",
        "bg_log": "#0B0E14",
        "text_primary": "#F0F6FC",
        "text_secondary": "#8B949E",
        "border": "#30363D",
        "accent_primary": "#2F81F7",
        "accent_primary_hover": "#58A6FF",
        "accent_secondary": "#2EA043",
        "accent_danger": "#F85149",
        "accent_warning": "#E3B341",
        "connected": "#2EA043",
        "running": "#2F81F7",
        "stopped": "#E3B341",
        "error": "#F85149",
        "disconnected": "#8B949E",
        "btn_disabled_bg": "#1C2128",
        "btn_disabled_fg": "#484F58",
    },
    "light": {
        "bg_app": "#F6F8FA",
        "bg_header": "#FFFFFF",
        "bg_panel": "#F3F4F6",
        "bg_card": "#FFFFFF",
        "bg_log": "#F8F9FA",
        "text_primary": "#1F2328",
        "text_secondary": "#656D76",
        "border": "#D0D7DE",
        "accent_primary": "#0969DA",
        "accent_primary_hover": "#0550AE",
        "accent_secondary": "#1A7F37",
        "accent_danger": "#D1242F",
        "accent_warning": "#BF8700",
        "connected": "#1A7F37",
        "running": "#0969DA",
        "stopped": "#BF8700",
        "error": "#D1242F",
        "disconnected": "#656D76",
        "btn_disabled_bg": "#F3F4F6",
        "btn_disabled_fg": "#8C959F",
    },
}

# Font Configuration
FONTS = {
    "title": ("Segoe UI Semibold", 18),
    "subtitle": ("Segoe UI", 11),
    "heading": ("Segoe UI Semibold", 13),
    "body": ("Segoe UI", 10),
    "small": ("Segoe UI", 9),
    "mono": ("Consolas", 9),
}

# Geometry
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 650
PADDING = 12
SPACING = 8

# Default Serial Settings
DEFAULT_BAUDRATE = 57600
DEFAULT_TIMEOUT = 1

# Data Constants
CHUNK_SIZE = 500  # Bytes per chunk
CHUNK_INTERVAL = 1  # Seconds between chunks

# CSV Export
CSV_TIME_MULTIPLIER = 20