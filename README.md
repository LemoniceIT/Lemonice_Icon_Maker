# Lemonice Icon Maker

A Python desktop application that converts standard image formats (PNG, JPG, JPEG, BMP, TIFF, WEBP) into multi-resolution `.ico` files for Windows applications and web development. Built with CustomTkinter featuring a dark high-contrast interface.

## Screenshots

![Main Interface](docs/gui_1.png)
*Application interface on launch.*

![Conversion Process](docs/gui_2.png)
*Real-time terminal log displaying image processing and file output.*

## Features

- **Format Support**: Accepts source images in PNG, JPG, JPEG, BMP, TIFF, and WEBP formats.
- **Multi-Resolution Packaging**: Generates multi-layer `.ico` files with user-selected dimensions (16x16, 32x32, 48x48, 64x64, 128x128, 256x256).
- **Custom Destination**: Configurable output file naming and directory target.
- **Embedded Logging Console**: Integrated terminal panel tracking application events, path resolution, and conversion status in real time.
- **Offline Processing**: Operates entirely locally without external dependencies or network communication.

## Requirements

- Python 3.11+
- CustomTkinter (>=6.0)
- Pillow (>=10.0)

## Installation

Clone the repository and install the required dependencies:

```bash
git clone https://github.com/LemoniceIT/Lemonice_Icon_Maker.git
cd Lemonice_Icon_Maker
pip install -r requirements.txt
```

## Usage

Start the application using:

```bash
python main.py
```

### Execution Steps

1. Click **Select Image** to choose a source file.
2. Select or deselect target icon resolutions as needed.
3. Click **Save As...** to set the output destination path.
4. Click **Convert** to build the multi-resolution `.ico` file.
5. Monitor completion details via the terminal log panel.

## Building Executables

To build a standalone Windows executable (`.exe`) without requiring a system Python environment:

```bash
pip install pyinstaller
pyinstaller --onefile --windowed main.py
```

The compiled binary will be placed in the `dist/` directory.

## Project Structure

```
Lemonice_Icon_Maker/
├── main.py              # Application entry point
├── requirements.txt     # Python dependency list
├── .gitignore
├── LICENSE              # License file
├── README.md
├── asset/               # Application assets and icon
│   └── ico.ico
├── docs/                # Documentation screenshots
│   ├── gui_1.png
│   └── gui_2.png
└── icon_maker/          # Core module source code
    ├── __init__.py
    ├── config.py
    └── gui.py
```

## License & Credits

Developed by Stefano D'Angelo. See the `LICENSE` file for full license information.

### Dependencies and Licenses

- **Python 3.11+** — [PSF License](https://docs.python.org/3/license.html)
- **CustomTkinter** — [Creative Commons Zero v1.0 Universal](https://github.com/TomSchimansky/CustomTkinter)
- **Pillow (PIL)** — [MIT-CMU License](https://github.com/python-pillow/Pillow)