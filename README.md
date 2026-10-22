# Lemonice Icon Maker

A Python desktop application that converts images (PNG, JPG, JPEG, BMP, TIFF, WEBP) into multi-resolution `.ico` files for Windows icons. Built with CustomTkinter with a Cyberpunk/Matrix dark theme.

## Features

- **Image Selection**: Choose source images in PNG, JPG, JPEG, BMP, TIFF, and WEBP formats
- **Multi-Resolution Output**: Select which icon sizes to include (16x16, 32x32, 48x48, 64x64, 128x128, 256x256)
- **Customizable Output**: Choose output filename and directory with `.ico` extension by default
- **Conversion Log**: Real-time log terminal panel showing all actions and conversion progress
- **Cyberpunk GUI**: 800x600 dark-themed interface with green accents

## Screenshots

![Interface preview](docs/screenshot.png)

## Requirements

- Python 3.11+
- CustomTkinter (>=6.0)
- Pillow (>=10.0)

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

### Steps

1. Click **"Select Image"** to choose a source image
2. (Optional) Uncheck any icon sizes you don't want
3. Click **"Save As..."** to choose output location (defaults to `.ico`)
4. Click **"Convert"** to generate the multi-resolution ICO file
5. Check the terminal log for conversion progress

## Building from Source

### Standalone Executable (.exe)

A pre-compiled Windows executable is available in the [`dist/`](dist/) directory. No Python installation required.

```bash
python main.py
```

### Creating Your Own .exe

Using PyInstaller:

```bash
pip install pyinstaller
pyinstaller --onefile --windowed main.py
```

## Project Structure

```
icon_maker/
├── main.py              # Application entry point
├── requirements.txt     # Python dependencies
├── .gitignore
├── README.md
├── asset/
│   └── ico.ico
└── icon_maker/
    ├── __init__.py
    ├── config.py
    └── gui.py
```

## Credits

Developed by Stefano D'Angelo

### Libraries and Licenses

- **Python 3.11+** — [PSF License](https://docs.python.org/3/license.html)
- **CustomTkinter** — [Creative Commons Zero v1.0 Universal](https://github.com/TomSchimansky/CustomTkinter)
- **Pillow (PIL)** — [MIT-CMU License](https://github.com/python-pillow/Pillow)
