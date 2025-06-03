# Natatnik

A lightweight text editor with basic formatting support for Windows.

## Features

- Dark mode interface
- Multiple tabs for editing different files
- Bold text with adjustable font size
- File operations (new, open, save, save as)
- Edit operations (cut, copy, paste)

## Requirements

To build the executable, you need:
- Python 3.6 or higher
- cx_Freeze package (`pip install cx_Freeze`)

## Building the Executable

1. Clone this repository
2. Install the required packages: `pip install cx_Freeze`
3. Run the build command: `python setup.py build`
4. The executable will be created in the `build` directory

## Usage

### Running the Application

- Double-click on `Natatnik.exe` in the build directory
- Alternatively, you can run the Python script directly: `python main.py`

### Font Size Adjustment

Use the font size slider in the toolbar to adjust the text size (from 10 to 80 points)

### Working with Files

- Create a new tab: File > New
- Open an existing file: File > Open
- Save the current file: File > Save
- Save the current file with a new name: File > Save As

## License

This project is open source and available under the MIT License.
