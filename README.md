# Sukant Sondhi's File Conversion Tool

A simple GUI tool to convert images (PNG, JPG, HEIC) to PDF or other image formats, and to convert PDF pages to images. Built with Python, Tkinter, and Pillow.

## Quick Start

**To use the tool, simply [download the latest `.exe` file from the Releases section](https://github.com/yourusername/File-Converter/releases) and run it—no installation required!**

> **Note:** If you want to view or modify the source code, switch to the `code` branch on this repository.

## Features

- Convert multiple images to a single PDF
- Convert images to JPG, PNG, or HEIC formats
- Convert PDF pages to images (JPG, PNG, HEIC)
- Drag-and-drop image reordering
- Image/PDF preview before conversion

## Requirements

- Python 3.7+
- See `requirements.txt` for dependencies:
  - `pillow`
  - `pillow-heif` (for HEIC support)
  - `pdf2image` (for PDF preview)
  - `pymupdf` (for PDF to image conversion)
  - `tk` (Tkinter GUI)

## Installation (For Developers)

If you want to run from source or modify the code, follow these steps:

1. (Recommended) Create and activate a virtual environment:

   ```sh
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```

## Usage (From Source)

Run the main script:

```sh
python main.py
```

- Use "Upload Images" to select images for conversion.
- Use "Upload PDF" to select a PDF for conversion to images.
- Choose the output format and convert.

## Notes

- For HEIC support, `pillow-heif` must be installed. Some systems may require additional libraries (see [pillow-heif documentation](https://github.com/strukturag/pillow-heif)).
- For PDF preview, `pdf2image` requires `poppler` to be installed on your system.
- For PDF to image conversion, `pymupdf` is used.

## License

MIT License
