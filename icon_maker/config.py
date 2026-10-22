"""
Configuration module for Lemonice Icon Maker.
Centralizes theme colors, dimensions, and constants.
"""

from pathlib import Path

# Application Metadata
APP_NAME: str = "Lemonice Icon Maker"
APP_DISPLAY_TITLE: str = "Lemonice Icon Maker — Image to ICO Converter"

# Read version from VERSION file
APP_VERSION: str = "1.0.0"
_version_path = Path(__file__).resolve().parent.parent / "VERSION"
if _version_path.exists():
    APP_VERSION = _version_path.read_text().strip()

# Application Directories and Paths
ASSETS_DIR: Path = Path(__file__).resolve().parent.parent / "asset"
APP_ICON_PATH: Path = ASSETS_DIR / "ico.ico"

# GUI Dimensions
GUI_WIDTH: int = 800
GUI_HEIGHT: int = 600

# Theme Colors (Cyberpunk/Matrix palette, matching example GUI)
GUI_BG_COLOR: str = "#0A0A0A"
GUI_PANEL_BG: str = "#121212"
GUI_TERMINAL_BG: str = "#000000"
GUI_ACCENT_COLOR: str = "#00FF66"
GUI_ACCENT_HOVER: str = "#00CC52"
GUI_TEXT_COLOR: str = "#E0E0E0"
GUI_MUTED_TEXT: str = "#7A7A7A"
GUI_DANGER_COLOR: str = "#FF3366"
GUI_DANGER_HOVER: str = "#CC2952"
GUI_WARNING_COLOR: str = "#FFB300"
GUI_BORDER_COLOR: str = "#1F3D2B"

# Polling Interval for log queue
GUI_QUEUE_POLL_INTERVAL_MS: int = 100

# Supported icon sizes
ICON_SIZES: list[tuple[int, int]] = [
    (16, 16),
    (32, 32),
    (48, 48),
    (64, 64),
    (128, 128),
    (256, 256),
]

# Default selected sizes (all)
DEFAULT_SELECTED_SIZES: list[tuple[int, int]] = ICON_SIZES.copy()
